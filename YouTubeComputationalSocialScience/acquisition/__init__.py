"""
Acquisition layer for YouTube Computational Social Science research.

Provides data extraction and normalization from YouTube using yt-dlp,
while preserving research provenance and data quality.
"""

from .youtube_scraper import YouTubeScraper
from .data_extractor import (
    extract_channel_data,
    extract_video_data,
    extract_comment_data,
    extract_recommendation_data,
    normalize_channel,
    normalize_video,
    normalize_comment,
    normalize_recommendation
)

__all__ = [
    "YouTubeScraper",
    "extract_channel_data", "extract_video_data", "extract_comment_data",
    "extract_recommendation_data", "normalize_channel", "normalize_video",
    "normalize_comment", "normalize_recommendation"
]