"""Repository interfaces for the YouTube CSS module.

These abstractions allow swapping persistence implementations
(SQLite, PostgreSQL, etc.) without changing business logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from domain.models import Channel, Comment, RecommendationObservation, Video, VideoObservation


class IChannelRepository(ABC):
    """Abstract channel persistence."""

    @abstractmethod
    def save(self, channel: Channel) -> None:
        """Persist a channel."""
        ...

    @abstractmethod
    def get_by_id(self, channel_id: str) -> Optional[Channel]:
        ...

    @abstractmethod
    def get_all(self) -> List[Channel]:
        ...

    @abstractmethod
    def exists(self, channel_id: str) -> bool:
        ...


class IVideoRepository(ABC):
    """Abstract video persistence."""

    @abstractmethod
    def save(self, video: Video) -> None:
        """Persist a video."""
        ...

    @abstractmethod
    def get_by_id(self, video_id: str) -> Optional[Video]:
        ...

    @abstractmethod
    def get_by_channel(self, channel_id: str) -> List[Video]:
        ...

    @abstractmethod
    def get_all(self) -> List[Video]:
        ...

    @abstractmethod
    def exists(self, video_id: str) -> bool:
        ...


class ICommentRepository(ABC):
    """Abstract comment persistence."""

    @abstractmethod
    def save(self, comment: Comment) -> None:
        """Persist a comment."""
        ...

    @abstractmethod
    def save_many(self, comments: List[Comment]) -> None:
        """Bulk persist comments."""
        ...

    @abstractmethod
    def get_by_video(self, video_id: str) -> List[Comment]:
        ...

    @abstractmethod
    def get_by_id(self, comment_id: str) -> Optional[Comment]:
        ...

    @abstractmethod
    def get_replies(self, parent_comment_id: str) -> List[Comment]:
        ...


class IObservationRepository(ABC):
    """Abstract observation persistence for longitudinal data."""

    @abstractmethod
    def save_video_observation(self, observation: VideoObservation) -> None:
        ...

    @abstractmethod
    def save_video_observations(self, observations: List[VideoObservation]) -> None:
        ...

    @abstractmethod
    def get_video_observations(self, video_id: str) -> List[VideoObservation]:
        ...

    @abstractmethod
    def save_recommendation_observation(self, observation: RecommendationObservation) -> None:
        ...

    @abstractmethod
    def save_recommendation_observations(self, observations: List[RecommendationObservation]) -> None:
        ...

    @abstractmethod
    def get_recommendation_observations(self, source_video_id: str) -> List[RecommendationObservation]:
        ...

    @abstractmethod
    def get_all_recommendation_observations(self) -> List[RecommendationObservation]:
        ...


class IUnitOfWork(ABC):
    """Unit of work for transactional operations."""

    @abstractmethod
    def commit(self) -> None:
        ...

    @abstractmethod
    def rollback(self) -> None:
        ...
