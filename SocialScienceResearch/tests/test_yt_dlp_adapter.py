"""Tests for the yt-dlp adapter using a fake YoutubeDL (no live network)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from SocialScienceResearch.acquisition.errors import (
    InvalidURLError,
    NetworkError,
    RateLimitError,
    RecommendationUnsupportedError,
    VideoUnavailableError,
    classify_exception,
)
from SocialScienceResearch.acquisition.yt_dlp_adapter import YtDlpAcquisitionProvider
from SocialScienceResearch.config.settings import CollectionSettings, ScraperSettings

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    with open(FIXTURES / name, encoding="utf-8") as fh:
        return json.load(fh)


class _FakeYoutubeDL:
    """Minimal stand-in for yt_dlp.YoutubeDL."""

    instances: list["_FakeYoutubeDL"] = []

    def __init__(self, opts: dict) -> None:
        self.opts = opts
        self.behavior = _FakeYoutubeDL._behavior
        self.calls: list[str] = []
        _FakeYoutubeDL.instances.append(self)

    def __enter__(self) -> "_FakeYoutubeDL":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def extract_info(self, url: str, download: bool = False) -> dict:
        self.calls.append(url)
        result = self.behavior.get(url)
        if callable(result):
            result = result(url)
        if isinstance(result, Exception):
            raise result
        if result is None:
            raise InvalidURLError(f"No behavior configured for {url}")
        return result

    def sanitize_info(self, info: dict) -> dict:
        return info


@pytest.fixture
def patch_ytdlp(monkeypatch) -> None:
    monkeypatch.setattr(
        "SocialScienceResearch.acquisition.yt_dlp_adapter.YoutubeDL", _FakeYoutubeDL
    )


def _provider() -> YtDlpAcquisitionProvider:
    return YtDlpAcquisitionProvider(
        settings=ScraperSettings(retries=3, retry_backoff=0.01),
        collection=CollectionSettings(collect_comments=True, max_comments_per_video=500),
    )


def test_extract_channel_returns_channel_and_videos(patch_ytdlp) -> None:
    raw = _load("channel_raw.json")
    _FakeYoutubeDL._behavior = {"https://youtube.com/@example": raw}
    provider = _provider()
    result = provider.extract_channel("https://youtube.com/@example")
    assert result.channel["channel_id"] == "UCexample00000000000000000"
    assert len(result.videos) == 2
    assert result.videos[0]["id"] == "v1example0000000000000000001"


def test_extract_channel_rejects_non_playlist(patch_ytdlp) -> None:
    _FakeYoutubeDL._behavior = {"https://youtube.com/watch?v=xyz": {"id": "xyz"}}
    provider = _provider()
    with pytest.raises(InvalidURLError):
        provider.extract_channel("https://youtube.com/watch?v=xyz")


def test_extract_video_requests_comments(patch_ytdlp) -> None:
    raw = _load("video_raw.json")
    _FakeYoutubeDL._behavior = {"https://youtube.com/watch?v=abc": raw}
    provider = _provider()
    info = provider.extract_video("https://youtube.com/watch?v=abc")
    assert info["id"] == "v1example0000000000000000001"
    fake = _FakeYoutubeDL.instances[-1]
    assert fake.opts["getcomments"] is True
    assert fake.opts["max_comments"] == (None, None, 500)


def test_extract_video_rejects_playlist(patch_ytdlp) -> None:
    raw = _load("channel_raw.json")
    _FakeYoutubeDL._behavior = {"https://youtube.com/@x": raw}
    provider = _provider()
    with pytest.raises(InvalidURLError):
        provider.extract_video("https://youtube.com/@x")


def test_extract_recommendations_unsupported_by_default(patch_ytdlp) -> None:
    raw = _load("video_raw.json")
    _FakeYoutubeDL._behavior = {"https://youtube.com/watch?v=abc": raw}
    provider = _provider()
    with pytest.raises(RecommendationUnsupportedError):
        provider.extract_recommendations("https://youtube.com/watch?v=abc")


def test_extract_recommendations_uses_provided_data(patch_ytdlp) -> None:
    raw = _load("video_raw.json")
    raw["recommended_videos"] = [{"id": "r1"}, {"id": "r2"}]
    _FakeYoutubeDL._behavior = {"https://youtube.com/watch?v=abc": raw}
    provider = _provider()
    recs = provider.extract_recommendations("https://youtube.com/watch?v=abc")
    assert [r["id"] for r in recs] == ["r1", "r2"]


# ----------------------------------------------------------------------
# Retry behaviour
# ----------------------------------------------------------------------
def test_transient_network_error_is_retried_then_succeeds(patch_ytdlp) -> None:
    from yt_dlp.utils import DownloadError

    calls = {"n": 0}
    raw = _load("video_raw.json")

    def flaky(url: str):
        calls["n"] += 1
        if calls["n"] < 3:
            raise DownloadError("ERROR: timed out while fetching")
        return raw

    _FakeYoutubeDL._behavior = {"https://youtube.com/watch?v=abc": flaky}
    provider = _provider()
    info = provider.extract_video("https://youtube.com/watch?v=abc")
    assert info["id"] == "v1example0000000000000000001"
    assert calls["n"] == 3


def test_permanent_error_not_retried(patch_ytdlp) -> None:
    from yt_dlp.utils import DownloadError

    calls = {"n": 0}

    def failing(url: str):
        calls["n"] += 1
        raise DownloadError("ERROR: Video unavailable, this video is unavailable")

    _FakeYoutubeDL._behavior = {"https://youtube.com/watch?v=abc": failing}
    provider = _provider()
    with pytest.raises(VideoUnavailableError):
        provider.extract_video("https://youtube.com/watch?v=abc")
    assert calls["n"] == 1


def test_rate_limit_error_classified(patch_ytdlp) -> None:
    from yt_dlp.utils import DownloadError

    def failing(url: str):
        raise DownloadError("ERROR: HTTP Error 429: Too Many Requests")

    _FakeYoutubeDL._behavior = {"https://youtube.com/watch?v=abc": failing}
    provider = _provider()
    with pytest.raises(RateLimitError):
        provider.extract_video("https://youtube.com/watch?v=abc")


def test_network_error_retryable_flag() -> None:
    assert NetworkError("x").retryable is True
    assert RateLimitError("x").retryable is True
    assert VideoUnavailableError("x").retryable is False


def test_classify_exception_mapping() -> None:
    from yt_dlp.utils import DownloadError

    assert classify_exception(DownloadError("ERROR: HTTP Error 429")) == "rate_limit"
    assert classify_exception(DownloadError("ERROR: Video unavailable")) == "unavailable"
    assert classify_exception(DownloadError("ERROR: Unsupported URL")) == "invalid_url"
    assert classify_exception(DownloadError("ERROR: timed out")) == "network"
    assert classify_exception(DownloadError("ERROR: Some weird thing")) == "library"
    assert classify_exception(ValueError("boom")) == "library"


# ----------------------------------------------------------------------
# Transcript extraction
# ----------------------------------------------------------------------
_SAMPLE_VTT = """WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:03.000
Hello world.

