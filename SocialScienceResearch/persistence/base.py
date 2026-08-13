"""Repository interfaces for the SocialScienceResearch module.

These abstract base classes are the only persistence contract the services and
analytics layers depend on. The Excel implementation in
``persistence.excel_repository`` provides the concrete repositories today; a
SQL/PostgreSQL/SQLite implementation can replace it later without touching
business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from SocialScienceResearch.domain.enums import EntityType, RunType
from SocialScienceResearch.domain.models import (
    AuthorProfile,
    Channel,
    ChannelObservation,
    CollectionError,
    CollectionRun,
    Comment,
    CommentObservation,
    RecommendationObservation,
    TranscriptRecord,
    Video,
    VideoObservation,
)
from SocialScienceResearch.domain.dataset_models import Dataset, ProjectItem
from SocialScienceResearch.domain.sample_models import Sample


@dataclass(frozen=True)
class UpsertResult:
    """Outcome of an upsert operation: was the entity newly created?"""

    entity_type: EntityType
    entity_id: str
    created: bool


@dataclass
class Repositories:
    """Container of all repository interfaces.

    Services depend on this container (not on concrete Excel classes), so a
    SQL backend can be dropped in by constructing the same container with SQL
    repository implementations.
    """

    channels: ChannelRepository
    videos: VideoRepository
    comments: CommentRepository
    runs: CollectionRunRepository
    recommendations: RecommendationRepository
    transcripts: TranscriptRepository
    authors: AuthorRepository
    datasets: DatasetRepository
    samples: SampleRepository
    project_items: ProjectItemRepository


class ChannelRepository(ABC):
    """Persistence contract for channels and channel observations."""

    @abstractmethod
    def upsert_channel(self, channel: Channel) -> UpsertResult:
        """Insert a new channel or return ``created=False`` if it exists."""

    @abstractmethod
    def get_channel(self, channel_id: str) -> Channel | None:
        """Return the channel with the given stable id, if present."""

    @abstractmethod
    def list_channels(self) -> list[Channel]:
        """Return all known channels."""

    @abstractmethod
    def save_channel_observation(self, observation: ChannelObservation) -> None:
        """Persist one run-scoped observation (idempotent by observation id)."""

    @abstractmethod
    def list_channel_observations(self, channel_id: str) -> list[ChannelObservation]:
        """Return all observations of a channel, oldest first."""

    @abstractmethod
    def get_latest_channel_observation(
        self, channel_id: str
    ) -> ChannelObservation | None:
        """Return the most recent observation of a channel, if any."""

    @abstractmethod
    def get_latest_channel_observations(
        self, channel_ids: list[str]
    ) -> dict[str, ChannelObservation]:
        """Return the most recent observation of each channel in one scan.

        The result dict is keyed by channel id (preserving the input order)
        and contains an entry only for ids that have at least one observation.
        This batch method replaces the N+1 ``get_latest_channel_observation``
        loop with a single pass over the observation sheet.
        """


class VideoRepository(ABC):
    """Persistence contract for videos and video observations."""

    @abstractmethod
    def upsert_video(self, video: Video) -> UpsertResult:
        """Insert a new video or return ``created=False`` if it exists."""

    @abstractmethod
    def get_video(self, video_id: str) -> Video | None:
        """Return the video with the given stable id, if present."""

    @abstractmethod
    def list_videos(self, channel_id: str | None = None) -> list[Video]:
        """Return all videos, optionally filtered by channel."""

    @abstractmethod
    def list_videos_by_run(self, run_id: str) -> list[Video]:
        """Return videos first discovered in the given collection run."""

    @abstractmethod
    def save_video_observation(self, observation: VideoObservation) -> None:
        """Persist one run-scoped observation (idempotent by observation id)."""

    @abstractmethod
    def list_video_observations(self, video_id: str) -> list[VideoObservation]:
        """Return all observations of a video, oldest first."""

    @abstractmethod
    def get_latest_video_observation(self, video_id: str) -> VideoObservation | None:
        """Return the most recent observation of a video, if any."""

    @abstractmethod
    def get_latest_video_observations(
        self, video_ids: list[str]
    ) -> dict[str, VideoObservation]:
        """Return the most recent observation of each video in one scan.

        Keyed by video id (input order preserved); ids without an observation
        are simply absent. Replaces the N+1 ``get_latest_video_observation``
        loop with a single pass over the observation sheet.
        """


class CommentRepository(ABC):
    """Persistence contract for comments and comment observations."""

    @abstractmethod
    def upsert_comment(self, comment: Comment) -> UpsertResult:
        """Insert a new comment or return ``created=False`` if it exists."""

    @abstractmethod
    def get_comment(self, comment_id: str) -> Comment | None:
        """Return the comment with the given stable id, if present."""

    @abstractmethod
    def list_comments(self, video_id: str | None = None) -> list[Comment]:
        """Return comments (roots and replies), optionally for a video."""

    @abstractmethod
    def list_root_comments(self, video_id: str) -> list[Comment]:
        """Return only root comments (parents of threads) for a video."""

    @abstractmethod
    def list_replies(self, parent_comment_id: str) -> list[Comment]:
        """Return the direct replies of a comment."""

    @abstractmethod
    def list_replies_by_ids(self, parent_comment_ids: list[str]) -> dict[str, list[Comment]]:
        """Return direct replies for multiple parent comments in one scan.

        Returns a dict keyed by parent_comment_id with lists of reply comments.
        """

    @abstractmethod
    def save_comment_observation(self, observation: CommentObservation) -> None:
        """Persist one run-scoped observation (idempotent by observation id)."""

    @abstractmethod
    def list_comment_observations(
        self, video_id: str | None = None, comment_id: str | None = None
    ) -> list[CommentObservation]:
        """Return comment observations, optionally filtered."""

    @abstractmethod
    def get_latest_comment_observation(
        self, comment_id: str
    ) -> CommentObservation | None:
        """Return the most recent observation of a comment, if any."""

    @abstractmethod
    def get_latest_comment_observations(
        self, comment_ids: list[str]
    ) -> dict[str, CommentObservation]:
        """Return the most recent observation of each comment in one scan.

        Keyed by comment id (input order preserved); ids without an
        observation are simply absent. Replaces the N+1
        ``get_latest_comment_observation`` loop with a single pass over the
        observation sheet.
        """


class CollectionRunRepository(ABC):
    """Persistence contract for collection runs and their failures."""

    @abstractmethod
    def create_run(self, run: CollectionRun) -> None:
        """Persist a new run record."""

    @abstractmethod
    def update_run(self, run: CollectionRun) -> None:
        """Update an existing run record (by ``run_id``)."""

    @abstractmethod
    def get_run(self, run_id: str) -> CollectionRun | None:
        """Return the run with the given id, if present."""

    @abstractmethod
    def list_runs(self, run_type: RunType | None = None) -> list[CollectionRun]:
        """Return runs, optionally filtered by type, oldest first."""

    @abstractmethod
    def record_error(self, error: CollectionError) -> None:
        """Persist a per-entity failure so failures are never silently dropped."""

    @abstractmethod
    def list_errors(self, run_id: str) -> list[CollectionError]:
        """Return all recorded errors for a run."""


class RecommendationRepository(ABC):
    """Persistence contract for observed recommendation relationships.

    The stored data is *network-ready*: each row is a directed edge
    ``source_video_id -> recommended_video_id`` observed during a run, which a
    future module can load into NetworkX.
    """

    @abstractmethod
    def save_recommendation(self, observation: RecommendationObservation) -> UpsertResult:
        """Persist one observed relationship (idempotent by run + source + target)."""

    @abstractmethod
    def list_recommendations_for_source(
        self, source_video_id: str, run_id: str | None = None
    ) -> list[RecommendationObservation]:
        """Return observed recommendations for a source video, optionally per run."""

    @abstractmethod
    def list_recommendation_edges(
        self,
        source_video_id: str | None = None,
        run_id: str | None = None,
    ) -> list[RecommendationObservation]:
        """Return recommendation edges for network construction."""

    @abstractmethod
    def list_source_video_ids(self) -> list[str]:
        """Return distinct source videos that have recommendation observations."""


class TranscriptRepository(ABC):
    """Persistence contract for video transcript artifacts.

    Transcript *content* is stored as external files (never inside the Excel
    workbook); this repository persists the metadata reference, provenance and
    explicit status (available/missing/unsupported) so transcript coverage is
    auditable and a future SQL provider can keep files + metadata separately.
    """

    @abstractmethod
    def save_transcript(self, record: TranscriptRecord) -> None:
        """Persist one transcript record (idempotent by transcript id)."""

    @abstractmethod
    def get_transcript(self, video_id: str) -> TranscriptRecord | None:
        """Return the most recent transcript record for a video, if any."""

    @abstractmethod
    def list_transcripts(
        self, video_id: str | None = None
    ) -> list[TranscriptRecord]:
        """Return transcript records, optionally filtered by video."""


class AuthorRepository(ABC):
    """Persistence contract for aggregated author participation profiles (D4).

    Author profiles are *derived* from the persisted comments corpus: each
    profile aggregates one ``author_id`` (falling back to ``author_name``),
    so this repository is a read-side projection over comments rather than an
    independently collected entity. The abstraction exists so a future SQL
    backend can materialize the same projection without changing services.
    """

    @abstractmethod
    def list_authors(self) -> list[AuthorProfile]:
        """Return one aggregated profile per comment author, id-ordered."""

    @abstractmethod
    def get_author(self, author_id: str) -> AuthorProfile | None:
        """Return the aggregated profile of one author, if any comments exist."""


class ProjectItemRepository(ABC):
    """Persistence contract for ProjectItems (sub-items within a research project)."""

    @abstractmethod
    def save_item(self, item: ProjectItem) -> None:
        """Persist a project item (upsert by item_id)."""

    @abstractmethod
    def get_item(self, item_id: str) -> ProjectItem | None:
        """Return the project item with the given id, if present."""

    @abstractmethod
    def list_items(self, project_id: str | None = None) -> list[ProjectItem]:
        """Return all project items, optionally filtered by project_id."""

    @abstractmethod
    def list_items_by_project(self, project_id: str) -> list[ProjectItem]:
        """Return all items belonging to a specific project."""

    @abstractmethod
    def update_item(self, item: ProjectItem) -> None:
        """Update an existing project item."""

    @abstractmethod
    def delete_item(self, item_id: str) -> None:
        """Delete a project item."""
