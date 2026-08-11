"""yt-dlp adapter for YouTube data acquisition.

Wraps yt-dlp to provide a clean interface for the CSS module.
Handles metadata extraction, comments, and recommendations.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class YtDlpConfig:
    """Configuration for yt-dlp extraction."""

    extract_comments: bool = True
    comment_limit: Optional[int] = None
    extract_recommendations: bool = True
    recommendation_limit: Optional[int] = None
    sleep_interval: float = 1.0
    max_retries: int = 3
    proxy: Optional[str] = None
    cookies_file: Optional[str] = None
    extra_opts: Dict[str, Any] = field(default_factory=dict)


class YtDlpAdapter:
    """Adapter wrapping yt-dlp for research data extraction."""

    def __init__(self, config: Optional[YtDlpConfig] = None) -> None:
        self.config = config or YtDlpConfig()
        self._ydl: Optional[Any] = None

    # ------------------------------------------------------------------
    # Lazy yt-dlp initialization
    # ------------------------------------------------------------------
    def _get_ydl(self) -> Any:
        if self._ydl is None:
            try:
                import yt_dlp
            except ImportError as exc:
                raise RuntimeError("yt-dlp is not installed. Install it with: pip install yt-dlp") from exc
            opts = self._build_ytdlp_opts()
            self._ydl = yt_dlp.YoutubeDL(opts)
        return self._ydl

    def _build_ytdlp_opts(self) -> Dict[str, Any]:
        opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
            "writesubtitles": False,
            "writeautomaticsub": False,
            "ignoreerrors": True,
            "retries": self.config.max_retries,
            "sleep_interval": self.config.sleep_interval,
        }
        if self.config.proxy:
            opts["proxy"] = self.config.proxy
        if self.config.cookies_file:
            opts["cookiefile"] = self.config.cookies_file
        opts.update(self.config.extra_opts)
        return opts

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract full video metadata."""
        try:
            ydl = self._get_ydl()
            info = ydl.extract_info(url, download=False)
            if info is None:
                logger.warning("No info returned for %s", url)
                return None
            return info
        except Exception as exc:
            logger.error("Failed to extract video info for %s: %s", url, exc)
            return None

    def extract_channel_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract channel metadata and video list."""
        try:
            ydl = self._get_ydl()
            info = ydl.extract_info(url, download=False)
            if info is None:
                logger.warning("No info returned for channel %s", url)
                return None
            return info
        except Exception as exc:
            logger.error("Failed to extract channel info for %s: %s", url, exc)
            return None

    def extract_comments(self, url: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract comments from a video.

        yt-dlp can fetch comments when writecomments is enabled.
        We simulate by extracting info with comments enabled.
        """
        try:
            import yt_dlp
            opts = self._build_ytdlp_opts()
            opts["writecomments"] = True
            opts["getcomments"] = True
            opts["extract_flat"] = False
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if not info:
                return []
            comments = info.get("comments", [])
            if limit:
                comments = comments[:limit]
            return comments
        except Exception as exc:
            logger.error("Failed to extract comments for %s: %s", url, exc)
            return []

    def extract_recommendations(self, url: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract related/recommended videos.

        yt-dlp exposes related videos in the 'related' or 'entries' fields
        depending on the extractor. We collect whatever is available.
        """
        try:
            info = self.extract_video_info(url)
            if not info:
                return []
            # yt-dlp may expose related videos under various keys
            related: List[Dict[str, Any]] = []
            for key in ("related", "related_videos", "recommendations", "entries"):
                if key in info and isinstance(info[key], list):
                    candidates = info[key]
                    # Filter out the source video itself if present
                    source_id = self._extract_video_id(url)
                    for cand in candidates:
                        if isinstance(cand, dict):
                            cand_id = cand.get("id") or cand.get("video_id")
                            if cand_id and cand_id != source_id:
                                related.append(cand)
            # Deduplicate by ID
            seen: set = set()
            deduped: List[Dict[str, Any]] = []
            for r in related:
                rid = r.get("id") or r.get("video_id")
                if rid and rid not in seen:
                    seen.add(rid)
                    deduped.append(r)
            if limit:
                deduped = deduped[:limit]
            return deduped
        except Exception as exc:
            logger.error("Failed to extract recommendations for %s: %s", url, exc)
            return []

    def extract_channel_videos(self, channel_url: str) -> List[Dict[str, Any]]:
        """Extract all videos from a channel."""
        info = self.extract_channel_info(channel_url)
        if not info:
            return []
        entries = info.get("entries", [])
        if not entries:
            # Some channel URLs return the channel info directly with entries
            return []
        videos: List[Dict[str, Any]] = []
        for entry in entries:
            if isinstance(entry, dict):
                videos.append(entry)
        return videos

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_video_id(url: str) -> Optional[str]:
        patterns = [
            r"(?:v=|/v/|/embed/|/shorts/)([0-9A-Za-z_-]{11})",
            r"([0-9A-Za-z_-]{11})",
        ]
        for pat in patterns:
            m = re.search(pat, url)
            if m:
                return m.group(1)
        return None

    @staticmethod
    def _extract_channel_id(url: str) -> Optional[str]:
        patterns = [
            r"youtube\.com/channel/([0-9A-Za-z_-]+)",
            r"youtube\.com/c/([0-9A-Za-z_-]+)",
            r"youtube\.com/@([0-9A-Za-z_-]+)",
            r"youtube\.com/user/([0-9A-Za-z_-]+)",
        ]
        for pat in patterns:
            m = re.search(pat, url)
            if m:
                return m.group(1)
        return None

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize a YouTube URL to canonical form."""
        vid = YtDlpAdapter._extract_video_id(url)
        if vid:
            return f"https://www.youtube.com/watch?v={vid}"
        return url

    @staticmethod
    def parse_upload_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse yt-dlp upload_date string to datetime."""
        if not date_str:
            return None
        for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
