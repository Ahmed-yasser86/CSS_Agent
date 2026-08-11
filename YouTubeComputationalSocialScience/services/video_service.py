"""
Video analysis service for YouTube Computational Social Science research.

Orchestrates the video analysis workflow including data acquisition,
persistence, analytics, and research output generation.
"""


import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from ..domain.models import Video, Comment, CollectionRun, CollectionStatus, VideoAnalytics, CommentAnalytics
from ..domain.analytics import calculate_video_analytics, calculate_comment_analytics
from ..domain.sampling import sample_videos
from ..acquisition.youtube_scraper import YouTubeScraper
from ..acquisition.data_extractor import extract_video_data, extract_comment_data
from ..persistence.repository import VideoRepository, CommentRepository


class VideoService:
    """
    Service for YouTube video analysis workflows.
    
    Orchestrates the complete video analysis pipeline from data acquisition
    to research output generation.
    """
    
    def __init__(self, 
                 video_repository: VideoRepository,
                 comment_repository: CommentRepository):
        """
        Initialize the video service.
        
        Args:
            video_repository: Repository for video persistence
            comment_repository: Repository for comment persistence
        """
        self.video_repository = video_repository
        self.comment_repository = comment_repository
    
    def analyze_video(self, video_url: str, 
                     comment_limit: int = 1000,
                     collect_recommendations: bool = False,
                     collect_script: bool = True) -> Dict[str, Any]:
        """
        Analyze a YouTube video and return comprehensive research data.
        
        Args:
            video_url: URL of the YouTube video to analyze
            comment_limit: Maximum number of comments to collect
            collect_recommendations: Whether to collect video recommendations
            collect_script: Whether to collect video transcript/script
            
        Returns:
            Dictionary containing analysis results and metadata
        """
        # Create collection run
        collection_run_id = str(uuid.uuid4())
        scraper = YouTubeScraper(collection_run_id)
        scraper.create_collection_run("video", video_url.split('/')[-1], video_url)
        
        try:
            # Step 1: Extract video metadata
            video_info = scraper.extract_video_info(video_url)
            if not video_info:
                return {"status": "failed", "error": "Could not extract video info", "collection_run_id": collection_run_id}
            
            # Step 1b: Extract video script if requested
            script = ""
            if collect_script:
                script = scraper.extract_video_script(video_url)
            
            # Step 2: Normalize and save video
            video = extract_video_data(video_info, collection_run_id, video_info.get('channel_id', ''), script)
            self.video_repository.save_video(video)
            
            # Step 3: Extract and save comments
            self._collect_video_comments(scraper, video, comment_limit)
            
            # Step 4: Extract recommendations if requested
            if collect_recommendations:
                self._collect_video_recommendations(scraper, video)
            
            # Step 5: Calculate analytics
            video_analytics, comment_analytics = self._calculate_video_analytics(video)
            
            # Complete collection run
            scraper.complete_collection_run()
            
            return {
                "status": "success",
                "collection_run_id": collection_run_id,
                "video": video.model_dump(),
                "video_analytics": video_analytics.model_dump(),
                "comment_analytics": comment_analytics.model_dump(),
                "comments_collected": scraper.collection_run.comments_collected,
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
    
    def _collect_video_comments(self, scraper: YouTubeScraper, video: Video, limit: int):
        """Collect and save comments for a video."""
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
    
    def _collect_video_recommendations(self, scraper: YouTubeScraper, video: Video):
        """Collect and save recommendations for a video."""
        # This will be implemented in the recommendation service
        pass
    
    def _calculate_video_analytics(self, video: Video) -> Tuple[VideoAnalytics, CommentAnalytics]:
        """Calculate analytics for a video and its comments."""
        comments = self.comment_repository.get_video_comments(video.video_id)
        video_analytics = calculate_video_analytics(video, comments)
        comment_analytics = calculate_comment_analytics(video, comments)
        return video_analytics, comment_analytics
    
    def get_video_analytics(self, video_id: str) -> Dict[str, Any]:
        """
        Get pre-calculated analytics for a video.
        
        Args:
            video_id: ID of the video
            
        Returns:
            Dictionary containing video analytics
        """
        video = self.video_repository.get_video(video_id)
        if not video:
            return {"status": "not_found", "error": "Video not found"}
        
        comments = self.comment_repository.get_video_comments(video_id)
        video_analytics = calculate_video_analytics(video, comments)
        comment_analytics = calculate_comment_analytics(video, comments)
        
        return {
            "status": "success",
            "video_id": video_id,
            "video_analytics": video_analytics.model_dump(),
            "comment_analytics": comment_analytics.model_dump()
        }
    
    def get_video_comment_samples(self, video_id: str, sample_strategy: str = "top_likes", sample_size: int = 20) -> Dict[str, Any]:
        """
        Get comment samples from a video using different sampling strategies.
        
        Args:
            video_id: ID of the video
            sample_strategy: Sampling strategy (top_likes, bottom_likes, latest, oldest, random)
            sample_size: Number of comments to sample
            
        Returns:
            Dictionary containing sampled comments
        """
        video = self.video_repository.get_video(video_id)
        if not video:
            return {"status": "not_found", "error": "Video not found"}
        
        comments = self.comment_repository.get_video_comments(video_id)
        if not comments:
            return {"status": "no_data", "error": "No comments found for video"}
        
        # Apply sampling strategy
        if sample_strategy == "top_likes":
            sampled_comments = sorted(comments, key=lambda c: c.like_count, reverse=True)[:sample_size]
        elif sample_strategy == "bottom_likes":
            sampled_comments = sorted(comments, key=lambda c: c.like_count)[:sample_size]
        elif sample_strategy == "latest":
            sampled_comments = sorted(comments, key=lambda c: c.published_at, reverse=True)[:sample_size]
        elif sample_strategy == "oldest":
            sampled_comments = sorted(comments, key=lambda c: c.published_at)[:sample_size]
        elif sample_strategy == "random":
            import random
            sampled_comments = random.sample(comments, min(sample_size, len(comments)))
        else:
            return {"status": "invalid_strategy", "error": "Invalid sampling strategy"}
        
        return {
            "status": "success",
            "video_id": video_id,
            "sample_strategy": sample_strategy,
            "sample_size": len(sampled_comments),
            "comments": [c.model_dump() for c in sampled_comments]
        }
    
    def analyze_video_engagement_temporal(self, video_id: str) -> Dict[str, Any]:
        """
        Analyze the temporal pattern of video engagement.
        
        Args:
            video_id: ID of the video
            
        Returns:
            Dictionary containing temporal engagement analysis
        """
        video = self.video_repository.get_video(video_id)
        if not video:
            return {"status": "not_found", "error": "Video not found"}
        
        comments = self.comment_repository.get_video_comments(video_id)
        if not comments:
            return {"status": "no_data", "error": "No comments found for video"}
        
        # Calculate comment velocity (comments per hour for first 24 hours)
        video_published = video.published_at
        first_day_comments = [c for c in comments if c.published_at <= video_published + timedelta(days=1)]
        
        comment_velocity = {}
        for comment in first_day_comments:
            hours_after = int((comment.published_at - video_published).total_seconds() / 3600)
            comment_velocity[f"hour_{hours_after}"] = comment_velocity.get(f"hour_{hours_after}", 0) + 1
        
        # Calculate engagement decay (comments per day for first 30 days)
        engagement_decay = {}
        for comment in comments:
            if comment.published_at <= video_published + timedelta(days=30):
                days_after = (comment.published_at - video_published).days
                engagement_decay[f"day_{days_after}"] = engagement_decay.get(f"day_{days_after}", 0) + 1
        
        # Calculate comment timing distribution
        comment_timing = {
            "<1 hour": 0,
            "1-6 hours": 0,
            "6-24 hours": 0,
            "1-7 days": 0,
            "1-4 weeks": 0,
            ">1 month": 0
        }
        
        for comment in comments:
            time_diff = comment.published_at - video_published
            hours_diff = time_diff.total_seconds() / 3600
            
            if hours_diff < 1:
                comment_timing["<1 hour"] += 1
            elif hours_diff < 6:
                comment_timing["1-6 hours"] += 1
            elif hours_diff < 24:
                comment_timing["6-24 hours"] += 1
            elif hours_diff < 168:  # 1 week
                comment_timing["1-7 days"] += 1
            elif hours_diff < 720:  # 1 month
                comment_timing["1-4 weeks"] += 1
            else:
                comment_timing[">1 month"] += 1
        
        return {
            "status": "success",
            "video_id": video_id,
            "comment_velocity": comment_velocity,
            "engagement_decay": engagement_decay,
            "comment_timing_distribution": comment_timing,
            "total_comments": len(comments)
        }
    
    def compare_videos(self, video_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple videos across various metrics.
        
        Args:
            video_ids: List of video IDs to compare
            
        Returns:
            Dictionary containing comparative analytics
        """
        comparison_data = {}
        
        for video_id in video_ids:
            video = self.video_repository.get_video(video_id)
            if not video:
                continue
            
            comments = self.comment_repository.get_video_comments(video_id)
            video_analytics = calculate_video_analytics(video, comments)
            
            comparison_data[video_id] = {
                "video": video.model_dump(),
                "analytics": video_analytics.model_dump(),
                "comment_count": len(comments)
            }
        
        return {
            "status": "success",
            "comparison": comparison_data,
            "videos_compared": len(comparison_data)
        }

    def get_video_engagement_analysis(self, video_id: str) -> Dict[str, Any]:
        """
        Get comprehensive engagement analysis for a video.
        
        Args:
            video_id: ID of the video
            
        Returns:
            Dictionary containing engagement analysis
        """
        video = self.video_repository.get_video(video_id)
        if not video:
            return {"status": "not_found", "error": "Video not found"}
        
        comments = self.comment_repository.get_video_comments(video_id)
        video_analytics = calculate_video_analytics(video, comments)
        
        # Calculate additional engagement metrics
        current_views = video.view_count_observations[-1].value if video.view_count_observations else video.view_count
        current_likes = video.like_count_observations[-1].value if video.like_count_observations else video.like_count
        current_comments = video.comment_count_observations[-1].value if video.comment_count_observations else video.comment_count
        
        # Calculate percentiles and distributions
        engagement_metrics = {
            "video_id": video_id,
            "collection_run_id": video.collection_run_id,
            "raw_metrics": {
                "views": int(current_views),
                "likes": int(current_likes),
                "comments": int(current_comments)
            },
            "rates": {
                "engagement_rate": video_analytics.engagement_rate,
                "like_rate": video_analytics.like_rate,
                "comment_rate": video_analytics.comment_rate
            },
            "comment_analytics": {
                "total_comments": len(comments),
                "unique_commenters": video_analytics.unique_commenters,
                "repeat_commenters": video_analytics.repeat_commenters,
                "avg_likes_per_comment": video_analytics.avg_likes_per_comment,
                "avg_replies_per_thread": video_analytics.avg_replies_per_thread,
                "thread_initiation_rate": video_analytics.thread_initiation_rate
            },
            "distribution": {
                "view_count": current_views,
                "like_count": current_likes,
                "comment_count": current_comments
            }
        }
        
        return {
            "status": "success",
            "engagement_analysis": engagement_metrics
        }
    
    def get_video_comment_analysis(self, video_id: str) -> Dict[str, Any]:
        """
        Get comprehensive comment analysis for a video.
        
        Args:
            video_id: ID of the video
            
        Returns:
            Dictionary containing comment analysis
        """
        video = self.video_repository.get_video(video_id)
        if not video:
            return {"status": "not_found", "error": "Video not found"}
        
        comments = self.comment_repository.get_video_comments(video_id)
        comment_analytics = calculate_comment_analytics(video, comments)
        
        return {
            "status": "success",
            "video_id": video_id,
            "comment_analysis": comment_analytics.model_dump(),
            "comments_analyzed": len(comments)
        }
    
    def get_video_comment_distribution(self, video_id: str) -> Dict[str, Any]:
        """
        Get comment distribution analysis for a video.
        
        Args:
            video_id: ID of the video
            
        Returns:
            Dictionary containing comment distribution
        """
        video = self.video_repository.get_video(video_id)
        if not video:
            return {"status": "not_found", "error": "Video not found"}
        
        comments = self.comment_repository.get_video_comments(video_id)
        
        if not comments:
            return {"status": "no_data", "error": "No comments found"}
        
        # Calculate distributions
        like_counts = [c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in comments]
        reply_counts = [c.reply_count_observations[-1].value if c.reply_count_observations else c.reply_count for c in comments]
        lengths = [len(c.text) for c in comments]
        
        return {
            "status": "success",
            "video_id": video_id,
            "distribution": {
                "likes": _calculate_percentiles(like_counts),
                "replies": _calculate_percentiles(reply_counts),
                "length": _calculate_length_distribution(lengths)
            },
            "total_comments": len(comments)
        }
    
    def get_video_comment_concentration(self, video_id: str) -> Dict[str, Any]:
        """
        Get comment concentration analysis for a video.
        
        Args:
            video_id: ID of the video
            
        Returns:
            Dictionary containing comment concentration metrics
        """
        video = self.video_repository.get_video(video_id)
        if not video:
            return {"status": "not_found", "error": "Video not found"}
        
        comments = self.comment_repository.get_video_comments(video_id)
        
        if not comments:
            return {"status": "no_data", "error": "No comments found"}
        
        # Get current like counts
        like_counts = [c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in comments]
        total_likes = sum(like_counts)
        
        if total_likes == 0:
            return {
                "status": "success",
                "video_id": video_id,
                "concentration": {
                    "gini_coefficient": 0.0,
                    "top_1_percent_share": 0.0,
                    "top_5_percent_share": 0.0,
                    "top_10_percent_share": 0.0
                },
                "total_comments": len(comments)
            }
        
        # Sort comments by likes (descending)
        sorted_comments = sorted(comments, key=lambda c: c.like_count_observations[-1].value if c.like_count_observations else c.like_count, reverse=True)
        
        # Calculate concentration metrics
        top_1_percent = max(1, len(sorted_comments) // 100)
        top_5_percent = max(1, len(sorted_comments) // 20)
        top_10_percent = max(1, len(sorted_comments) // 10)
        
        top_1_likes = sum(c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in sorted_comments[:top_1_percent])
        top_5_likes = sum(c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in sorted_comments[:top_5_percent])
        top_10_likes = sum(c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in sorted_comments[:top_10_percent])
        
        return {
            "status": "success",
            "video_id": video_id,
            "concentration": {
                "gini_coefficient": _calculate_gini_coefficient(like_counts),
                "top_1_percent_share": top_1_likes / total_likes,
                "top_5_percent_share": top_5_likes / total_likes,
                "top_10_percent_share": top_10_likes / total_likes
            },
            "total_comments": len(comments)
        }


def _calculate_percentiles(values):
    """Calculate percentiles for a list of values."""
    if not values:
        return {}
    sorted_values = sorted(values)
    n = len(sorted_values)
    return {
        "min": sorted_values[0],
        "p10": sorted_values[max(0, int(n * 0.10) - 1)],
        "p25": sorted_values[max(0, int(n * 0.25) - 1)],
        "median": sorted_values[max(0, int(n * 0.50) - 1)],
        "p75": sorted_values[max(0, int(n * 0.75) - 1)],
        "p90": sorted_values[max(0, int(n * 0.90) - 1)],
        "p95": sorted_values[max(0, int(n * 0.95) - 1)],
        "p99": sorted_values[max(0, int(n * 0.99) - 1)],
        "max": sorted_values[-1]
    }


def _calculate_length_distribution(lengths):
    """Calculate distribution of lengths into bins."""
    if not lengths:
        return {}
    bins = {"0-50": 0, "51-100": 0, "101-250": 0, "251-500": 0, "500+": 0}
    for length in lengths:
        if length <= 50:
            bins["0-50"] += 1
        elif length <= 100:
            bins["51-100"] += 1
        elif length <= 250:
            bins["101-250"] += 1
        elif length <= 500:
            bins["251-500"] += 1
        else:
            bins["500+"] += 1
    total = sum(bins.values())
    if total > 0:
        for key in bins:
            bins[key] = bins[key] / total
    return bins


def _calculate_gini_coefficient(values):
    """Calculate Gini coefficient for a list of values."""
    if not values or sum(values) == 0:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    cumulative_sum = sum(sorted_values[i] * (n - i) for i in range(n))
    total_sum = sum(sorted_values)
    if total_sum == 0:
        return 0.0
    return (n + 1 - 2 * cumulative_sum / total_sum) / n