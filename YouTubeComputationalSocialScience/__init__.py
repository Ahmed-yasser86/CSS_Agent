"""
YouTube Computational Social Science Module

This module provides research-oriented YouTube data acquisition and analytics
for computational social science research.
"""

from .domain.models import (
    Channel,
    Video,
    Comment,
    CollectionRun,
    Recommendation,
    Observation,
    ChannelAnalytics,
    VideoAnalytics,
    CommentAnalytics
)
from .domain.analytics import (
    calculate_channel_analytics,
    calculate_video_analytics,
    calculate_comment_analytics,
    calculate_engagement_metrics,
    calculate_temporal_metrics,
    calculate_distribution_metrics
)
from .domain.sampling import (
    sample_videos,
    stratified_sample,
    top_performers_sample,
    bottom_performers_sample
)
from .services.channel_service import ChannelService
from .services.video_service import VideoService
from .services.recommendation_service import RecommendationService
from .persistence.repository import (
    ChannelRepository,
    VideoRepository,
    CommentRepository,
    RecommendationRepository
)
from .persistence.excel_repository import (
    ExcelChannelRepository,
    ExcelVideoRepository,
    ExcelCommentRepository,
    ExcelRecommendationRepository
)

__all__ = [
    # Domain models
    "Channel", "Video", "Comment", "CollectionRun", "Recommendation", "Observation",
    "ChannelAnalytics", "VideoAnalytics", "CommentAnalytics",
    
    # Analytics
    "calculate_channel_analytics", "calculate_video_analytics", "calculate_comment_analytics",
    "calculate_engagement_metrics", "calculate_temporal_metrics", "calculate_distribution_metrics",
    
    # Sampling
    "sample_videos", "stratified_sample", "top_performers_sample", "bottom_performers_sample",
    
    # Services
    "ChannelService", "VideoService", "RecommendationService",
    
    # Repositories
    "ChannelRepository", "VideoRepository", "CommentRepository", "RecommendationRepository",
    "ExcelChannelRepository", "ExcelVideoRepository", "ExcelCommentRepository",
    "ExcelRecommendationRepository"
]