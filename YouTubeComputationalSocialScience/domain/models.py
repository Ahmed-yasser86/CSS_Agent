"""
Domain models for YouTube Computational Social Science research.

These models represent the core entities and their relationships for research purposes,
preserving provenance, historical observations, and research-grade data quality.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class CollectionStatus(str, Enum):
    """Status of a collection operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    NOT_ATTEMPTED = "not_attempted"


class Observation(BaseModel):
    """
    A historical observation of a metric at a specific time.
    
    This preserves the distinction between source observations and derived values,
    enabling longitudinal research.
    """
    observed_at: datetime = Field(..., description="When this observation was made")
    value: float = Field(..., description="The observed value")
    source: str = Field(..., description="Source of this observation (raw/derived)")
    collection_run_id: str = Field(..., description="ID of the collection run")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Comment(BaseModel):
    """
    A YouTube comment with metadata and reply structure.
    
    Preserves the hierarchical structure of comment threads for research into
    discussion patterns and audience interaction.
    """
    comment_id: str = Field(..., description="Stable YouTube comment ID")
    video_id: str = Field(..., description="ID of the video this comment belongs to")
    channel_id: str = Field(..., description="ID of the channel this comment belongs to")
    author_id: Optional[str] = Field(None, description="ID of the comment author if available")
    author_name: Optional[str] = Field(None, description="Name of the comment author")
    text: str = Field(..., description="Comment text content")
    published_at: datetime = Field(..., description="When the comment was published")
    like_count: int = Field(..., description="Number of likes on this comment")
    reply_count: int = Field(0, description="Number of replies to this comment")
    parent_id: Optional[str] = Field(None, description="ID of parent comment if this is a reply")
    is_reply: bool = Field(False, description="Whether this comment is a reply")
    
    # Historical observations
    like_count_observations: List[Observation] = Field(default_factory=list, description="Historical like count observations")
    reply_count_observations: List[Observation] = Field(default_factory=list, description="Historical reply count observations")
    
    # Collection metadata
    collection_status: CollectionStatus = Field(CollectionStatus.SUCCESS, description="Collection status")
    collection_errors: List[str] = Field(default_factory=list, description="Errors encountered during collection")
    collection_run_id: str = Field(..., description="ID of the collection run")


class Video(BaseModel):
    """
    A YouTube video with metadata, statistics, and research observations.
    
    Preserves both raw source data and derived analytical values for research
    reproducibility and longitudinal analysis.
    """
    video_id: str = Field(..., description="Stable YouTube video ID")
    channel_id: str = Field(..., description="ID of the channel this video belongs to")
    title: str = Field(..., description="Video title")
    description: str = Field(..., description="Video description")
    published_at: datetime = Field(..., description="When the video was published")
    duration: int = Field(..., description="Video duration in seconds")
    category: Optional[str] = Field(None, description="Video category")
    tags: List[str] = Field(default_factory=list, description="Video tags")
    language: Optional[str] = Field(None, description="Video language")
    
    # Source statistics (raw observations)
    view_count: int = Field(..., description="Number of views")
    like_count: int = Field(..., description="Number of likes")
    comment_count: int = Field(..., description="Number of comments")
    
    # Video content
    script: str = Field("", description="Video transcript/script if available")
    thumbnail_url: Optional[str] = Field(None, description="Video thumbnail URL")
    chapters: List[Dict[str, Any]] = Field(default_factory=list, description="Video chapters with timestamps")
    
    # Historical observations
    view_count_observations: List[Observation] = Field(default_factory=list, description="Historical view count observations")
    like_count_observations: List[Observation] = Field(default_factory=list, description="Historical like count observations")
    comment_count_observations: List[Observation] = Field(default_factory=list, description="Historical comment count observations")
    
    # Collection metadata
    collection_status: CollectionStatus = Field(CollectionStatus.SUCCESS, description="Collection status")
    collection_errors: List[str] = Field(default_factory=list, description="Errors encountered during collection")
    collection_run_id: str = Field(..., description="ID of the collection run")
    url: str = Field(..., description="Canonical URL of the video")
    
    # Derived metrics (calculated by the system)
    engagement_rate: Optional[float] = Field(None, description="Engagement rate (comments + likes) / views")
    like_rate: Optional[float] = Field(None, description="Like rate (likes / views)")
    comment_rate: Optional[float] = Field(None, description="Comment rate (comments / views)")


