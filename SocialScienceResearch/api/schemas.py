"""Typed HTTP response models for the SocialScienceResearch API.

Every endpoint declares a ``response_model`` built from these schemas. Field
names and shapes mirror the previous hand-built payloads exactly (``extra``
is allowed so nothing is silently stripped), except where a proven defect was
fixed (e.g. ``/top`` now annotates MISSING rows with ``availability``).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from SocialScienceResearch.services.pagination import Paginated

__all__ = [
    "ChannelCountPayload",
    "ChannelOverviewPayload",
    "ChannelPayload",
    "CollectionErrorPayload",
    "CollectionResultPayload",
    "CollectionResultsPayload",
    "CommentPayload",
    "DatasetSummaryPayload",
    "ErrorPayload",
    "JobCancelPayload",
    "JobFailurePayload",
    "JobPayload",
    "JobResultPayload",
    "JobSubmitPayload",
    "NetworkSummaryPayload",
    "OperatorInfoPayload",
    "Paginated",
    "PercentilesPayload",
    "QueryPreviewResponse",
    "QueryPreviewStage",
    "QueryResolveResponse",
    "RawVideoPayload",
    "RecommendationPayload",
    "RunPayload",
    "SamplingResultPayload",
    "ThreadPayload",
    "TopVideoRow",
    "TopVideosPayload",
    "VariableMetaPayload",
    "VelocityPoint",
    "VideoEngagementPayload",
    "VideoNetworkContextPayload",
    "VideoObservationPayload",
    "VideoPayload",
]


class _Base(BaseModel):
    """Extra fields pass through unchanged (frontend-compatible payloads)."""

    model_config = ConfigDict(extra="allow")


class ValuePayload(_Base):
    value: float | int | None = None
    availability: str = "available"


class CollectionErrorPayload(_Base):
    error_id: str
    run_id: str
    entity_type: str
    entity_id: str | None = None
    error_type: str
    message: str
    occurred_at: datetime
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class CollectionResultPayload(_Base):
    run_id: str
    run_type: str
    status: str
    target_url: str
    target_id: str | None = None
    entities_discovered: int = 0
    entities_created: int = 0
    entities_existing: int = 0
    entities_failed: int = 0
    comments_collected: int = 0
    errors: list[CollectionErrorPayload] = Field(default_factory=list)
    skipped: list[dict[str, Any]] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None


class CollectionResultsPayload(_Base):
    target_count: int
    results: list[CollectionResultPayload] = Field(default_factory=list)


class JobSubmitPayload(_Base):
    job_id: str


class JobPayload(_Base):
    job_id: str
    kind: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    progress: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None
    cancel_requested: bool = False


class JobCancelPayload(_Base):
    job_id: str
    cancelled: bool


class JobFailurePayload(_Base):
    error: str


class JobResultPayload(_Base):
    """Union-shaped job result (single result, many results, or failure)."""

    error: str | None = None
    target_count: int | None = None
    results: list[CollectionResultPayload] | None = None
    run_id: str | None = None
    run_type: str | None = None
    status: str | None = None
    target_url: str | None = None
    target_id: str | None = None
    entities_discovered: int | None = None
    entities_created: int | None = None
    entities_existing: int | None = None
    entities_failed: int | None = None
    comments_collected: int | None = None
    errors: list[CollectionErrorPayload] | None = None
    skipped: list[dict[str, Any]] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class RunPayload(_Base):
    run_id: str
    run_type: str
    target_url: str
    target_channel_id: str | None = None
    target_video_id: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    provider: str = "yt-dlp"
    provider_version: str | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)
    entities_discovered: int = 0
    entities_succeeded: int = 0
    entities_failed: int = 0
    notes: list[str] = Field(default_factory=list)


class ChannelPayload(_Base):
    channel_id: str
    url: str
    title: str | None = None
    description: str | None = None
    handle: str | None = None
    is_verified: bool | None = None
    avatar_url: str | None = None
    banner_url: str | None = None
    country: str | None = None
    joined_date: date | None = None
    first_observed_run_id: str
    raw_json: dict[str, Any] = Field(default_factory=dict)


class VideoPayload(_Base):
    video_id: str
    url: str
    channel_id: str | None = None
    title: str | None = None
    description: str | None = None
    duration: int | None = None
    upload_date: date | None = None
    upload_timestamp: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    language: str | None = None
    live_status: str | None = None
    availability: str | None = None
    age_limit: int | None = None
    is_short: bool | None = None
    thumbnail_url: str | None = None
    chapters_json: list[dict[str, Any]] = Field(default_factory=list)
    transcript_path: str | None = None
    transcript_status: str | None = None
    transcript_lang: str | None = None
    first_observed_run_id: str
    raw_json: dict[str, Any] = Field(default_factory=dict)


class VideoObservationPayload(_Base):
    observation_id: str
    collection_run_id: str
    video_id: str
    observed_at: datetime
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    favorite_count: int | None = None
    raw_json: dict[str, Any] = Field(default_factory=dict)


class CommentPayload(_Base):
    comment_id: str
    video_id: str
    author_name: str | None = None
    author_id: str | None = None
    comment_text: str | None = None
    published_at: datetime | None = None
    is_reply: bool = False
    parent_comment_id: str | None = None
    root_comment_id: str | None = None
    is_author: bool | None = None
    first_observed_run_id: str
    raw_json: dict[str, Any] = Field(default_factory=dict)


class RecommendationPayload(_Base):
    observation_id: str
    collection_run_id: str
    source_video_id: str
    recommended_video_id: str
    position: int | None = None
    status: str
    channel_id: str | None = None
    title: str | None = None
    observed_at: datetime | None = None
    raw_json: dict[str, Any] = Field(default_factory=dict)


class ThreadPayload(_Base):
    comment: CommentPayload
    replies: list[CommentPayload] = Field(default_factory=list)


class ChannelOverviewPayload(_Base):
    channel_id: str
    observed_at: datetime | None = None
    subscribers: ValuePayload
    videos: ValuePayload
    views: ValuePayload


class VideoEngagementPayload(_Base):
    video_id: str
    observed_at: datetime | None = None
    views: ValuePayload
    likes: ValuePayload
    comments: ValuePayload
    engagement_rate: ValuePayload
    like_rate: ValuePayload
    comment_rate: ValuePayload


class PercentilesPayload(_Base):
    video_id: str
    availability: str
    observed_like_counts: list[int] = Field(default_factory=list)
    bands: dict[str, float | None] = Field(default_factory=dict)


class VelocityPoint(_Base):
    bucket: str
    count: int


class TopVideoRow(_Base):
    video_id: str
    title: str | None = None
    views: float | int | None = None
    likes: float | int | None = None
    comments: float | int | None = None
    observed_at: datetime | None = None
    availability: str = "available"


class TopVideosPayload(_Base):
    channel_id: str
    metric: str
    top: list[TopVideoRow] = Field(default_factory=list)


class SamplingResultPayload(_Base):
    strategy: str
    entity_type: str
    population_size: int
    sample_size: int
    entity_ids: list[str] = Field(default_factory=list)
    criteria_json: dict[str, Any] = Field(default_factory=dict)
    seed: int | None = None
    missing_metric_count: int = 0


class RawVideoPayload(_Base):
    video_id: str
    raw_json: dict[str, Any] = Field(default_factory=dict)


class ChannelCountPayload(_Base):
    channel_id: str
    count: int


class NetworkSummaryPayload(_Base):
    node_count: int = 0
    edge_count: int = 0
    source_count: int = 0
    target_count: int = 0
    most_recommended: list[dict[str, Any]] = Field(default_factory=list)
    most_active_sources: list[dict[str, Any]] = Field(default_factory=list)
    highest_pagerank: list[dict[str, Any]] = Field(default_factory=list)


class VideoNetworkContextPayload(_Base):
    video_id: str
    in_degree: int = 0
    out_degree: int = 0
    pagerank: float | None = None
    recommended_by: list[dict[str, Any]] = Field(default_factory=list)
    recommends: list[dict[str, Any]] = Field(default_factory=list)


class DatasetSummaryPayload(_Base):
    generated_at: datetime
    channels: int
    videos: int
    comments: int
    transcripts_available: int
    transcript_coverage: float
    runs: int


class ErrorPayload(_Base):
    """Machine-readable error envelope used by every 4xx/5xx response."""

    code: str
    message: str
    detail: str | None = None


class VariableMetaPayload(_Base):
    """One registered research variable of an entity."""

    entity: str
    name: str
    data_type: str
    source: str
    description: str
    unit: str | None = None
    availability: str
    limits: str | None = None


class OperatorInfoPayload(_Base):
    """One operator understood by the research query evaluator."""

    name: str
    description: str


class QueryPreviewStage(_Base):
    """A single funnel stage: cumulative = rows matching the prefix so far,
    matched = incremental drop caused by adding this condition."""

    condition: str
    matched: int
    cumulative: int


class QueryPreviewResponse(_Base):
    """Response of ``POST /research/query/preview``."""

    total: int
    stages: list[QueryPreviewStage] = Field(default_factory=list)
    population_size: int
    n: int


class QueryResolveResponse(_Base):
    """Count-only response of ``POST /research/query/resolve``."""

    total: int
    population_size: int
