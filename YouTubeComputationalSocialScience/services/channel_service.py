"""
Channel analysis service for YouTube Computational Social Science research.

Orchestrates the channel analysis workflow including data acquisition,
persistence, analytics, and research output generation.
"""

import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from ..domain.models import Channel, Video, Comment, CollectionRun, CollectionStatus, ChannelAnalytics
from ..domain.analytics import calculate_channel_analytics
from ..domain.sampling import sample_videos
from ..acquisition.youtube_scraper import YouTubeScraper
from ..acquisition.data_extractor import extract_channel_data, extract_video_data, extract_comment_data
from ..persistence.repository import ChannelRepository, VideoRepository, CommentRepository


class ChannelService:
    """
    Service for YouTube channel analysis workflows.
    
    Orchestrates the complete channel analysis pipeline from data acquisition
    to research output generation.
    """
    
    def __init__(self, 
                 channel_repository: ChannelRepository,
                 video_repository: VideoRepository,
                 comment_repository: CommentRepository):
        """
        Initialize the channel service.
        
        Args:
            channel_repository: Repository for channel persistence
            video_repository: Repository for video persistence
            comment_repository: Repository for comment persistence
        """
        self.channel_repository = channel_repository
        self.video_repository = video_repository
        self.comment_repository = comment_repository
    
    def analyze_channel(self, channel_url: str, 
                       video_limit: int = 100,
                       comment_limit: int = 1000,
                       sampling_strategy: str = "stratified",
                       **sampling_kwargs) -> Dict[str, Any]:
        """
        Analyze a YouTube channel and return comprehensive research data.
        
        Args:
            channel_url: URL of the YouTube channel to analyze
            video_limit: Maximum number of videos to collect
            comment_limit: Maximum number of comments to collect per video
            sampling_strategy: Strategy for sampling videos (random, stratified, top_performers, etc.)
            sampling_kwargs: Additional arguments for the sampling strategy
            
        Returns:
            Dictionary containing analysis results and metadata
        """
        # Create collection run
        collection_run_id = str(uuid.uuid4())
        scraper = YouTubeScraper(collection_run_id)
        scraper.create_collection_run("channel", channel_url.split('/')[-1], channel_url)
        
        try:
            # Step 1: Extract channel metadata
            channel_info = scraper.extract_channel_info(channel_url)
            if not channel_info:
                return {"status": "failed", "error": "Could not extract channel info", "collection_run_id": collection_run_id}
            
            # Step 2: Normalize and save channel
            channel = extract_channel_data(channel_info, collection_run_id)
            self.channel_repository.save_channel(channel)
            
            # Step 3: Extract and save videos
            videos = self._collect_channel_videos(scraper, channel_url, channel.channel_id, video_limit)
            
            # Step 4: Apply sampling strategy
            sampled_videos = sample_videos(videos, strategy=sampling_strategy, **sampling_kwargs)
            
            # Step 5: Collect comments for sampled videos
            self._collect_video_comments(scraper, sampled_videos, comment_limit)
            
            # Step 6: Calculate analytics
            analytics = self._calculate_channel_analytics(channel, videos)
            
            # Complete collection run
            scraper.complete_collection_run()
            
            return {
                "status": "success",
                "collection_run_id": collection_run_id,
                "channel": channel.model_dump(),
                "videos_collected": len(videos),
                "videos_sampled": len(sampled_videos),
                "analytics": analytics.model_dump(),
                "collection_run": scraper.get_collection_run().model_dump()
            }
            
        except Exception as e:
            # Mark collection as failed
            scraper.complete_collection_run(CollectionStatus.FAILED)
            return {
                "status": "failed",
                "error": str(e),
                "collection_run_id": collection_run_id,
                "collection_run": scraper.get_collection_run().model_dump()
            }
    
    def _collect_channel_videos(self, scraper: YouTubeScraper, channel_url: str, channel_id: str, limit: int) -> List[Video]:
        """Collect and save videos from a channel."""
        videos_data = scraper.extract_channel_videos(channel_url, limit)
        videos = []
        
        for video_data in videos_data:
            try:
                video = extract_video_data(video_data, scraper.collection_run_id, channel_id)
                self.video_repository.save_video(video)
                videos.append(video)
            except Exception as e:
                scraper.collection_run.errors.append(f"Video extraction failed: {str(e)}")
                scraper.collection_run.videos_failed += 1
                continue
        
        return videos
    
    def _collect_video_comments(self, scraper: YouTubeScraper, videos: List[Video], limit: int):
        """Collect and save comments for a list of videos."""
        for video in videos:
            try:
                comments_data = scraper.extract_video_comments(video.url, limit)
                
                for comment_data in comments_data:
                    try:
                        comment = extract_comment_data(
                            comment_data, 
                            scraper.collection_run_id, 
                            video.video_id, 
                            video.channel_id
                        )
                        self.comment_repository.save_comment(comment)
                        
                        # Update reply count for parent comments
                        if comment.parent_id:
                            parent_comment = self.comment_repository.get_comment(comment.parent_id)
                            if parent_comment:
                                parent_comment.reply_count += 1
                                self.comment_repository.save_comment(parent_comment)
                                
                    except Exception as e:
                        scraper.collection_run.errors.append(f"Comment extraction failed: {str(e)}")
                        scraper.collection_run.comments_failed += 1
                        continue
                        
            except Exception as e:
                scraper.collection_run.errors.append(f"Comments for video {video.video_id} failed: {str(e)}")
                continue
    
    def _calculate_channel_analytics(self, channel: Channel, videos: List[Video]) -> ChannelAnalytics:
        """Calculate analytics for a channel."""
        return calculate_channel_analytics(channel, videos)
    
    def get_channel_analytics(self, channel_id: str) -> Dict[str, Any]:
        """
        Get pre-calculated analytics for a channel.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            Dictionary containing channel analytics
        """
        channel = self.channel_repository.get_channel(channel_id)
        if not channel:
            return {"status": "not_found", "error": "Channel not found"}
        
        videos = self.channel_repository.get_channel_videos(channel_id)
        analytics = calculate_channel_analytics(channel, videos)
        
        return {
            "status": "success",
            "channel_id": channel_id,
            "analytics": analytics.model_dump()
        }
    
    def compare_channels(self, channel_ids: List[str], period: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Compare multiple channels across various metrics.
        
        Args:
            channel_ids: List of channel IDs to compare
            period: Optional time period to filter videos
            
        Returns:
            Dictionary containing comparative analytics
        """
        comparison_data = {}
        
        for channel_id in channel_ids:
            channel = self.channel_repository.get_channel(channel_id)
            if not channel:
                continue
            
            videos = self.channel_repository.get_channel_videos(channel_id)
            
            # Filter by period if specified
            if period:
                start_date, end_date = period
                videos = [v for v in videos if start_date <= v.published_at <= end_date]
            
            analytics = calculate_channel_analytics(channel, videos)
            
            comparison_data[channel_id] = {
                "channel": channel.model_dump(),
                "analytics": analytics.model_dump(),
                "video_count": len(videos)
            }
        
        return {
            "status": "success",
            "comparison": comparison_data,
            "channels_compared": len(comparison_data)
        }
    
    def get_channel_upload_pattern(self, channel_id: str) -> Dict[str, Any]:
        """
        Analyze the upload pattern of a channel.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            Dictionary containing upload pattern analysis
        """
        channel = self.channel_repository.get_channel(channel_id)
        if not channel:
            return {"status": "not_found", "error": "Channel not found"}
        
        videos = self.channel_repository.get_channel_videos(channel_id)
        if not videos:
            return {"status": "no_data", "error": "No videos found for channel"}
        
        # Sort videos by publication date
        sorted_videos = sorted(videos, key=lambda v: v.published_at)
        
        # Calculate upload frequency by time period
        upload_pattern = {
            "hourly": {},
            "daily": {},
            "weekly": {},
            "monthly": {},
            "yearly": {}
        }
        
        for video in sorted_videos:
            # Hour of day
            hour_key = video.published_at.strftime("%H")
            upload_pattern["hourly"][hour_key] = upload_pattern["hourly"].get(hour_key, 0) + 1
            
            # Day of week
            weekday_key = video.published_at.strftime("%A")
            upload_pattern["daily"][weekday_key] = upload_pattern["daily"].get(weekday_key, 0) + 1
            
            # Week of year
            week_key = video.published_at.strftime("%Y-%U")
            upload_pattern["weekly"][week_key] = upload_pattern["weekly"].get(week_key, 0) + 1
            
            # Month of year
            month_key = video.published_at.strftime("%Y-%m")
            upload_pattern["monthly"][month_key] = upload_pattern["monthly"].get(month_key, 0) + 1
            
            # Year
            year_key = str(video.published_at.year)
            upload_pattern["yearly"][year_key] = upload_pattern["yearly"].get(year_key, 0) + 1
        
        # Calculate average gaps between uploads
        gaps = []
        for i in range(1, len(sorted_videos)):
            gap = (sorted_videos[i].published_at - sorted_videos[i-1].published_at).days
            gaps.append(gap)
        
        avg_gap = sum(gaps) / len(gaps) if gaps else 0
        
        return {
            "status": "success",
            "channel_id": channel_id,
            "upload_pattern": upload_pattern,
            "total_videos": len(videos),
            "avg_gap_between_uploads_days": avg_gap,
            "first_upload": sorted_videos[0].published_at.isoformat() if sorted_videos else None,
            "last_upload": sorted_videos[-1].published_at.isoformat() if sorted_videos else None
        }
    
    def get_channel_engagement_analysis(self, channel_id: str) -> Dict[str, Any]:
        """
        Get comprehensive engagement analysis for a channel.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            Dictionary containing engagement analysis
        """
        channel = self.channel_repository.get_channel(channel_id)
        if not channel:
            return {"status": "not_found", "error": "Channel not found"}
        
        videos = self.channel_repository.get_channel_videos(channel_id)
        if not videos:
            return {"status": "no_data", "error": "No videos found for channel"}
        
        # Calculate engagement metrics for all videos
        view_counts = []
        like_counts = []
        comment_counts = []
        engagement_rates = []
        
        for video in videos:
            views = video.view_count_observations[-1].value if video.view_count_observations else video.view_count
            likes = video.like_count_observations[-1].value if video.like_count_observations else video.like_count
            comments = video.comment_count_observations[-1].value if video.comment_count_observations else video.comment_count
            
            view_counts.append(views)
            like_counts.append(likes)
            comment_counts.append(comments)
            
            if views > 0:
                engagement_rates.append((likes + comments) / views)
        
        # Calculate percentiles
        sorted_views = sorted(view_counts)
        sorted_likes = sorted(like_counts)
        sorted_comments = sorted(comment_counts)
        n = len(sorted_views)
        
        def percentile(sorted_list, p):
            if not sorted_list:
                return 0
            idx = int(len(sorted_list) * p / 100)
            return sorted_list[min(idx, len(sorted_list) - 1)]
        
        return {
            "status": "success",
            "channel_id": channel_id,
            "engagement_analysis": {
                "summary": {
                    "total_videos": len(videos),
                    "total_views": sum(view_counts),
                    "total_likes": sum(like_counts),
                    "total_comments": sum(comment_counts),
                    "avg_engagement_rate": sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0
                },
                "view_distribution": {
                    "min": min(view_counts) if view_counts else 0,
                    "p10": percentile(sorted_views, 10),
                    "p25": percentile(sorted_views, 25),
                    "median": percentile(sorted_views, 50),
                    "p75": percentile(sorted_views, 75),
                    "p90": percentile(sorted_views, 90),
                    "max": max(view_counts) if view_counts else 0
                },
                "like_distribution": {
                    "min": min(like_counts) if like_counts else 0,
                    "p10": percentile(sorted_likes, 10),
                    "p25": percentile(sorted_likes, 25),
                    "median": percentile(sorted_likes, 50),
                    "p75": percentile(sorted_likes, 75),
                    "p90": percentile(sorted_likes, 90),
                    "max": max(like_counts) if like_counts else 0
                },
                "comment_distribution": {
                    "min": min(comment_counts) if comment_counts else 0,
                    "p10": percentile(sorted_comments, 10),
                    "p25": percentile(sorted_comments, 25),
                    "median": percentile(sorted_comments, 50),
                    "p75": percentile(sorted_comments, 75),
                    "p90": percentile(sorted_comments, 90),
                    "max": max(comment_counts) if comment_counts else 0
                }
            }
        }
    
    def get_channel_performance_distribution(self, channel_id: str) -> Dict[str, Any]:
        """
        Get performance distribution analysis for a channel.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            Dictionary containing performance distribution
        """
        channel = self.channel_repository.get_channel(channel_id)
        if not channel:
            return {"status": "not_found", "error": "Channel not found"}
        
        videos = self.channel_repository.get_channel_videos(channel_id)
        if not videos:
            return {"status": "no_data", "error": "No videos found for channel"}
        
        # Calculate performance metrics for all videos
        video_performance = []
        for video in videos:
            views = video.view_count_observations[-1].value if video.view_count_observations else video.view_count
            likes = video.like_count_observations[-1].value if video.like_count_observations else video.like_count
            comments = video.comment_count_observations[-1].value if video.comment_count_observations else video.comment_count
            
            if views > 0:
                engagement_rate = (likes + comments) / views
            else:
                engagement_rate = 0
            
            video_performance.append({
                "video_id": video.video_id,
                "title": video.title,
                "published_at": video.published_at.isoformat(),
                "views": int(views),
                "likes": int(likes),
                "comments": int(comments),
                "engagement_rate": engagement_rate
            })
        
        # Sort by views to get top performers
        sorted_by_views = sorted(video_performance, key=lambda x: x["views"], reverse=True)
        sorted_by_engagement = sorted(video_performance, key=lambda x: x["engagement_rate"], reverse=True)
        
        n = len(sorted_by_views)
        
        return {
            "status": "success",
            "channel_id": channel_id,
            "performance_distribution": {
                "total_videos": n,
                "top_1_percent": [v for v in sorted_by_views[:max(1, n // 100)]],
                "top_5_percent": [v for v in sorted_by_views[:max(1, n // 20)]],
                "top_10_percent": [v for v in sorted_by_views[:max(1, n // 10)]],
                "median": sorted_by_views[n // 2] if n > 0 else None,
                "bottom_10_percent": [v for v in sorted_by_views[max(0, n - n // 10):]],
                "bottom_5_percent": [v for v in sorted_by_views[max(0, n - n // 20):]],
                "bottom_1_percent": [v for v in sorted_by_views[max(0, n - n // 100):]]
            },
            "highest_engagement": sorted_by_engagement[:5],
            "lowest_engagement": sorted_by_engagement[-5:] if len(sorted_by_engagement) >= 5 else sorted_by_engagement
        }