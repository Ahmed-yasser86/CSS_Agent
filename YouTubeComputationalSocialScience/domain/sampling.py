"""
Sampling strategies for YouTube Computational Social Science research.

Provides research-grade sampling methods that support reproducible research
and enable comparative analysis across different time periods and strata.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import random
from .models import Video


def sample_videos(videos: List[Video], strategy: str = "random", **kwargs) -> List[Video]:
    """
    Sample videos using the specified strategy.
    
    Args:
        videos: List of videos to sample from
        strategy: Sampling strategy (random, stratified, top_performers, bottom_performers)
        kwargs: Additional strategy-specific parameters
        
    Returns:
        List of sampled videos
    """
    if not videos:
        return []
    
    if strategy == "random":
        return random_sample(videos, **kwargs)
    elif strategy == "stratified":
        return stratified_sample(videos, **kwargs)
    elif strategy == "top_performers":
        return top_performers_sample(videos, **kwargs)
    elif strategy == "bottom_performers":
        return bottom_performers_sample(videos, **kwargs)
    elif strategy == "temporal":
        return temporal_sample(videos, **kwargs)
    else:
        raise ValueError(f"Unknown sampling strategy: {strategy}")


def random_sample(videos: List[Video], sample_size: int = 10, seed: Optional[int] = None) -> List[Video]:
    """
    Randomly sample videos from the collection.
    
    Args:
        videos: List of videos to sample from
        sample_size: Number of videos to sample
        seed: Random seed for reproducibility
        
    Returns:
        List of randomly sampled videos
    """
    if seed is not None:
        random.seed(seed)
    
    if sample_size >= len(videos):
        return videos.copy()
    
    return random.sample(videos, sample_size)


def stratified_sample(videos: List[Video], strata: str = "year", sample_per_stratum: int = 10, metric: str = "views") -> List[Video]:
    """
    Stratified sampling of videos by time period.
    
    Args:
        videos: List of videos to sample from
        strata: Stratification criterion (year, month, quarter)
        sample_per_stratum: Number of videos to sample per stratum
        metric: Metric to use for sorting within strata (views, likes, comments)
        
    Returns:
        List of videos sampled using stratified strategy
    """
    if not videos:
        return []
    
    # Group videos by stratum
    strata_groups = _group_by_stratum(videos, strata)
    
    sampled_videos = []
    
    for stratum, stratum_videos in strata_groups.items():
        if len(stratum_videos) <= sample_per_stratum:
            sampled_videos.extend(stratum_videos)
        else:
            # Sort by metric and take top sample_per_stratum
            sorted_videos = _sort_videos_by_metric(stratum_videos, metric)
            sampled_videos.extend(sorted_videos[:sample_per_stratum])
    
    return sampled_videos


def top_performers_sample(videos: List[Video], sample_size: int = 10, metric: str = "views") -> List[Video]:
    """
    Sample top performing videos by the specified metric.
    
    Args:
        videos: List of videos to sample from
        sample_size: Number of videos to sample
        metric: Metric to use for ranking (views, likes, comments, engagement_rate)
        
    Returns:
        List of top performing videos
    """
    if not videos:
        return []
    
    sorted_videos = _sort_videos_by_metric(videos, metric)
    return sorted_videos[:sample_size]


def bottom_performers_sample(videos: List[Video], sample_size: int = 10, metric: str = "views") -> List[Video]:
    """
    Sample bottom performing videos by the specified metric.
    
    Args:
        videos: List of videos to sample from
        sample_size: Number of videos to sample
        metric: Metric to use for ranking (views, likes, comments, engagement_rate)
        
    Returns:
        List of bottom performing videos
    """
    if not videos:
        return []
    
    sorted_videos = _sort_videos_by_metric(videos, metric)
    return sorted_videos[-sample_size:]


def temporal_sample(videos: List[Video], time_periods: List[Tuple[datetime, datetime]], sample_per_period: int = 10, metric: str = "views") -> List[Video]:
    """
    Sample videos from specific time periods.
    
    Args:
        videos: List of videos to sample from
        time_periods: List of (start_date, end_date) tuples
        sample_per_period: Number of videos to sample per period
        metric: Metric to use for ranking within periods
        
    Returns:
        List of videos sampled from specified time periods
    """
    if not videos or not time_periods:
        return []
    
    sampled_videos = []
    
    for start_date, end_date in time_periods:
        # Filter videos in this time period
        period_videos = [v for v in videos if start_date <= v.published_at <= end_date]
        
        if period_videos:
            if len(period_videos) <= sample_per_period:
                sampled_videos.extend(period_videos)
            else:
                # Sort by metric and take top sample_per_period
                sorted_videos = _sort_videos_by_metric(period_videos, metric)
                sampled_videos.extend(sorted_videos[:sample_per_period])
    
    return sampled_videos


def _group_by_stratum(videos: List[Video], strata: str) -> Dict[str, List[Video]]:
    """Group videos by stratum (year, month, quarter)."""
    strata_groups = {}
    
    for video in videos:
        if strata == "year":
            stratum = str(video.published_at.year)
        elif strata == "month":
            stratum = video.published_at.strftime("%Y-%m")
        elif strata == "quarter":
            quarter = (video.published_at.month - 1) // 3 + 1
            stratum = f"{video.published_at.year}-Q{quarter}"
        else:
            raise ValueError(f"Unknown stratum: {strata}")
        
        if stratum not in strata_groups:
            strata_groups[stratum] = []
        strata_groups[stratum].append(video)
    
    return strata_groups


def _sort_videos_by_metric(videos: List[Video], metric: str) -> List[Video]:
    """Sort videos by the specified metric."""
    if not videos:
        return []
    
    # Get the current value for the metric
    def get_metric(video: Video):
        if metric == "views":
            return video.view_count_observations[-1].value if video.view_count_observations else video.view_count
        elif metric == "likes":
            return video.like_count_observations[-1].value if video.like_count_observations else video.like_count
        elif metric == "comments":
            return video.comment_count_observations[-1].value if video.comment_count_observations else video.comment_count
        elif metric == "engagement_rate":
            current_views = video.view_count_observations[-1].value if video.view_count_observations else video.view_count
            current_likes = video.like_count_observations[-1].value if video.like_count_observations else video.like_count
            current_comments = video.comment_count_observations[-1].value if video.comment_count_observations else video.comment_count
            return (current_likes + current_comments) / current_views if current_views > 0 else 0
        else:
            raise ValueError(f"Unknown metric: {metric}")
    
    return sorted(videos, key=get_metric, reverse=True)