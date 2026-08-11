"""
Data extraction and normalization from YouTube to domain models.

Transforms raw yt-dlp output into typed domain entities with
validation and research-appropriate transformations.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..domain.models import (
    Channel, Video, Comment, Observation
)


class DataExtractor:
    """
    Extracts and normalizes YouTube data to domain models.
    
    Transforms raw yt-dlp output into typed domain entities
    with validation and research-appropriate calculations.
    """
    
    @staticmethod
    def extract_channel(raw_data: Dict[str, Any]) -> Optional[Channel]:
        """
        Extract channel from raw yt-dlp data.
        
        Args:
            raw_data: Raw channel data from yt-dlp
            
        Returns:
            Channel domain model or None if extraction fails
        """
        try:
            channel_id = raw_data.get('channel_id') or raw_data.get('id', '')
            channel_name = raw_data.get('channel') or raw_data.get('channel_title', '')
            description = raw_data.get('description', '')
            subscriber_count = raw_data.get('subscriber_count', 0) or 0
            video_count = raw_data.get('playlist_count', 0) or raw_data.get('video_count', 0) or 0
            created_at = raw_data.get('channel_creation_date') or raw_data.get('created_at')
            playlist_id = raw_data.get('playlist_id', '')
            url = raw_data.get('webpage_url', f'https://www.youtube.com/channel/{channel_id}')
            
            # Handle playlist entries (channel uploads)
            if 'entries' in raw_data:
                # This is a playlist of videos, not a channel
                return None
            
            return Channel(
                channel_id=channel_id,
                title=channel_name,
                description=description,
                subscriber_count=subscriber_count,
                video_count=video_count,
                playlist_id=playlist_id or channel_id,  # Use channel_id as fallback
                url=url,
                created_at=created_at,
                collection_run_id=raw_data.get('collection_run_id', '')
            )
            
        except Exception as e:
            return None
    
    @staticmethod
    def extract_video(raw_data: Dict[str, Any]) -> Optional[Video]:
        """
        Extract video from raw yt-dlp data.
        
        Args:
            raw_data: Raw video data from yt-dlp
            
        Returns:
            Video domain model or None if extraction fails
        """
        try:
            video_id = raw_data.get('id') or raw_data.get('video_id', '')
            channel_id = raw_data.get('channel_id', '')
            channel_title = raw_data.get('channel', '') or raw_data.get('channel_title', '')
            title = raw_data.get('title', '')
            description = raw_data.get('description', '')
            published_at = raw_data.get('upload_date') or raw_data.get('published_at') or raw_data.get('timestamp')
            duration = raw_data.get('duration', 0) or 0
            view_count = raw_data.get('view_count', 0) or 0
            like_count = raw_data.get('like_count', 0) or 0
            comment_count = raw_data.get('comment_count', 0) or 0
            
            # Calculate engagement rates
            engagement = DataExtractor._calculate_engagement(
                view_count, like_count, comment_count, duration
            )
            
            return Video(
                video_id=video_id,
                channel_id=channel_id,
                channel_title=channel_title,
                title=title,
                description=description,
                published_at=published_at,
                duration=duration,
                view_count=view_count,
                like_count=like_count,
                comment_count=comment_count,
                engagement_rate=engagement['engagement_rate'],
                like_rate=engagement['like_rate'],
                comment_rate=engagement['comment_rate'],
                collection_run_id=raw_data.get('collection_run_id', ''),
                url=raw_data.get('webpage_url', f'https://youtube.com/watch?v={video_id}')
            )
            
        except Exception as e:
            return None
    
    @staticmethod
    def extract_comment(raw_data: Dict[str, Any]) -> Optional[Comment]:
        """
        Extract comment from raw yt-dlp data.
        
        Args:
            raw_data: Raw comment data from yt-dlp
            
        Returns:
            Comment domain model or None if extraction fails
        """
        try:
            comment_id = raw_data.get('id', '')
            video_id = raw_data.get('video_id', '')
            author_name = raw_data.get('author') or raw_data.get('author_name', '')
            author_id = raw_data.get('author_id')
            text = raw_data.get('text', raw_data.get('content', ''))
            published_at = raw_data.get('timestamp') or raw_data.get('published_at')
            like_count = raw_data.get('like_count', 0) or 0
            parent_id = raw_data.get('parent') or raw_data.get('parent_id') or None
            
            # Handle nested replies
            is_reply = parent_id is not None and parent_id != ''
            
            return Comment(
                comment_id=comment_id,
                video__id=video_id,
                channel_id=raw_data.get('channel_id', ''),
                author_id=author_id,
                author_name=author_name,
                text=text,
                published_at=published_at,
                like_count=like_count,
                is_reply=is_reply,
                parent_id=parent_id if is_reply else None,
                collection_run_id=raw_data.get('collection_run_id', '')
            )
            
        except Exception as e:
            return None
    
    @staticmethod
    def extract_observation(raw_data: Dict[str, Any], observation_type: str) -> Optional[Observation]:
        """
        Extract observation from raw data for historical tracking.
        
        Args:
            raw_data: Raw data containing the observation value
            observation_type: Type of observation (view_count, subscriber_count, etc.)
            
        Returns:
            Observation domain model or None if extraction fails
        """
        try:
            value = raw_data.get(observation_type, 0) or 0
            source = raw_data.get('source', 'youtube_api')
            collection_run_id = raw_data.get('collection_run_id', '')
            
            return Observation(
                observed_at=datetime.now(),
                value=float(value),
                source=source,
                collection_run_id=collection_run_id
            )
            
        except Exception as e:
            return None
    
    @staticmethod
    def _calculate_engagement(
        view_count: int, 
        like_count: int, 
        comment_count: int,
        duration: int
    ) -> Dict[str, float]:
        """
        Calculate engagement rates for research analysis.
        
        Args:
            view_count: Number of views
            like_count: Number of likes
            comment_count: Number of comments
            duration: Video duration in seconds
            
        Returns:
            Dictionary with calculated engagement metrics
        """
        # Engagement rate: (likes + comments) / views * 100
        engagement_rate = 0.0
        if view_count > 0:
            engagement_rate = ((like_count + comment_count) / view_count) * 100
        
        # Like rate: likes / views * 100
        like_rate = 0.0
        if view_count > 0:
            like_rate = (like_count / view_count) * 100
        
        # Comment rate: comments / views * 100
        comment_rate = 0.0
        if view_count > 0:
            comment_rate = (comment_count / view_count) * 100
        
        # View-to-duration ratio (views per second of content)
        view_per_second = 0.0
        if duration > 0:
            view_per_second = view_count / duration
        
        return {
            'engagement_rate': engagement_rate,
            'like_rate': like_rate,
            'comment_rate': comment_rate,
            'view_per_second': view_per_second
        }
    
    @staticmethod
    def extract_recommendation_relationship(
        source_video_id: str,
        recommended_video: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract recommendation relationship for network analysis.
        
        Args:
            source_video_id: ID of the source video
            recommended_video: Raw data of the recommended video
            
        Returns:
            Dictionary with relationship data for network construction
        """
        try:
            target_video_id = recommended_video.get('id', '')
            if not target_video_id:
                return None
                
            return {
                'source_video_id': source_video_id,
                'target_video_id': target_video_id,
                'target_title': recommended_video.get('title', ''),
                'target_channel': recommended_video.get('channel', ''),
                'relationship_type': 'recommendation'
            }
            
        except Exception as e:
            return None
