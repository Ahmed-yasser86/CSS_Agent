"""
Analytics functions for YouTube Computational Social Science research.

Provides research-grade analytics that preserve provenance, handle missing data,
and support longitudinal analysis.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import math
from .models import Channel, Video, Comment, Observation, ChannelAnalytics, VideoAnalytics, CommentAnalytics


def calculate_channel_analytics(channel: Channel, videos: List[Video]) -> ChannelAnalytics:
    """
    Calculate comprehensive analytics for a YouTube channel.
    
    Args:
        channel: The channel to analyze
        videos: List of videos belonging to the channel
        
    Returns:
        ChannelAnalytics object with calculated metrics
    """
    if not videos:
        analytics = ChannelAnalytics(channel_id=channel.channel_id, collection_run_id=channel.collection_run_id)
        analytics.subscriber_count = channel.subscriber_count
        return analytics
    
    analytics = ChannelAnalytics(channel_id=channel.channel_id, collection_run_id=channel.collection_run_id)
    
    # Set subscriber count from channel
    analytics.subscriber_count = channel.subscriber_count
    
    # Calculate temporal metrics
    _calculate_channel_temporal_metrics(analytics, videos)
    
    # Calculate engagement metrics
    _calculate_channel_engagement_metrics(analytics, videos)
    
    # Calculate distribution metrics
    _calculate_channel_distribution_metrics(analytics, videos)
    
    # Calculate growth metrics
    _calculate_channel_growth_metrics(analytics, channel)
    
    # Identify top performers
    _identify_top_performers(analytics, videos)
    
    return analytics


def _calculate_channel_temporal_metrics(analytics: ChannelAnalytics, videos: List[Video]):
    """Calculate temporal metrics for channel analytics."""
    if not videos:
        return
    
    # Sort videos by publication date
    sorted_videos = sorted(videos, key=lambda v: v.published_at)
    
    # Calculate upload frequency (videos per week)
    if len(sorted_videos) >= 2:
        time_span = (sorted_videos[-1].published_at - sorted_videos[0].published_at).days
        if time_span > 0:
            analytics.upload_frequency = len(sorted_videos) / (time_span / 7)
    
    # Calculate upload consistency (standard deviation of time between uploads)
    if len(sorted_videos) >= 3:
        intervals = []
        for i in range(1, len(sorted_videos)):
            interval = (sorted_videos[i].published_at - sorted_videos[i-1].published_at).days
            intervals.append(interval)
        
        if intervals:
            analytics.upload_consistency = statistics.stdev(intervals)
    
    # Calculate uploads by period (year-month)
    for video in sorted_videos:
        period = video.published_at.strftime("%Y-%m")
        analytics.uploads_by_period[period] = analytics.uploads_by_period.get(period, 0) + 1
    
    # Calculate views by period
    for video in sorted_videos:
        period = video.published_at.strftime("%Y-%m")
        current_views = video.view_count_observations[-1].value if video.view_count_observations else video.view_count
        analytics.views_by_period[period] = analytics.views_by_period.get(period, 0) + current_views


def _calculate_channel_engagement_metrics(analytics: ChannelAnalytics, videos: List[Video]):
    """Calculate engagement metrics for channel analytics."""
    if not videos:
        return
    
    total_views = sum(v.view_count_observations[-1].value if v.view_count_observations else v.view_count for v in videos)
    total_likes = sum(v.like_count_observations[-1].value if v.like_count_observations else v.like_count for v in videos)
    total_comments = sum(v.comment_count_observations[-1].value if v.comment_count_observations else v.comment_count for v in videos)
    
    # Set summary statistics
    analytics.total_videos = len(videos)
    analytics.total_views = int(total_views)
    analytics.total_likes = int(total_likes)
    analytics.total_comments = int(total_comments)
    
    # Calculate overall engagement rate
    if total_views > 0:
        analytics.engagement_rate = (total_comments + total_likes) / total_views
    
    analytics.avg_views_per_video = total_views / len(videos)
    analytics.avg_likes_per_video = total_likes / len(videos)
    analytics.avg_comments_per_video = total_comments / len(videos)


def _calculate_channel_distribution_metrics(analytics: ChannelAnalytics, videos: List[Video]):
    """Calculate distribution metrics for channel analytics."""
    if not videos:
        return
    
    # Get current metrics for each video
    view_counts = [v.view_count_observations[-1].value if v.view_count_observations else v.view_count for v in videos]
    like_counts = [v.like_count_observations[-1].value if v.like_count_observations else v.like_count for v in videos]
    comment_counts = [v.comment_count_observations[-1].value if v.comment_count_observations else v.comment_count for v in videos]
    
    # Calculate percentiles for views
    analytics.view_distribution = _calculate_percentiles(view_counts)
    
    # Calculate percentiles for likes
    analytics.like_distribution = _calculate_percentiles(like_counts)
    
    # Calculate percentiles for comments
    analytics.comment_distribution = _calculate_percentiles(comment_counts)


def _calculate_channel_growth_metrics(analytics: ChannelAnalytics, channel: Channel):
    """Calculate growth metrics for channel analytics."""
    if len(channel.subscriber_count_observations) >= 2:
        # Calculate growth rate between first and last observation
        first = channel.subscriber_count_observations[0]
        last = channel.subscriber_count_observations[-1]
        time_span = (last.observed_at - first.observed_at).days
        
        if time_span > 0:
            analytics.subscriber_growth_rate = (last.value - first.value) / time_span
    
    if len(channel.view_count_observations) >= 2:
        first = channel.view_count_observations[0]
        last = channel.view_count_observations[-1]
        time_span = (last.observed_at - first.observed_at).days
        
        if time_span > 0:
            analytics.view_growth_rate = (last.value - first.value) / time_span


def _identify_top_performers(analytics: ChannelAnalytics, videos: List[Video]):
    """Identify top performing videos for channel analytics."""
    if not videos:
        return
    
    # Sort videos by different metrics
    sorted_by_views = sorted(videos, key=lambda v: v.view_count_observations[-1].value if v.view_count_observations else v.view_count, reverse=True)
    sorted_by_likes = sorted(videos, key=lambda v: v.like_count_observations[-1].value if v.like_count_observations else v.like_count, reverse=True)
    sorted_by_comments = sorted(videos, key=lambda v: v.comment_count_observations[-1].value if v.comment_count_observations else v.comment_count, reverse=True)
    
    # Take top 5 for each category
    analytics.top_videos_by_views = sorted_by_views[:5]
    analytics.top_videos_by_likes = sorted_by_likes[:5]
    analytics.top_videos_by_comments = sorted_by_comments[:5]


def calculate_video_analytics(video: Video, comments: List[Comment]) -> VideoAnalytics:
    """
    Calculate comprehensive analytics for a YouTube video.
    
    Args:
        video: The video to analyze
        comments: List of comments belonging to the video
        
    Returns:
        VideoAnalytics object with calculated metrics
    """
    analytics = VideoAnalytics(video_id=video.video_id, collection_run_id=video.collection_run_id)
    
    # Calculate engagement metrics
    _calculate_video_engagement_metrics(analytics, video)
    
    # Calculate temporal metrics
    _calculate_video_temporal_metrics(analytics, video, comments)
    
    # Calculate distribution metrics
    _calculate_video_distribution_metrics(analytics, comments)
    
    # Calculate participation metrics
    _calculate_video_participation_metrics(analytics, comments)
    
    # Calculate thread metrics
    _calculate_video_thread_metrics(analytics, comments)
    
    # Calculate engagement concentration
    _calculate_video_engagement_concentration(analytics, comments)
    
    return analytics


def _calculate_video_engagement_metrics(analytics: VideoAnalytics, video: Video):
    """Calculate engagement metrics for video analytics."""
    current_views = video.view_count_observations[-1].value if video.view_count_observations else video.view_count
    current_likes = video.like_count_observations[-1].value if video.like_count_observations else video.like_count
    current_comments = video.comment_count_observations[-1].value if video.comment_count_observations else video.comment_count
    
    # Set current video stats
    analytics.view_count = int(current_views)
    analytics.like_count = int(current_likes)
    analytics.comment_count = int(current_comments)
    
    if current_views > 0:
        analytics.engagement_rate = (current_comments + current_likes) / current_views
        analytics.like_rate = current_likes / current_views
        analytics.comment_rate = current_comments / current_views


def _calculate_video_temporal_metrics(analytics: VideoAnalytics, video: Video, comments: List[Comment]):
    """Calculate temporal metrics for video analytics."""
    if not comments:
        return
    
    # Calculate comment velocity (comments per hour for first 24 hours)
    video_published = video.published_at
    first_day_comments = [c for c in comments if c.published_at <= video_published + timedelta(days=1)]
    
    if first_day_comments:
        # Group by hour
        for comment in first_day_comments:
            hours_after = int((comment.published_at - video_published).total_seconds() / 3600)
            analytics.comment_velocity[f"hour_{hours_after}"] = analytics.comment_velocity.get(f"hour_{hours_after}", 0) + 1
    
    # Calculate engagement decay (comments per day for first 30 days)
    if comments:
        # Group by day
        for comment in comments:
            if comment.published_at <= video_published + timedelta(days=30):
                days_after = (comment.published_at - video_published).days
                analytics.engagement_decay[f"day_{days_after}"] = analytics.engagement_decay.get(f"day_{days_after}", 0) + 1


def _calculate_video_distribution_metrics(analytics: VideoAnalytics, comments: List[Comment]):
    """Calculate distribution metrics for video analytics."""
    if not comments:
        return
    
    # Comment like distribution
    like_counts = [c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in comments]
    analytics.comment_like_distribution = _calculate_percentiles(like_counts)
    
    # Comment length distribution
    lengths = [len(c.text) for c in comments]
    analytics.comment_length_distribution = _calculate_length_distribution(lengths)


def _calculate_video_participation_metrics(analytics: VideoAnalytics, comments: List[Comment]):
    """Calculate participation metrics for video analytics."""
    if not comments:
        return
    
    # Count unique commenters (if author_id is available)
    if comments[0].author_id:
        unique_authors = set(c.author_id for c in comments if c.author_id)
        analytics.unique_commenters = len(unique_authors)
        
        # Calculate repeat commenters
        author_counts = {}
        for comment in comments:
            if comment.author_id:
                author_counts[comment.author_id] = author_counts.get(comment.author_id, 0) + 1
        
        analytics.repeat_commenters = sum(1 for count in author_counts.values() if count > 1)


def _calculate_video_thread_metrics(analytics: VideoAnalytics, comments: List[Comment]):
    """Calculate thread metrics for video analytics."""
    if not comments:
        return
    
    # Identify root comments (not replies)
    root_comments = [c for c in comments if not c.is_reply]
    reply_comments = [c for c in comments if c.is_reply]
    
    if root_comments:
        # Calculate thread initiation rate
        threads_with_replies = sum(1 for c in root_comments if c.reply_count > 0)
        analytics.thread_initiation_rate = threads_with_replies / len(root_comments)
        
        # Calculate average replies per thread
        total_replies = sum(c.reply_count for c in root_comments)
        analytics.avg_replies_per_thread = total_replies / len(root_comments)
    
    # Calculate maximum thread depth
    if reply_comments:
        # Build reply tree
        reply_map = {c.comment_id: c for c in reply_comments}
        max_depth = 0
        
        for comment in root_comments:
            depth = _calculate_thread_depth(comment, reply_map)
            if depth > max_depth:
                max_depth = depth
        
        analytics.max_thread_depth = max_depth


def _calculate_thread_depth(comment: Comment, reply_map: Dict[str, Comment], current_depth: int = 1) -> int:
    """Recursively calculate thread depth."""
    max_depth = current_depth
    
    # Find replies to this comment
    for reply in reply_map.values():
        if reply.parent_id == comment.comment_id:
            depth = _calculate_thread_depth(reply, reply_map, current_depth + 1)
            if depth > max_depth:
                max_depth = depth
    
    return max_depth


def _calculate_video_engagement_concentration(analytics: VideoAnalytics, comments: List[Comment]):
    """Calculate engagement concentration metrics for video analytics."""
    if not comments:
        return
    
    # Get current like counts
    like_counts = [c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in comments]
    total_likes = sum(like_counts)
    
    if total_likes > 0:
        # Sort comments by likes (descending)
        sorted_comments = sorted(comments, key=lambda c: c.like_count_observations[-1].value if c.like_count_observations else c.like_count, reverse=True)
        
        # Calculate top 1% share
        top_1_percent = max(1, len(sorted_comments) // 100)
        top_1_likes = sum(c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in sorted_comments[:top_1_percent])
        analytics.top_1_percent_share = top_1_likes / total_likes
        
        # Calculate top 5% share
        top_5_percent = max(1, len(sorted_comments) // 20)
        top_5_likes = sum(c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in sorted_comments[:top_5_percent])
        analytics.top_5_percent_share = top_5_likes / total_likes
        
        # Calculate top 10% share
        top_10_percent = max(1, len(sorted_comments) // 10)
        top_10_likes = sum(c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in sorted_comments[:top_10_percent])
        analytics.top_10_percent_share = top_10_likes / total_likes


def calculate_comment_analytics(video: Video, comments: List[Comment]) -> CommentAnalytics:
    """
    Calculate comprehensive analytics for YouTube comments.
    
    Args:
        video: The video the comments belong to
        comments: List of comments to analyze
        
    Returns:
        CommentAnalytics object with calculated metrics
    """
    analytics = CommentAnalytics(video_id=video.video_id, collection_run_id=video.collection_run_id)
    
    if not comments:
        return analytics
    
    # Calculate temporal metrics
    _calculate_comment_temporal_metrics(analytics, video, comments)
    
    # Calculate engagement metrics
    _calculate_comment_engagement_metrics(analytics, comments)
    
    # Calculate distribution metrics
    _calculate_comment_distribution_metrics(analytics, comments)
    
    # Calculate participation metrics
    _calculate_comment_participation_metrics(analytics, comments)
    
    # Calculate thread metrics
    _calculate_comment_thread_metrics(analytics, comments)
    
    # Calculate engagement concentration
    _calculate_comment_engagement_concentration(analytics, comments)
    
    return analytics


def _calculate_comment_temporal_metrics(analytics: CommentAnalytics, video: Video, comments: List[Comment]):
    """Calculate temporal metrics for comment analytics."""
    video_published = video.published_at
    
    # Calculate comment timing relative to video publication
    for comment in comments:
        time_diff = comment.published_at - video_published
        hours_diff = time_diff.total_seconds() / 3600
        
        if hours_diff < 1:
            bin_key = "<1 hour"
        elif hours_diff < 6:
            bin_key = "1-6 hours"
        elif hours_diff < 24:
            bin_key = "6-24 hours"
        elif hours_diff < 168:  # 1 week
            bin_key = "1-7 days"
        elif hours_diff < 720:  # 1 month
            bin_key = "1-4 weeks"
        else:
            bin_key = ">1 month"
        
        analytics.comment_timing[bin_key] = analytics.comment_timing.get(bin_key, 0) + 1
    
    # Calculate comment velocity (comments per hour for first 24 hours)
    first_day_comments = [c for c in comments if c.published_at <= video_published + timedelta(days=1)]
    
    if first_day_comments:
        for comment in first_day_comments:
            hours_after = int((comment.published_at - video_published).total_seconds() / 3600)
            analytics.comment_velocity[f"hour_{hours_after}"] = analytics.comment_velocity.get(f"hour_{hours_after}", 0) + 1


def _calculate_comment_engagement_metrics(analytics: CommentAnalytics, comments: List[Comment]):
    """Calculate engagement metrics for comment analytics."""
    if not comments:
        return
    
    # Get current metrics
    like_counts = [c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in comments]
    reply_counts = [c.reply_count_observations[-1].value if c.reply_count_observations else c.reply_count for c in comments]
    
    analytics.avg_likes_per_comment = sum(like_counts) / len(like_counts)
    analytics.avg_replies_per_comment = sum(reply_counts) / len(reply_counts)


def _calculate_comment_distribution_metrics(analytics: CommentAnalytics, comments: List[Comment]):
    """Calculate distribution metrics for comment analytics."""
    if not comments:
        return
    
    # Like distribution
    like_counts = [c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in comments]
    analytics.like_distribution = _calculate_percentiles(like_counts)
    
    # Reply distribution
    reply_counts = [c.reply_count_observations[-1].value if c.reply_count_observations else c.reply_count for c in comments]
    analytics.reply_distribution = _calculate_percentiles(reply_counts)
    
    # Length distribution
    lengths = [len(c.text) for c in comments]
    analytics.length_distribution = _calculate_length_distribution(lengths)


def _calculate_comment_participation_metrics(analytics: CommentAnalytics, comments: List[Comment]):
    """Calculate participation metrics for comment analytics."""
    if not comments or not comments[0].author_id:
        return
    
    # Count unique commenters
    unique_authors = set(c.author_id for c in comments if c.author_id)
    analytics.unique_commenters = len(unique_authors)
    
    # Calculate comments per commenter
    author_counts = {}
    for comment in comments:
        if comment.author_id:
            author_counts[comment.author_id] = author_counts.get(comment.author_id, 0) + 1
    
    # Create distribution
    for count in author_counts.values():
        bin_key = _get_bin_key(count, [1, 2, 5, 10, 20, 50])
        analytics.comments_per_commenter[bin_key] = analytics.comments_per_commenter.get(bin_key, 0) + 1


def _calculate_comment_thread_metrics(analytics: CommentAnalytics, comments: List[Comment]):
    """Calculate thread metrics for comment analytics."""
    if not comments:
        return
    
    # Identify root comments and replies
    root_comments = [c for c in comments if not c.is_reply]
    reply_comments = [c for c in comments if c.is_reply]
    
    if root_comments:
        # Calculate thread initiation rate
        threads_with_replies = sum(1 for c in root_comments if c.reply_count > 0)
        analytics.thread_initiation_rate = threads_with_replies / len(root_comments)
    
    # Calculate thread depth distribution
    if reply_comments:
        reply_map = {c.comment_id: c for c in reply_comments}
        depth_counts = {}
        
        for comment in root_comments:
            depth = _calculate_thread_depth(comment, reply_map)
            depth_key = f"depth_{depth}"
            depth_counts[depth_key] = depth_counts.get(depth_key, 0) + 1
        
        analytics.thread_depth_distribution = depth_counts


def _calculate_comment_engagement_concentration(analytics: CommentAnalytics, comments: List[Comment]):
    """Calculate engagement concentration metrics for comment analytics."""
    if not comments:
        return
    
    # Get current like counts
    like_counts = [c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in comments]
    total_likes = sum(like_counts)
    
    if total_likes > 0:
        # Calculate Gini coefficient
        analytics.gini_coefficient = _calculate_gini_coefficient(like_counts)
        
        # Sort comments by likes (descending)
        sorted_comments = sorted(comments, key=lambda c: c.like_count_observations[-1].value if c.like_count_observations else c.like_count, reverse=True)
        
        # Calculate top 1% share
        top_1_percent = max(1, len(sorted_comments) // 100)
        top_1_likes = sum(c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in sorted_comments[:top_1_percent])
        analytics.top_1_percent_share = top_1_likes / total_likes
        
        # Calculate top 5% share
        top_5_percent = max(1, len(sorted_comments) // 20)
        top_5_likes = sum(c.like_count_observations[-1].value if c.like_count_observations else c.like_count for c in sorted_comments[:top_5_percent])
        analytics.top_5_percent_share = top_5_likes / total_likes


def calculate_engagement_metrics(entity: Video | Comment) -> Dict[str, float]:
    """
    Calculate basic engagement metrics for a video or comment.
    
    Args:
        entity: Video or Comment object
        
    Returns:
        Dictionary of engagement metrics
    """
    metrics = {}
    
    if isinstance(entity, Video):
        current_views = entity.view_count_observations[-1].value if entity.view_count_observations else entity.view_count
        current_likes = entity.like_count_observations[-1].value if entity.like_count_observations else entity.like_count
        current_comments = entity.comment_count_observations[-1].value if entity.comment_count_observations else entity.comment_count
        
        if current_views > 0:
            metrics["engagement_rate"] = (current_comments + current_likes) / current_views
            metrics["like_rate"] = current_likes / current_views
            metrics["comment_rate"] = current_comments / current_views
    
    elif isinstance(entity, Comment):
        current_likes = entity.like_count_observations[-1].value if entity.like_count_observations else entity.like_count
        current_replies = entity.reply_count_observations[-1].value if entity.reply_count_observations else entity.reply_count
        
        metrics["like_count"] = current_likes
        metrics["reply_count"] = current_replies
        metrics["engagement_score"] = current_likes + current_replies
    
    return metrics


def calculate_temporal_metrics(entities: List[Video | Comment], time_field: str = "published_at") -> Dict[str, Dict[str, float]]:
    """
    Calculate temporal metrics for a list of entities.
    
    Args:
        entities: List of Video or Comment objects
        time_field: Field name to use for temporal analysis
        
    Returns:
        Dictionary of temporal metrics by time period
    """
    if not entities:
        return {}
    
    metrics = {
        "hourly": {},
        "daily": {},
        "weekly": {},
        "monthly": {}
    }
    
    # Find the earliest and latest dates
    dates = [getattr(e, time_field) for e in entities]
    min_date = min(dates)
    max_date = max(dates)
    
    # Group entities by different time periods
    for entity in entities:
        date = getattr(entity, time_field)
        
        # Hourly (for first 24 hours)
        if (date - min_date).days < 1:
            hour_key = f"hour_{(date - min_date).total_seconds() // 3600}"
            metrics["hourly"][hour_key] = metrics["hourly"].get(hour_key, 0) + 1
        
        # Daily
        day_key = date.strftime("%Y-%m-%d")
        metrics["daily"][day_key] = metrics["daily"].get(day_key, 0) + 1
        
        # Weekly
        week_key = date.strftime("%Y-%U")
        metrics["weekly"][week_key] = metrics["weekly"].get(week_key, 0) + 1
        
        # Monthly
        month_key = date.strftime("%Y-%m")
        metrics["monthly"][month_key] = metrics["monthly"].get(month_key, 0) + 1
    
    return metrics


def calculate_distribution_metrics(values: List[float]) -> Dict[str, float]:
    """
    Calculate distribution metrics for a list of values.
    
    Args:
        values: List of numerical values
        
    Returns:
        Dictionary of distribution metrics
    """
    if not values:
        return {}
    
    return _calculate_percentiles(values)


def _calculate_percentiles(values: List[float]) -> Dict[str, float]:
    """Calculate percentiles for a list of values."""
    if not values:
        return {}
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    return {
        "min": sorted_values[0],
        "p10": _percentile(sorted_values, 10),
        "p25": _percentile(sorted_values, 25),
        "median": _percentile(sorted_values, 50),
        "p75": _percentile(sorted_values, 75),
        "p90": _percentile(sorted_values, 90),
        "p95": _percentile(sorted_values, 95),
        "p99": _percentile(sorted_values, 99),
        "max": sorted_values[-1]
    }


def _calculate_length_distribution(lengths: List[int]) -> Dict[str, float]:
    """Calculate distribution of lengths into bins."""
    if not lengths:
        return {}
    
    bins = {
        "0-50": 0,
        "51-100": 0,
        "101-250": 0,
        "251-500": 0,
        "500+": 0
    }
    
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
    
    # Convert counts to percentages
    total = sum(bins.values())
    if total > 0:
        for key in bins:
            bins[key] = bins[key] / total
    
    return bins


def _calculate_gini_coefficient(values: List[float]) -> float:
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


def _percentile(sorted_values: List[float], percentile: float) -> float:
    """Calculate percentile from sorted values."""
    n = len(sorted_values)
    if n == 0:
        return 0.0
    
    k = (n - 1) * percentile / 100
    f = math.floor(k)
    c = math.ceil(k)
    
    if f == c:
        return sorted_values[int(k)]
    
    d0 = sorted_values[int(f)] * (c - k)
    d1 = sorted_values[int(c)] * (k - f)
    
    return d0 + d1


def _get_bin_key(value: int, bins: List[int]) -> str:
    """Get the appropriate bin key for a value."""
    for i, bin_threshold in enumerate(bins):
        if value <= bin_threshold:
            if i == 0:
                return f"1-{bin_threshold}"
            else:
                return f"{bins[i-1]+1}-{bin_threshold}"
    
    return f">{bins[-1]}"