"""yt-dlp implementation of the acquisition provider.

The only module in the application that knows about yt-dlp. It:

* extracts channel metadata + video entries (flat by default for speed),
* extracts full video metadata, including comments when configured,
* exposes recommendations only when the library actually provides them,
  otherwise raises :class:`RecommendationUnsupportedError` (no fabrication).

Failures are classified through ``errors.classify_exception`` and transient
network/rate-limit failures are retried via the tenacity policy.
"""

from __future__ import annotations

import html
import re
import urllib.error
import urllib.request
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from SocialScienceResearch.config.settings import CollectionSettings, ScraperSettings
from SocialScienceResearch.domain.enums import TranscriptStatus
from SocialScienceResearch.utils.logger import get_logger

from .base import AcquisitionProvider, ChannelExtract, TranscriptExtract
from .errors import (
    InvalidURLError,
    NetworkError,
    RecommendationUnsupportedError,
    TranscriptUnsupportedError,
    build_error,
    classify_exception,
)
from .retry import retry_policy

logger = get_logger(__name__)


class _YtDlpLogger:
    """Silent yt-dlp logger that forwards warnings/errors to our logger."""

    def debug(self, msg: str) -> None:  # noqa: D401
        logger.debug("yt-dlp: %s", msg)

    def info(self, msg: str) -> None:
        logger.debug("yt-dlp: %s", msg)

    def warning(self, msg: str) -> None:
        logger.warning("yt-dlp: %s", msg)

    def error(self, msg: str) -> None:
        logger.error("yt-dlp: %s", msg)