class Channel(BaseModel):
    """
    A YouTube channel with metadata, videos, and research observations.
    
    Designed for longitudinal research with historical observations and
    incremental collection capabilities.
    """
    channel_id: str = Field(..., description="Stable YouTube channel ID")
    title: str = Field(..., description="Channel title")
    description: str = Field(..., description="Channel description")
    custom_url: Optional[str] = Field(None, description="Channel custom URL")
    published_at: datetime = Field(..., description="When the channel was created")
    thumbnail_url: Optional[str] = Field(None, description="Channel thumbnail URL")
    country: Optional[str] = Field(None, description="Channel country")
    
    # Source statistics
    subscriber_count: int = Field(..., description="Number of subscribers")
    video_count: int = Field(..., description="Number of videos")
    view_count: int = Field(..., description="Total number of views")
    
    # Derived metrics (calculated by the system)
    upload_frequency: Optional[float] = Field(None, description="Average upload frequency in videos per week")
    growth_rate: Optional[float] = Field(None, description="Subscriber growth rate")
    
    # Historical observations
    subscriber_count_observations: List[Observation] = Field(default_factory=list, description="Historical subscriber count observations")
    video_count_observations: List[Observation] = Field(default_factory=list, description="Historical video count observations")
    view_count_observations: List[Observation] = Field(default_factory=list, description="Historical view count observations")
    
    # Collection metadata
    collection_status: CollectionStatus = Field(CollectionStatus.SUCCESS, description="Collection status")
    collection_errors: List[str] = Field(default_factory=list, description="Errors encountered during collection")
    collection_run_id: str = Field(..., description="ID of the collection run")
    url: str = Field(..., description="Canonical URL of the channel")


class Recommendation(BaseModel):
    """
    An observed recommendation relationship between videos.
    
    Preserves the dynamic nature of YouTube's recommendation system for
    network analysis and longitudinal research.
    """
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique recommendation ID")
    source_video_id: str = Field(..., description="ID of the source video")
    source_video_title: Optional[str] = Field(None, description="Title of the source video")
    source_channel_id: Optional[str] = Field(None, description="Channel ID of the source video")
    source_channel_title: Optional[str] = Field(None, description="Channel title of the source video")
    recommended_video_id: str = Field(..., description="ID of the recommended video")
    recommended_video_title: Optional[str] = Field(None, description="Title of the recommended video")
    recommended_video_url: Optional[str] = Field(None, description="URL of the recommended video")
    recommended_channel_id: Optional[str] = Field(None, description="Channel ID of the recommended video")
    recommended_channel_title: Optional[str] = Field(None, description="Channel title of the recommended video")
    rank: Optional[int] = Field(None, description="Position in recommendation list")
    position: Optional[str] = Field(None, description="Position context (sidebar, end, etc.)")
    collection_run_id: str = Field(..., description="ID of the collection run")
    observed_at: datetime = Field(..., description="When this recommendation was observed")


class CollectionRun(BaseModel):
    """
    Metadata about a collection operation for research reproducibility.
    
    Tracks what was collected, when, from which source, and with what results
    to support research provenance and reproducibility.
    """
    collection_run_id: str = Field(..., description="Unique ID for this collection run")
    started_at: datetime = Field(..., description="When the collection started")
    completed_at: Optional[datetime] = Field(None, description="When the collection completed")
    source_type: str = Field(..., description="Type of source (channel/video/recommendation)")
    source_id: str = Field(..., description="ID of the source entity")
    source_url: str = Field(..., description="URL of the source entity")
    
    # Collection statistics
    videos_discovered: int = Field(0, description="Number of videos discovered")
    videos_collected: int = Field(0, description="Number of videos successfully collected")
    videos_failed: int = Field(0, description="Number of videos that failed to collect")
    
    comments_discovered: int = Field(0, description="Number of comments discovered")
    comments_collected: int = Field(0, description="Number of comments successfully collected")
    comments_failed: int = Field(0, description="Number of comments that failed to collect")
    
    recommendations_discovered: int = Field(0, description="Number of recommendations discovered")
    recommendations_collected: int = Field(0, description="Number of recommendations successfully collected")
    recommendations_failed: int = Field(0, description="Number of recommendations that failed to collect")
    
    status: CollectionStatus = Field(CollectionStatus.SUCCESS, description="Overall collection status")
    errors: List[str] = Field(default_factory=list, description="Errors encountered during collection")
    
    # Configuration
    sampling_strategy: Optional[str] = Field(None, description="Sampling strategy used")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filters applied during collection")