00:00:03.500 --> 00:00:06.000
This is a <i>caption</i> test &amp; more.
"""


def test_extract_transcript_available(patch_ytdlp, monkeypatch) -> None:
    raw = _load("video_raw.json")
    raw["subtitles"] = {
        "en": [{"url": "https://example.com/captions.vtt", "ext": "vtt"}]
    }
    _FakeYoutubeDL._behavior = {"https://youtube.com/watch?v=abc": raw}
    provider = _provider()
    monkeypatch.setattr(provider, "_fetch_caption", lambda url: _SAMPLE_VTT)

    extract = provider.extract_transcript("https://youtube.com/watch?v=abc", lang="en")

    from SocialScienceResearch.domain.enums import TranscriptStatus

    assert extract.status == TranscriptStatus.AVAILABLE
    assert extract.lang == "en"
    assert extract.content == "Hello world.\nThis is a caption test & more."


def test_extract_transcript_prefers_manual_over_auto(patch_ytdlp, monkeypatch) -> None:
    raw = _load("video_raw.json")
    raw["subtitles"] = {
        "en": [{"url": "https://example.com/manual.vtt", "ext": "vtt"}]
    }
    raw["automatic_captions"] = {
        "en": [{"url": "https://example.com/auto.vtt", "ext": "vtt"}]
    }
    _FakeYoutubeDL._behavior = {"https://youtube.com/watch?v=abc": raw}
    provider = _provider()
    fetched = []
    monkeypatch.setattr(
        provider, "_fetch_caption", lambda url: fetched.append(url) or _SAMPLE_VTT
    )

    extract = provider.extract_transcript("https://youtube.com/watch?v=abc", lang="en")

    from SocialScienceResearch.domain.enums import TranscriptStatus

    assert extract.status == TranscriptStatus.AVAILABLE
    assert fetched == ["https://example.com/manual.vtt"]


def test_extract_transcript_missing_when_no_tracks(patch_ytdlp) -> None:
    raw = _load("video_raw.json")  # no subtitles / automatic_captions keys
    _FakeYoutubeDL._behavior = {"https://youtube.com/watch?v=abc": raw}
    provider = _provider()

    extract = provider.extract_transcript("https://youtube.com/watch?v=abc", lang="en")

    from SocialScienceResearch.domain.enums import TranscriptStatus

    assert extract.status == TranscriptStatus.MISSING
    assert extract.content is None


def test_extract_transcript_missing_when_track_has_no_text(patch_ytdlp, monkeypatch) -> None:
    raw = _load("video_raw.json")
    raw["automatic_captions"] = {
        "en": [{"url": "https://example.com/empty.vtt", "ext": "vtt"}]
    }
    _FakeYoutubeDL._behavior = {"https://youtube.com/watch?v=abc": raw}
    provider = _provider()
    monkeypatch.setattr(provider, "_fetch_caption", lambda url: "WEBVTT\n\n\n")

    extract = provider.extract_transcript("https://youtube.com/watch?v=abc", lang="en")

    from SocialScienceResearch.domain.enums import TranscriptStatus

    assert extract.status == TranscriptStatus.MISSING


def test_parse_vtt_to_text_strips_timing_and_tags() -> None:
    from SocialScienceResearch.acquisition.yt_dlp_adapter import _parse_vtt_to_text

    assert _parse_vtt_to_text(_SAMPLE_VTT) == (
        "Hello world.\nThis is a caption test & more."
    )
    assert _parse_vtt_to_text("") == ""
    assert _parse_vtt_to_text("WEBVTT\n\n00:00:01,000 --> 00:00:02,000\nnothing") == (
        "nothing"
    )
