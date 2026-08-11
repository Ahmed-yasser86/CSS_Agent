"""
Persistence layer for YouTube Computational Social Science research.

Provides repository interfaces and implementations for storing research data
while maintaining research provenance and enabling future storage backends.
"""

from .repository import (
    ChannelRepository,
    VideoRepository,
    CommentRepository,
    RecommendationRepository
)
from .excel_repository import (
    ExcelChannelRepository,
    ExcelVideoRepository,
    ExcelCommentRepository,
    ExcelRecommendationRepository
)

__all__ = [
    "ChannelRepository", "VideoRepository", "CommentRepository", "RecommendationRepository",
    "ExcelChannelRepository", "ExcelVideoRepository", "ExcelCommentRepository",
    "ExcelRecommendationRepository"
]