class ChannelAnalytics(BaseModel):
    """Analytics for a YouTube channel."""
    channel_id: str = Field(..., description="Channel ID")
    collection_run_id: str = Field(..., description="Collection run ID")
    
    # Summary statistics
    total_videos: Optional[int] = Field(None, description="Total number of videos")
    total_views: Optional[int] = Field(None, description="Total number of views")
    total_likes: Optional[int] = Field(None, description="Total number of likes")
    total_comments: Optional[int] = Field(None, description="Total number of comments")
    subscriber_count: Optional[int] = Field(None, description="Current subscriber count")
    engagement_rate: Optional[float] = Field(None, description="Overall engagement rate")
    
    # Temporal metrics
    upload_frequency: Optional[float] = Field(None, description="Videos per week")
    upload_consistency: Optional[float] = Field(None, description="Consistency of upload schedule")
    
    # Engagement metrics
    avg_views_per_video: Optional[float] = Field(None, description="Average views per video")
    avg_likes_per_video: Optional[float] = Field(None, description="Average likes per video")
    avg_comments_per_video: Optional[float] = Field(None, description="Average comments per video")
    
    # Distribution metrics
    view_distribution: Dict[str, float] = Field(default_factory=dict, description="Distribution of views across videos")
    like_distribution: Dict[str, float] = Field(default_factory=dict, description="Distribution of likes across videos")
    comment_distribution: Dict[str, float] = Field(default_factory=dict, description="Distribution of comments across videos")
    
    # Growth metrics
    subscriber_growth_rate: Optional[float] = Field(None, description="Subscriber growth rate")
    view_growth_rate: Optional[float] = Field(None, description="View growth rate")
    
    # Top performers
    top_videos_by_views: List[Video] = Field(default_factory=list, description="Top videos by views")
    top_videos_by_likes: List[Video] = Field(default_factory=list, description="Top videos by likes")
    top_videos_by_comments: List[Video] = Field(default_factory=list, description="Top videos by comments")
    
    # Temporal analysis
    views_by_period: Dict[str, float] = Field(default_factory=dict, description="Views by time period")
    uploads_by_period: Dict[str, int] = Field(default_factory=dict, description="Uploads by time period")


class RecommendationNetwork(BaseModel):
    """
    A network of recommendation relationships for analysis.
    
    Represents the recommendation ecosystem around a video or channel,
    enabling network analysis of YouTube's recommendation algorithm.
    """
    network_id: str = Field(..., description="Unique ID for this recommendation network")
    source_video_id: str = Field(..., description="ID of the source video")
    collection_run_id: str = Field(..., description="Collection run ID")
    
    # Network structure
    nodes: List[str] = Field(default_factory=list, description="List of video IDs in the network")
    edges: List[Dict[str, str]] = Field(default_factory=list, description="List of recommendation relationships")
    
    # Network metrics
    network_size: int = Field(0, description="Number of nodes in the network")
    network_density: Optional[float] = Field(None, description="Density of the network")
    average_degree: Optional[float] = Field(None, description="Average degree of nodes")
    
    # Temporal aspects
    observed_at: datetime = Field(..., description="When this network was observed")
    
    # Graph and stats (runtime computed, not persisted)
    graph: Optional[Any] = Field(None, description="NetworkX graph object (runtime only)")
    stats: Optional[Dict[str, Any]] = Field(None, description="Computed network statistics")
    


