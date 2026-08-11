"""
Data extraction and normalization for YouTube Computational Social Science research.

Provides functions to extract and normalize YouTube data from yt-dlp results
into research-grade domain models while preserving provenance and data quality.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from ..domain.models import Channel, Video, Comment, Recommendation, Observation, CollectionStatus


def extract_channel_data(scraper_result: Dict[str, Any], collection_run_id: str) -> Channel:
    """
    Extract and normalize channel data from yt-dlp result.
    
    Args:
        scraper_result: Raw result from yt-dlp
        collection_run_id: ID of the collection run
        
    Returns:
        Normalized Channel object
    """
    # Create observation for current metrics
    observed_at = datetime.now()
    
    # Extract basic channel info
    channel_id = scraper_result.get('id', '')
    title = scraper_result.get('title', '')
    description = scraper_result.get('description', '')
    custom_url = scraper_result.get('custom_url')
    published_at = _parse_datetime(scraper_result.get('channel_create_time'))
    thumbnail_url = scraper_result.get('thumbnail')
    country = scraper_result.get('country')
    
    # Extract statistics - use `or 0` to handle None values
    subscriber_count = scraper_result.get('subscriber_count') or 0
    video_count = scraper_result.get('video_count') or 0
    view_count = scraper_result.get('view_count') or 0
    
    # Create channel object
    channel = Channel(
        channel_id=channel_id,
        title=title,
        description=description,
        custom_url=custom_url,
        published_at=published_at,
        thumbnail_url=thumbnail_url,
        country=country,
        subscriber_count=subscriber_count,
        video_count=video_count,
        view_count=view_count,
        collection_status=CollectionStatus.SUCCESS,
        collection_errors=[],
        collection_run_id=collection_run_id,
        url=scraper_result.get('webpage_url', ''),
        
        # Historical observations
        subscriber_count_observations=[
            Observation(
                observed_at=observed_at,
                value=subscriber_count,
                source="raw",
                collection_run_id=collection_run_id
            )
        ],
        video_count_observations=[
            Observation(
                observed_at=observed_at,
                value=video_count,
                source="raw",
                collection_run_id=collection_run_id
            )
        ],
        view_count_observations=[
            Observation(
                observed_at=observed_at,
                value=view_count,
                source="raw",
                collection_run_id=collection_run_id
            )
        ]
    )
    
    return channel


def extract_video_data(scraper_result: Dict[str, Any], collection_run_id: str, channel_id: str, script: str = "") -> Video:
    """
    Extract and normalize video data from yt-dlp result.
    
    Args:
        scraper_result: Raw result from yt-dlp
        collection_run_id: ID of the collection run
        channel_id: ID of the channel this video belongs to
        script: Optional video transcript/script
        
    Returns:
        Normalized Video object
    """
    # Create observation for current metrics
    observed_at = datetime.now()
    
    # Extract basic video info
    video_id = scraper_result.get('id', '')
    title = scraper_result.get('title', '')
    description = scraper_result.get('description', '')
    published_at = _parse_datetime(scraper_result.get('upload_date'))
    duration = scraper_result.get('duration', 0)
    category = scraper_result.get('categories', [None])[0] if scraper_result.get('categories') else None
    tags = scraper_result.get('tags', [])
    language = scraper_result.get('language')
    thumbnail_url = scraper_result.get('thumbnail')
    
    # Extract chapters if available
    chapters = []
    if 'chapters' in scraper_result and scraper_result['chapters']:
        for ch in scraper_result['chapters']:
            chapters.append({
                'title': ch.get('title', ''),
                'start_time': ch.get('start_time', 0),
                'end_time': ch.get('end_time', 0)
            })
    
    # Extract statistics
    view_count = scraper_result.get('view_count', 0)
    like_count = scraper_result.get('like_count', 0)
    comment_count = scraper_result.get('comment_count', 0)
    
    # Create video object
    video = Video(
        video_id=video_id,
        channel_id=channel_id,
        title=title,
        description=description,
        published_at=published_at,
        duration=duration,
        category=category,
        tags=tags,
        language=language,
        view_count=view_count,
        like_count=like_count,
        comment_count=comment_count,
        script=script,
        thumbnail_url=thumbnail_url,
        chapters=chapters,
        collection_status=CollectionStatus.SUCCESS,
        collection_errors=[],
        collection_run_id=collection_run_id,
        url=scraper_result.get('webpage_url', ''),
        
        # Historical observations
        view_count_observations=[
            Observation(
                observed_at=observed_at,
                value=view_count,
                source="raw",
                collection_run_id=collection_run_id
            )
        ],
        like_count_observations=[
            Observation(
                observed_at=observed_at,
                value=like_count,
                source="raw",
                collection_run_id=collection_run_id
            )
        ],
        comment_count_observations=[
            Observation(
                observed_at=observed_at,
                value=comment_count,
                source="raw",
                collection_run_id=collection_run_id
            )
        ]
    )
    
    return video


def extract_comment_data(scraper_result: Dict[str, Any], collection_run_id: str, video_id: str, channel_id: str) -> Comment:
    """
    Extract and normalize comment data from yt-dlp result.
    
    Args:
        scraper_result: Raw result from yt-dlp
        collection_run_id: ID of the collection run
        video_id: ID of the video this comment belongs to
        channel_id: ID of the channel this comment belongs to
        
    Returns:
        Normalized Comment object
    """
    # Create observation for current metrics
    observed_at = datetime.now()
    
    # Extract basic comment info
    comment_id = scraper_result.get('id', str(uuid.uuid4()))
    author_id = scraper_result.get('author_id')
    author_name = scraper_result.get('author')
    text = scraper_result.get('text', '')
    published_at = _parse_datetime(scraper_result.get('timestamp'))
    like_count = scraper_result.get('like_count', 0)
    parent_id = scraper_result.get('parent_id')
    is_reply = parent_id is not None
    
    # Create comment object
    comment = Comment(
        comment_id=comment_id,
        video_id=video_id,
        channel_id=channel_id,
        author_id=author_id,
        author_name=author_name,
        text=text,
        published_at=published_at,
        like_count=like_count,
        reply_count=0,  # Will be updated when replies are processed
        parent_id=parent_id,
        is_reply=is_reply,
        collection_status=CollectionStatus.SUCCESS,
        collection_errors=[],
        collection_run_id=collection_run_id,
        
        # Historical observations
        like_count_observations=[
            Observation(
                observed_at=observed_at,
                value=like_count,
                source="raw",
                collection_run_id=collection_run_id
            )
        ],
        reply_count_observations=[]
    )
    
    return comment


def extract_recommendation_data(scraper_result: Dict[str, Any], collection_run_id: str, source_video_id: str) -> Recommendation:
    """
    Extract and normalize recommendation data from yt-dlp result.
    
    Args:
        scraper_result: Raw result from yt-dlp
        collection_run_id: ID of the collection run
        source_video_id: ID of the source video
        
    Returns:
        Normalized Recommendation object
    """
    # Extract basic recommendation info
    recommended_video_id = scraper_result.get('id', '')
    recommendation_rank = scraper_result.get('rank')
    recommendation_context = scraper_result.get('context', 'related_videos')
    
    # Extract metadata about the recommended video
    recommended_video_title = scraper_result.get('title', '')
    recommended_channel_id = scraper_result.get('channel_id', '')
    recommended_channel_title = scraper_result.get('channel', '')
    recommended_video_url = scraper_result.get('url', '') or f"https://youtube.com/watch?v={recommended_video_id}"
    
    # Create recommendation object
    recommendation = Recommendation(
        source_video_id=source_video_id,
        source_video_title=scraper_result.get('source_video_title'),
        source_channel_id=scraper_result.get('source_channel_id'),
        source_channel_title=scraper_result.get('source_channel_title'),
        recommended_video_id=recommended_video_id,
        recommended_video_title=recommended_video_title,
        recommended_video_url=recommended_video_url,
        recommended_channel_id=recommended_channel_id,
        recommended_channel_title=recommended_channel_title,
        rank=recommendation_rank,
        position=recommendation_context,
        collection_run_id=collection_run_id,
        observed_at=datetime.now()
    )
    
    return recommendation


def normalize_channel(raw_data: Dict[str, Any], collection_run_id: str) -> Channel:
    """
    Normalize raw channel data into a Channel object.
    
    Args:
        raw_data: Raw channel data
        collection_run_id: ID of the collection run
        
    Returns:
        Normalized Channel object
    """
    return extract_channel_data(raw_data, collection_run_id)


def normalize_video(raw_data: Dict[str, Any], collection_run_id: str, channel_id: str) -> Video:
    """
    Normalize raw video data into a Video object.
    
    Args:
        raw_data: Raw video data
        collection_run_id: ID of the collection run
        channel_id: ID of the channel this video belongs to
        
    Returns:
        Normalized Video object
    """
    return extract_video_data(raw_data, collection_run_id, channel_id)


def normalize_comment(raw_data: Dict[str, Any], collection_run_id: str, video_id: str, channel_id: str) -> Comment:
    """
    Normalize raw comment data into a Comment object.
    
    Args:
        raw_data: Raw comment data
        collection_run_id: ID of the collection run
        video_id: ID of the video this comment belongs to
        channel_id: ID of the channel this comment belongs to
        
    Returns:
        Normalized Comment object
    """
    return extract_comment_data(raw_data, collection_run_id, video_id, channel_id)


def normalize_recommendation(raw_data: Dict[str, Any], collection_run_id: str, source_video_id: str) -> Recommendation:
    """
    Normalize raw recommendation data into a Recommendation object.
    
    Args:
        raw_data: Raw recommendation data
        collection_run_id: ID of the collection run
        source_video_id: ID of the source video
        
    Returns:
        Normalized Recommendation object
    """
    return extract_recommendation_data(raw_data, collection_run_id, source_video_id)


def _parse_datetime(date_str: Optional[str]) -> datetime:
    """Parse a date string into a datetime object."""
    if not date_str:
        return datetime.now()
    
    try:
        # Try parsing different date formats
        if len(date_str) == 8:  # YYYYMMDD
            return datetime.strptime(date_str, "%Y%m%d")
        elif len(date_str) == 10 and date_str[4] == '-':  # YYYY-MM-DD
            return datetime.strptime(date_str, "%Y-%m-%d")
        else:
            # Try parsing as timestamp
            return datetime.fromtimestamp(int(date_str))
    except (ValueError, TypeError):
        return datetime.now()