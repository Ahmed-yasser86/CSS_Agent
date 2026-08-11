"""
Repository interfaces for YouTube Computational Social Science research.

Defines abstract base classes for persistence operations, enabling the
repository pattern and facilitating future storage backend implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..domain.models import Channel, Video, Comment, Recommendation, CollectionRun


class ChannelRepository(ABC):
    """Abstract base class for channel persistence operations."""
    
    @abstractmethod
    def save_channel(self, channel: Channel) -> bool:
        """Save a channel to the repository."""
        pass
    
    @abstractmethod
    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Retrieve a channel by its ID."""
        pass
    
    @abstractmethod
    def get_channels(self, limit: int = 100, offset: int = 0) -> List[Channel]:
        """Retrieve multiple channels with pagination."""
        pass
    
    @abstractmethod
    def get_channel_videos(self, channel_id: str, limit: int = 100, offset: int = 0) -> List[Video]:
        """Retrieve videos for a specific channel."""
        pass
    
    @abstractmethod
    def get_channel_analytics(self, channel_id: str) -> Dict[str, Any]:
        """Retrieve analytics for a specific channel."""
        pass
    
    @abstractmethod
    def delete_channel(self, channel_id: str) -> bool:
        """Delete a channel from the repository."""
        pass


class VideoRepository(ABC):
    """Abstract base class for video persistence operations."""
    
    @abstractmethod
    def save_video(self, video: Video) -> bool:
        """Save a video to the repository."""
        pass
    
    @abstractmethod
    def get_video(self, video_id: str) -> Optional[Video]:
        """Retrieve a video by its ID."""
        pass
    
    @abstractmethod
    def get_videos(self, limit: int = 100, offset: int = 0) -> List[Video]:
        """Retrieve multiple videos with pagination."""
        pass
    
    @abstractmethod
    def get_video_comments(self, video_id: str, limit: int = 100, offset: int = 0) -> List[Comment]:
        """Retrieve comments for a specific video."""
        pass
    
    @abstractmethod
    def get_video_analytics(self, video_id: str) -> Dict[str, Any]:
        """Retrieve analytics for a specific video."""
        pass
    
    @abstractmethod
    def delete_video(self, video_id: str) -> bool:
        """Delete a video from the repository."""
        pass


class CommentRepository(ABC):
    """Abstract base class for comment persistence operations."""
    
    @abstractmethod
    def save_comment(self, comment: Comment) -> bool:
        """Save a comment to the repository."""
        pass
    
    @abstractmethod
    def get_comment(self, comment_id: str) -> Optional[Comment]:
        """Retrieve a comment by its ID."""
        pass
    
    @abstractmethod
    def get_comments(self, limit: int = 100, offset: int = 0) -> List[Comment]:
        """Retrieve multiple comments with pagination."""
        pass
    
    @abstractmethod
    def get_video_comments(self, video_id: str, limit: int = 100, offset: int = 0) -> List[Comment]:
        """Retrieve comments for a specific video."""
        pass
    
    @abstractmethod
    def get_comment_replies(self, comment_id: str, limit: int = 100, offset: int = 0) -> List[Comment]:
        """Retrieve replies for a specific comment."""
        pass
    
    @abstractmethod
    def get_comment_analytics(self, comment_id: str) -> Dict[str, Any]:
        """Retrieve analytics for a specific comment."""
        pass
    
    @abstractmethod
    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment from the repository."""
        pass


class RecommendationRepository(ABC):
    """Abstract base class for recommendation persistence operations."""
    
    @abstractmethod
    def save_recommendation(self, recommendation: Recommendation) -> bool:
        """Save a recommendation to the repository."""
        pass
    
    @abstractmethod
    def get_recommendations_for_video(self, video_id: str, limit: int = 100, offset: int = 0) -> List[Recommendation]:
        """Retrieve recommendations for a specific video."""
        pass
    
    @abstractmethod
    def get_recommendations_from_video(self, video_id: str, limit: int = 100, offset: int = 0) -> List[Recommendation]:
        """Retrieve recommendations from a specific video."""
        pass
    
    @abstractmethod
    def get_video_recommendations(self, video_id: str) -> List[Recommendation]:
        """Retrieve all recommendations for a video (both for and from)."""
        pass
    
    @abstractmethod
    def get_collection_runs_for_video(self, video_id: str) -> List[CollectionRun]:
        """Retrieve collection runs for a specific video."""
        pass
    
    @abstractmethod
    def get_recommendations_by_run(self, collection_run_id: str) -> List[Recommendation]:
        """Retrieve recommendations from a specific collection run."""
        pass
    
    @abstractmethod
    def get_recommendation_network(self, video_ids: List[str]) -> Dict[str, Any]:
        """Retrieve a recommendation network for the specified videos."""
        pass
    
    @abstractmethod
    def delete_recommendation(self, source_video_id: str, recommended_video_id: str) -> bool:
        """Delete a recommendation from the repository."""
        pass


class CollectionRunRepository(ABC):
    """Abstract base class for collection run persistence operations."""
    
    @abstractmethod
    def save_collection_run(self, collection_run: CollectionRun) -> bool:
        """Save a collection run to the repository."""
        pass
    
    @abstractmethod
    def get_collection_run(self, collection_run_id: str) -> Optional[CollectionRun]:
        """Retrieve a collection run by its ID."""
        pass
    
    @abstractmethod
    def get_collection_runs(self, limit: int = 100, offset: int = 0) -> List[CollectionRun]:
        """Retrieve multiple collection runs with pagination."""
        pass
    
    @abstractmethod
    def get_collection_runs_for_source(self, source_type: str, source_id: str) -> List[CollectionRun]:
        """Retrieve collection runs for a specific source."""
        pass
    
    @abstractmethod
    def delete_collection_run(self, collection_run_id: str) -> bool:
        """Delete a collection run from the repository."""
        pass