class VideoAnalytics(BaseModel):
    """Analytics for a YouTube video."""
    video_id: str = Field(..., description="Video ID")
    collection_run_id: str = Field(..., description="Collection run ID")
    
    # Current video stats
    view_count: Optional[int] = Field(None, description="Current view count")
    like_count: Optional[int] = Field(None, description="Current like count")
    comment_count: Optional[int] = Field(None, description="Current comment count")
    
    # Engagement metrics
    engagement_rate: Optional[float] = Field(None, description="Engagement rate (comments + likes) / views")
    like_rate: Optional[float] = Field(None, description="Like rate (likes / views)")
    comment_rate: Optional[float] = Field(None, description="Comment rate (comments / views)")
    
    # Temporal metrics
    comment_velocity: Dict[str, float] = Field(default_factory=dict, description="Comments per time period")
    engagement_decay: Dict[str, float] = Field(default_factory=dict, description="Engagement decay over time")
    
    # Distribution metrics
    comment_like_distribution: Dict[str, float] = Field(default_factory=dict, description="Distribution of comment likes")
    comment_length_distribution: Dict[str, float] = Field(default_factory=dict, description="Distribution of comment lengths")
    
    # Participation metrics
    unique_commenters: Optional[int] = Field(None, description="Number of unique commenters")
    repeat_commenters: Optional[int] = Field(None, description="Number of repeat commenters")
    
    # Thread metrics
    thread_initiation_rate: Optional[float] = Field(None, description="Percentage of comments with replies")
    avg_replies_per_thread: Optional[float] = Field(None, description="Average replies per comment thread")
    max_thread_depth: Optional[int] = Field(None, description="Maximum thread depth")
    
    # Top comments
    top_comments_by_likes: List[Comment] = Field(default_factory=list, description="Top comments by likes")
    top_comments_by_replies: List[Comment] = Field(default_factory=list, description="Top comments by replies")
    
    # Engagement concentration
    top_1_percent_share: Optional[float] = Field(None, description="Share of likes from top 1% comments")
    top_5_percent_share: Optional[float] = Field(None, description="Share of likes from top 5% comments")
    top_10_percent_share: Optional[float] = Field(None, description="Share of likes from top 10% comments")


class CommentAnalytics(BaseModel):
    """Analytics for YouTube comments."""
    video_id: str = Field(..., description="Video ID")
    collection_run_id: str = Field(..., description="Collection run ID")
    
    # Sentiment metrics
    avg_sentiment: Optional[float] = Field(None, description="Average sentiment score (-1 to 1)")
    
    # Temporal metrics
    comment_timing: Dict[str, float] = Field(default_factory=dict, description="Comment timing relative to video publication")
    comment_velocity: Dict[str, float] = Field(default_factory=dict, description="Comments per time period")
    comment_velocity_first_hour: Optional[float] = Field(None, description="Comments in the first hour")
    
    # Engagement metrics
    avg_likes_per_comment: Optional[float] = Field(None, description="Average likes per comment")
    avg_replies_per_comment: Optional[float] = Field(None, description="Average replies per comment")
    
    # Distribution metrics
    like_distribution: Dict[str, float] = Field(default_factory=dict, description="Distribution of comment likes")
    reply_distribution: Dict[str, float] = Field(default_factory=dict, description="Distribution of comment replies")
    length_distribution: Dict[str, float] = Field(default_factory=dict, description="Distribution of comment lengths")
    
    # Participation metrics
    unique_commenters: Optional[int] = Field(None, description="Number of unique commenters")
    comments_per_commenter: Dict[str, float] = Field(default_factory=dict, description="Distribution of comments per commenter")
    
    # Thread metrics
    thread_depth_distribution: Dict[str, float] = Field(default_factory=dict, description="Distribution of thread depths")
    thread_initiation_rate: Optional[float] = Field(None, description="Percentage of comments that start threads")
    
    # Engagement concentration
    gini_coefficient: Optional[float] = Field(None, description="Gini coefficient of comment likes")
    top_1_percent_share: Optional[float] = Field(None, description="Share of likes from top 1% comments")
    top_5_percent_share: Optional[float] = Field(None, description="Share of likes from top 5% comments")