"""
YouTube data acquisition module.

Provides YouTube scraping via yt-dlp and data extraction/normalization
to domain models for Computational Social Science research.
"""

from .youtube_scraper import YouTubeScraper
from .data_extractor import DataExtractor

__all__ = ['YouTubeScraper', 'DataExtractor']