"""
Repository interfaces for YouTube Research module.

Implements Repository Pattern for persistence abstraction, enabling
future storage backend replacements without changing business logic.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from ..domain.models import Channel, Video, Comment, CollectionRun


class ChannelRepository(ABC):
    """Abstract base class for channel persistence operations."""
    
    @abstractmethod
    def save(self, channel: Channel) -> bool:
        """Save a channel to the repository."""
        pass
    
    @abstractmethod
    def get(self, channel_id: str) -> Optional[Channel]:
        """Retrieve a channel by its ID."""
        pass
    
    @abstractmethod
    def list(self, limit: int = 100, offset: int = 0) -> List[Channel]:
        """Retrieve multiple channels with pagination."""
        pass
    
    @abstractmethod
    def delete(self, channel_id: str) -> bool:
        """Delete a channel from the repository."""
        pass
    
    @abstractmethod
    def exists(self, channel_id: str) -> bool:
        """Check if a channel exists in the repository."""
        pass


class VideoRepository(ABC):
    """Abstract base class for video persistence operations."""
    
    @abstractmethod
    def save(self, video: Video) -> bool:
        """Save a video to the repository."""
        pass
    
    @abstractmethod
    def save_batch(self, videos: List[Video]) -> int:
        """Save multiple videos efficiently."""
        pass
    
    @abstractmethod
    def get(self, video_id: str) -> Optional[Video]:
        """Retrieve a video by its ID."""
        pass
    
    @abstractmethod
    def list(self, limit: int = 100, offset: int = 0) -> List[Video]:
        """Retrieve multiple videos with pagination."""
        pass
    
    @abstractmethod
    def list_by_channel(self, channel_id: str, limit: int = 100, offset: int = 0) -> List[Video]:
        """Retrieve videos for a specific channel."""
        pass
    
    @abstractmethod
    def delete(self, video_id: str) -> bool:
        """Delete a video from the repository."""
        pass
    
    @abstractmethod
    def exists(self, video_id: str) -> bool:
        """Check if a video exists in the repository."""
        pass
    
    @abstractmethod
    def count_by_channel(self, channel_id: str) -> int:
        """Count videos for a specific channel."""
        pass
    
    @abstractmethod
    def filter(
        self,
        channel_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        duration_min: Optional[int] = None,
        duration_max: Optional[int] = None,
        views_min: Optional[int] = None,
        views_max: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "published_at",
        sort_order: str = "desc"
    ) -> List[Video]:
        """Filter videos with multiple criteria."""
        pass


class CommentRepository(ABC):
    """Abstract base class for comment persistence operations."""
    
    @abstractmethod
    def save(self, comment: Comment) -> bool:
        """Save a comment to the repository."""
        pass
    
    @abstractmethod
    def save_batch(self, comments: List[Comment]) -> int:
        """Save multiple comments efficiently."""
        pass
    
    @abstractmethod
    def get(self, comment_id: str) -> Optional[Comment]:
        """Retrieve a comment by its ID."""
        pass
    
    @abstractmethod
    def list(self, limit: int = 100, offset: int = 0) -> List[Comment]:
        """Retrieve multiple comments with pagination."""
        pass
    
    @abstractmethod
    def list_by_video(self, video_id: str, limit: int = 100, offset: int = 0) -> List[Comment]:
        """Retrieve comments for a specific video."""
        pass
    
    @abstractmethod
    def delete(self, comment_id: str) -> bool:
        """Delete a comment from the repository."""
        pass
    
    @abstractmethod
    def count_by_video(self, video_id: str) -> int:
        """Count comments for a specific video."""
        pass


class CollectionRunRepository(ABC):
    """Abstract base class for collection run persistence operations."""
    
    @abstractmethod
    def save(self, run: CollectionRun) -> bool:
        """Save a collection run to the repository."""
        pass
    
    @abstractmethod
    def get(self, run_id: str) -> Optional[CollectionRun]:
        """Retrieve a collection run by its ID."""
        pass
    
    @abstractmethod
    def list(self, limit: int = 100, offset: int = 0) -> List[CollectionRun]:
        """Retrieve multiple collection runs with pagination."""
        pass
    
    @abstractmethod
    def list_by_channel(self, channel_id: str) -> List[CollectionRun]:
        """Retrieve collection runs for a specific channel."""
        pass