class YtDlpAcquisitionProvider(AcquisitionProvider):
    """yt-dlp-backed :class:`AcquisitionProvider`."""

    def __init__(
        self,
        settings: ScraperSettings | None = None,
        collection: CollectionSettings | None = None,
    ) -> None:
        self._settings = settings or ScraperSettings()
        self._collection = collection or CollectionSettings()
        self._retry = retry_policy(
            retries=self._settings.retries,
            backoff=self._settings.retry_backoff,
        )

    # ------------------------------------------------------------------
    # Public interface (wrapped with the retry policy)
    # ------------------------------------------------------------------
    def extract_channel(self, channel_url: str) -> ChannelExtract:
        return self._retry(self._extract_channel)(channel_url)

    def extract_video(self, video_url: str) -> dict[str, Any]:
        return self._retry(self._extract_video)(video_url)

    def extract_recommendations(self, video_url: str) -> list[dict[str, Any]]:
        return self._retry(self._extract_recommendations)(video_url)

    def extract_transcript(
        self, video_url: str, lang: str | None = None
    ) -> TranscriptExtract:
        return self._retry(self._extract_transcript)(video_url, lang)

    # ------------------------------------------------------------------
    # Internal implementations
    # ------------------------------------------------------------------
    def _extract_channel(self, channel_url: str) -> ChannelExtract:
        opts = self._base_opts()
        flat = self._collection.extract_flat
        if flat:
            opts["extract_flat"] = "in_playlist"
        else:
            # Deep extraction is expensive: bound the fetch to the per-run
            # quota here so we never deep-fetch the whole channel.
            if self._collection.max_videos_per_channel:
                opts["playlistend"] = self._collection.max_videos_per_channel
        info = self._extract(channel_url, opts)
        if info.get("_type") != "playlist":
            raise InvalidURLError(
                f"URL does not resolve to a channel/playlist: {channel_url}"
            )
        entries = info.get("entries") or []
        channel_raw = {k: v for k, v in info.items() if k != "entries"}
        video_entries = [e for e in entries if isinstance(e, dict)]
        video_ids: list[str] = []
        for e in video_entries:
            raw_id = e.get("id") or e.get("video_id")
            if raw_id:
                video_ids.append(str(raw_id))
        return ChannelExtract(
            channel=channel_raw,
            videos=video_entries,
            # Stable ids of the *whole* discovered corpus, before the per-run
            # quota (max_videos_per_channel) is enforced by the service.
            video_ids=video_ids,
        )

    def _extract_video(self, video_url: str) -> dict[str, Any]:
        opts = self._base_opts()
        if self._collection.collect_comments:
            opts["getcomments"] = True
            opts["max_comments"] = (
                None,
                None,
                self._collection.max_comments_per_video,
            )
        info = self._extract(video_url, opts)
        if info.get("_type") == "playlist":
            raise InvalidURLError(
                f"URL resolves to a playlist/channel, not a video: {video_url}"
            )
        return info

    def _extract_recommendations(self, video_url: str) -> list[dict[str, Any]]:
        info = self._extract_video(video_url)
        # yt-dlp does not expose recommendations reliably; we only use data the
        # library actually provides. Absence is explicit, never fabricated.
        entries = info.get("recommended_videos") or info.get("related") or []
        if not entries:
            raise RecommendationUnsupportedError(
                "yt-dlp does not expose recommendation/related-video data for "
                f"{video_url}; observed relationships are unavailable."
            )
        return [e for e in entries if isinstance(e, dict)]

    def _extract_transcript(
        self, video_url: str, lang: str | None = None
    ) -> TranscriptExtract:
        """Best-effort caption transcript extraction for one video.

        Never fabricates content: videos without captions return ``MISSING``;
        captions that exist but cannot be retrieved raise
        :class:`TranscriptUnsupportedError` (classified, auditable).
        """
        lang = lang or self._settings.transcript_lang
        opts = self._base_opts()
        opts["subtitleslangs"] = [lang]
        opts["writesubtitles"] = True
        opts["writeautomaticsub"] = True
        info = self._extract(video_url, opts)

        tracks: dict[str, list[dict[str, Any]]] = info.get("subtitles") or {}
        automatic: dict[str, list[dict[str, Any]]] = info.get("automatic_captions") or {}
        track_url, track_lang = self._pick_track(tracks, automatic, lang)
        if track_url is None:
            return TranscriptExtract(
                status=TranscriptStatus.MISSING,
                lang=lang,
                message="No caption track is available for this video.",
            )

        try:
            raw = self._fetch_caption(track_url)
        except urllib.error.HTTPError as exc:
            raise NetworkError(f"caption download failed: {exc}") from exc
        except urllib.error.URLError as exc:
            raise NetworkError(f"caption download failed: {exc}") from exc

        text = _parse_vtt_to_text(raw)
        if not text.strip():
            return TranscriptExtract(
                status=TranscriptStatus.MISSING,
                lang=track_lang,
                message="Caption track exists but contained no text.",
            )
        return TranscriptExtract(
            content=text, lang=track_lang, status=TranscriptStatus.AVAILABLE
        )

    @staticmethod
    def _pick_track(
        tracks: dict[str, list[dict[str, Any]]],
        automatic: dict[str, list[dict[str, Any]]],
        lang: str,
    ) -> tuple[str | None, str | None]:
        """Choose a caption track URL, preferring the requested language.

        Prefers manually-provided subtitles over auto-captions; falls back to
        the first available language when the requested one is absent.
        """
        for source in (tracks, automatic):
            if source.get(lang):
                track = source[lang][-1]
                return track.get("url"), lang
        for name, entries in tracks.items():
            if entries:
                return entries[-1].get("url"), name
        for name, entries in automatic.items():
            if entries:
                return entries[-1].get("url"), name
        return None, None

    def _fetch_caption(self, url: str) -> str:
        if self._settings.proxy:
            handler = urllib.request.ProxyHandler(
                {"http": self._settings.proxy, "https": self._settings.proxy}
            )
            opener = urllib.request.build_opener(handler)
        else:
            opener = urllib.request.build_opener()
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": self._settings.transcript_lang or "en",
            },
        )
        with opener.open(req, timeout=self._settings.socket_timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")

    # ------------------------------------------------------------------
    # Shared extraction
    # ------------------------------------------------------------------
    def _extract(self, url: str, opts: dict[str, Any]) -> dict[str, Any]:
        with YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except DownloadError as exc:
                raise build_error(classify_exception(exc), str(exc)) from exc
            except Exception as exc:  # noqa: BLE001 - classify anything else
                raise build_error(classify_exception(exc), str(exc)) from exc
            if info is None:
                raise InvalidURLError(f"Could not resolve URL: {url}")
            return ydl.sanitize_info(info)

    def _base_opts(self) -> dict[str, Any]:
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "socket_timeout": self._settings.socket_timeout,
            "logger": _YtDlpLogger(),
            "extractor_retries": 0,  # retries handled by our tenacity policy
        }
        if self._settings.proxy:
            opts["proxy"] = self._settings.proxy
        if self._settings.impersonate:
            opts["impersonate"] = self._settings.impersonate
        return opts


_CUE_LINE = re.compile(r"\d{1,2}:\d{2}(:\d{2})?[.,]\d{3}\s*-->\s*\d{1,2}:\d{2}(:\d{2})?[.,]\d{3}")


def _parse_vtt_to_text(raw: str) -> str:
    """Convert a WebVTT/SRT caption payload into plain transcript text."""
    lines: list[str] = []
    for line in raw.replace("\r\n", "\n").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if lower.startswith("webvtt"):
            continue
        if _CUE_LINE.match(stripped):
            continue
        if re.fullmatch(r"NOTE.*", stripped):
            continue
        if lower.startswith("kind:") or lower.startswith("language:"):
            continue
        cleaned = html.unescape(re.sub(r"<[^>]+>", "", stripped))
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)
