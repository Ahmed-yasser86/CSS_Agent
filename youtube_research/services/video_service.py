"""Video service for YouTube research."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ..domain.models import Video, Comment, CollectionRun, CollectionStatus
from ..persistence.repository import VideoRepository, CommentRepository
from ..acquisition.youtube_scraper import YouTubeScraper
from ..acquisition.data_extractor import DataExtractor


class VideoService:
    """Service for video-related research operations."""
    
    def __init__(
        self,
        video_repository: VideoRepository,
        comment_repository: CommentRepository,
        scraper: Optional[YouTubeScraper] = None
    ):
        self.video_repository = video_repository
        self.comment_repository = comment_repository
        self.scraper = scraper or YouTubeScraper()
        self.data_extractor = DataExtractor()
    
    def collect_video(self, video_url: str) -> Optional[Video]:
        """
        Collect video data from YouTube and persist.
        
        Args:
            video_url: URL of the YouTube video
            
        Returns:
            Collected Video or None if collection failed
        """
        # Extract video info
        raw_data = self.scraper.extract_video_info(video_url)
        if not raw_data:
            return None
        
        # Transform to domain model
        video = self.data_extractor.extract_video(raw_data)
        if not video:
            return None
        
        # Save to repository
        self.video_repository.save(video)
        
        # Update collection run
        collection_run = self.scraper.get_collection_run()
        collection_run.source_id = video.video_id
        collection_run.status = CollectionStatus.SUCCESS
        
        return video
    
    def collect_video_with_comments(
        self, 
        video_url: str, 
        comment_limit: int = 1000
    ) -> Optional[Video]:
        """
        Collect video data with comments.
        
        Args:
            video_url: URL of the YouTube video
            comment_limit: Maximum number of comments to collect
            
        Returns:
            Collected Video or None if collection failed
        """
        # Collect video first
        video = self.collect_video(video_url)
        if not video:
            return None
        
        # Collect comments
        raw_comments = self.scraper.extract_video_comments(video_url, comment_limit)
        
        for raw_comment in raw_comments:
            comment = self.data_extractor.extract_comment(raw_comment)
            if comment:
                comment.video_id = video.video_id
                self.comment_repository.save(comment)
        
        return video
    
    def get_video(self, video_id: str) -> Optional[Video]:
        """Get a video by ID."""
        return self.video_repository.get(video_id)
    
    def list_videos(self, limit: int = 100) -> List[Video]:
        """List all videos."""
        return self.video_repository.list(limit)
    
    def list_videos_by_channel(self, channel_id: str) -> List[Video]:
        """List all videos for a channel."""
        return self.video_repository.list_by_channel(channel_id)
    
    def video_exists(self, video_id: str) -> bool:
        """Check if a video exists."""
        return self.video_repository.exists(video_id)
    
    def get_video_comments(self, video_id: str) -> List[Comment]:
        """Get all comments for a video."""
        return self.comment_repository.filter(video_id=video_id)
    
    def calculate_comment_velocity(self, video_id: str) -> float:
        """
        Calculate comment velocity (comments per day since publication).
        
        Args:
            video_id: Video ID to analyze
            
        Returns:
            Comment velocity or 0 if video not found
        """
        video = self.video_repository.get(video_id)
        if not video:
            return 0.0
        
        comments = self.comment_repository.filter(video_id=video_id)
        if not video.published_at:
            return 0.0
        
        days_since_publication = (datetime.now() - video.published_at).days
        if days_since_publication <= 0:
            return float(len(comments))
        
        return len(comments) / days_since_publication
    
    def calculate_engagement_concentration(self, video_id: str) -> float:
        """
        Calculate engagement concentration using Gini coefficient.
        
        Args:
            video_id: Video ID to analyze
            
        Returns:
            Gini coefficient (0 = equal distribution, 1 = max concentration)
        """
        comments = self.comment_repository.filter(video_id=video_id)
        if not comments:
            return 0.0
        
        # Get like counts for all comments
        like_counts = sorted([c.like_count for c in comments])
        n = len(like_counts)
        
        if n < 2:
            return 0.0
        
        # Calculate Gini coefficient
        cumsum = sum(like_counts)
        if cumsum == 0:
            return 0.0
        
        gini_num = sum((2 * i + 1 - n) * lc for i, lc in enumerate(like_counts))
        gini_denom = n * cumsum
        
        return gini_num / gini_denom if gini_denom != 0 else 0.0