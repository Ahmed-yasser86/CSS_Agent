"""Domain enumerations for the YouTube CSS module."""

from enum import Enum, auto


class CollectionRunStatus(Enum):
    """Status of a data collection run."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class SamplingMethod(Enum):
    """Video sampling methods for research."""

    RANDOM = "random"
    STRATIFIED_TEMPORAL = "stratified_temporal"
    TOP_VIEWS = "top_views"
    BOTTOM_VIEWS = "bottom_views"
    TOP_ENGAGEMENT = "top_engagement"
    BOTTOM_ENGAGEMENT = "bottom_engagement"
    TOP_COMMENT_RATE = "top_comment_rate"
    TOP_LIKE_RATE = "top_like_rate"
    TOP_COMMENTS = "top_comments"
    LONGEST = "longest"
    SHORTEST = "shortest"


class AnalysisType(Enum):
    """Types of analytics that can be performed."""

    ENGAGEMENT_DISTRIBUTION = "engagement_distribution"
    COMMENT_VELOCITY = "comment_velocity"
    REPLY_RATE = "reply_rate"
    THREAD_DEPTH = "thread_depth"
    ENGAGEMENT_CONCENTRATION = "engagement_concentration"
    PUBLISHING_PATTERN = "publishing_pattern"
    UPLOAD_TIME_ANALYSIS = "upload_time_analysis"
    CONTENT_EVOLUTION = "content_evolution"
    AUDIENCE_EVOLUTION = "audience_evolution"
    RECOMMENDATION_NETWORK = "recommendation_network"


class TimeGranularity(Enum):
    """Time granularity for temporal analysis."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class CommentSort(Enum):
    """Comment sorting options."""

    TOP = "top"
    NEWEST = "newest"
    OLDEST = "oldest"


class EntityType(Enum):
    """Types of entities in the system."""

    CHANNEL = "channel"
    VIDEO = "video"
    COMMENT = "comment"
