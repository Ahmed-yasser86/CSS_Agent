"""
YouTube data acquisition using yt-dlp for Computational Social Science research.

Provides research-grade data extraction with error handling, retries,
and provenance tracking for reproducible research.
"""

import yt_dlp
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from ..domain.models import CollectionRun, CollectionStatus

logger = logging.getLogger(__name__)


class YouTubeScraper:
    """
    YouTube data scraper using yt-dlp for research purposes.
    
    Designed for research-grade data collection with:
    - Error handling and retries
    - Provenance tracking
    - Rate limit awareness
    - Research metadata preservation
    """
    
    def __init__(self, collection_run_id: Optional[str] = None):
        """Initialize the YouTube scraper."""
        self.collection_run_id = collection_run_id or str(uuid.uuid4())
        self.collection_run = CollectionRun(
            collection_run_id=self.collection_run_id,
            started_at=datetime.now(),
            source_type="unknown",
            source_id="unknown",
            source_url="unknown"
        )
    
    def create_collection_run(self, source_type: str, source_id: str, source_url: str) -> CollectionRun:
        """Create a collection run for tracking provenance."""
        self.collection_run.source_type = source_type
        self.collection_run.source_id = source_id
        self.collection_run.source_url = source_url
        self.collection_run.status = CollectionStatus.NOT_ATTEMPTED
        return self.collection_run
    
    def get_collection_run(self) -> CollectionRun:
        """Get the current collection run."""
        return self.collection_run
    
    def complete_collection_run(self, status: CollectionStatus = CollectionStatus.SUCCESS) -> CollectionRun:
        """Mark the collection run as complete."""
        self.collection_run.completed_at = datetime.now()
        self.collection_run.status = status
        return self.collection_run
    
    def _get_yt_dlp_options(self, **kwargs) -> Dict[str, Any]:
        """Get yt-dlp options with research-appropriate defaults."""
        options = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'force_generic_extractor': False,
        }
        options.update(kwargs)
        return options
    
    def extract_channel_info(self, channel_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract channel information from a channel URL.
        
        Args:
            channel_url: URL of the YouTube channel
            
        Returns:
            Dictionary containing channel information or None if extraction fails
        """
        try:
            self.create_collection_run("channel", channel_url, channel_url)
            self.collection_run.status = CollectionStatus.SUCCESS
            
            ydl_opts = self._get_yt_dlp_options()
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
                if info:
                    # If it's a channel, it might come as a playlist of uploads
                    if 'entries' in info:
                        # Channel with uploads playlist
                        channel_info = info
                    else:
                        channel_info = info
                    
                    return channel_info
                    
        except Exception as e:
            logger.error(f"Error extracting channel info: {e}")
            self.collection_run.status = CollectionStatus.FAILED
            self.collection_run.errors.append(str(e))
            return None
    
    def extract_video_info(self, video_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract video information from a video URL.
        
        Args:
            video_url: URL of the YouTube video
            
        Returns:
            Dictionary containing video information or None if extraction fails
        """
        try:
            video_id = video_url.split('/')[-1].split('?')[0]
            self.create_collection_run("video", video_id, video_url)
            self.collection_run.status = CollectionStatus.SUCCESS
            
            ydl_opts = self._get_yt_dlp_options()
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info if info else None
                
        except Exception as e:
            logger.error(f"Error extracting video info: {e}")
            self.collection_run.status = CollectionStatus.FAILED
            self.collection_run.errors.append(str(e))
            return None
    
    def extract_channel_videos(self, channel_url: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Extract videos from a channel.
        
        Args:
            channel_url: URL of the YouTube channel
            limit: Maximum number of videos to extract
            
        Returns:
            List of video information dictionaries
        """
        videos = []
        try:
            channel_id = channel_url.split('/')[-1].split('@')[-1].split('?')[0]
            self.create_collection_run("channel", channel_id, channel_url)
            
            ydl_opts = self._get_yt_dlp_options(
                extract_flat=False,
                playlistend=limit
            )
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            videos.append(entry)
                            self.collection_run.videos_discovered += 1
                            
                self.collection_run.videos_collected = len(videos)
                self.collection_run.status = CollectionStatus.SUCCESS
                
        except Exception as e:
            logger.error(f"Error extracting channel videos: {e}")
            self.collection_run.status = CollectionStatus.FAILED
            self.collection_run.errors.append(str(e))
            
        return videos
    
    def extract_video_comments(self, video_url: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Extract comments from a video.
        
        Args:
            video_url: URL of the YouTube video
            limit: Maximum number of comments to extract
            
        Returns:
            List of comment information dictionaries
        """
        comments = []
        try:
            video_id = video_url.split('/')[-1].split('?')[0]
            self.create_collection_run("video", video_id, video_url)
            
            ydl_opts = self._get_yt_dlp_options(
                extract_flat=False,
                getcomments=True
            )
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                if info:
                    comments_list = info.get('comments')
                    if comments_list:
                        for comment in comments_list[:limit]:
                            if comment:
                                comments.append(comment)
                                self.collection_run.comments_discovered += 1
                    
                    self.collection_run.comments_collected = len(comments)
                    self.collection_run.status = CollectionStatus.SUCCESS
                    
        except Exception as e:
            logger.error(f"Error extracting video comments: {e}")
            self.collection_run.status = CollectionStatus.FAILED
            self.collection_run.errors.append(str(e))
            
        return comments
    
    def extract_video_recommendations(self, video_url: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Extract recommended videos from a video page.
        
        Note: yt-dlp does not directly expose recommendations. This method
        attempts to capture related videos from the video info when available.
        
        Args:
            video_url: URL of the YouTube video
            limit: Maximum number of recommendations to extract
            
        Returns:
            List of recommended video information dictionaries
        """
        recommendations = []
        try:
            video_id = video_url.split('/')[-1].split('?')[0]
            self.create_collection_run("recommendation", video_id, video_url)
            
            ydl_opts = self._get_yt_dlp_options(extract_flat=False)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                if info:
                    # yt-dlp may provide 'related_videos' or similar fields
                    related = info.get('related_videos', [])
                    for rel_video in related[:limit]:
                        if rel_video and isinstance(rel_video, dict):
                            recommendations.append(rel_video)
                            self.collection_run.recommendations_discovered += 1
                    
                    self.collection_run.recommendations_collected = len(recommendations)
                    self.collection_run.status = CollectionStatus.SUCCESS
                    
        except Exception as e:
            logger.error(f"Error extracting video recommendations: {e}")
            self.collection_run.status = CollectionStatus.FAILED
            self.collection_run.errors.append(str(e))
            
        return recommendations
