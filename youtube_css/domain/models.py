"""Domain models for the YouTube Computational Social Science module.

All models are designed to support:
- Data quality and reproducibility
- Provenance tracking
- Historical observations
- Deduplication
- Incremental collection
- Research transparency
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .enums import CollectionRunStatus, EntityType


@dataclass
class CollectionRun:
    """Tracks a single data collection operation.

    Every collection run gets a unique ID and timestamp.
    This enables reproducibility and provenance tracking.
    """

    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: CollectionRunStatus = CollectionRunStatus.PENDING
    entity_type: Optional[EntityType] = None
    target_id: Optional[str] = None
    target_url: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    items_collected: int = 0
    items_expected: Optional[int] = None
    source_info: Dict[str, Any] = field(default_factory=dict)

    def mark_completed(self) -> None:
        self.status = CollectionRunStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        self.status = CollectionRunStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.errors.append(error)

    def mark_partial(self, error: Optional[str] = None) -> None:
        self.status = CollectionRunStatus.PARTIAL
        self.completed_at = datetime.utcnow()
        if error:
            self.errors.append(error)


@dataclass
class Channel:
    """YouTube channel entity.

    Preserves channel metadata and supports repeated collection.
    """

    channel_id: str
    channel_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    joined_date: Optional[datetime] = None
    country: Optional[str] = None
    language: Optional[str] = None
    thumbnail_url: Optional[str] = None
    banner_url: Optional[str] = None
    verified: Optional[bool] = None
    tags: List[str] = field(default_factory=list)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    first_seen_at: datetime = field(default_factory=datetime.utcnow)
    last_updated_at: datetime = field(default_factory=datetime.utcnow)
    collection_runs: List[str] = field(default_factory=list)

    @property
    def canonical_id(self) -> str:
        return self.channel_id


@dataclass
class Video:
    """YouTube video entity.

    Stores video metadata separately from observations to support
    longitudinal research without overwriting historical data.
    """

    video_id: str
    video_url: str
    channel_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    upload_date: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    language: Optional[str] = None
    thumbnail_url: Optional[str] = None
    live_status: Optional[str] = None
    availability: Optional[str] = None
    age_limit: Optional[int] = None
    chapters: List[Dict[str, Any]] = field(default_factory=list)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    first_seen_at: datetime = field(default_factory=datetime.utcnow)
    last_updated_at: datetime = field(default_factory=datetime.utcnow)
    collection_runs: List[str] = field(default_factory=list)

    @property
    def canonical_id(self) -> str:
        return self.video_id


@dataclass
class VideoObservation:
    """A point-in-time observation of video statistics.

    This is the key structure for longitudinal research.
    Each observation captures stats at a specific moment.
    """

    observation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str = ""
    run_id: str = ""
    observed_at: datetime = field(default_factory=datetime.utcnow)
    views: Optional[int] = None
    likes: Optional[int] = None
    comments_count: Optional[int] = None
    # Derived metrics (calculated by our system, not from source)
    like_rate: Optional[float] = None  # likes / views
    comment_rate: Optional[float] = None  # comments / views
    engagement_score: Optional[float] = None  # configurable formula
    raw_source_values: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Comment:
    """YouTube comment entity.

    Preserves comment text, metadata, and relationships.
    """

    comment_id: str
    video_id: str
    text: Optional[str] = None
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    like_count: Optional[int] = None
    reply_count: Optional[int] = None
    is_reply: bool = False
    parent_comment_id: Optional[str] = None
    posted_at: Optional[datetime] = None
    # Research field: comment age relative to video upload
    comment_age_seconds: Optional[int] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    first_seen_at: datetime = field(default_factory=datetime.utcnow)
    collection_run: Optional[str] = None

    @property
    def canonical_id(self) -> str:
        return self.comment_id


@dataclass
class CommentThread:
    """A comment and its replies as a conversation unit."""

    root_comment: Comment
    replies: List[Comment] = field(default_factory=list)
    reply_count: int = 0
    total_likes: int = 0
    max_reply_depth: int = 0


@dataclass
class RecommendationObservation:
    """Observed recommendation relationship between videos.

    This represents what was observable at collection time,
    not a permanent property of YouTube's algorithm.
    """

    observation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_video_id: str = ""
    recommended_video_id: str = ""
    run_id: str = ""
    observed_at: datetime = field(default_factory=datetime.utcnow)
    # If the library provides ranking/ordering info
    rank: Optional[int] = None
    # Collection context
    collection_method: Optional[str] = None
    # Any additional metadata about the recommendation
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchDataset:
    """Container for a complete research dataset.

    Returned by analysis workflows to package all relevant data.
    """

    dataset_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    run_id: str = ""
    channels: List[Channel] = field(default_factory=list)
    videos: List[Video] = field(default_factory=list)
    observations: List[VideoObservation] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    recommendations: List[RecommendationObservation] = field(default_factory=list)
    analytics_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
