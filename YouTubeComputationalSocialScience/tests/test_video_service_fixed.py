"""
Test cases for VideoService.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
import os
import random

# Add the parent directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from YouTubeComputationalSocialScience.services.video_service import VideoService
from YouTubeComputationalSocialScience.domain.models import Video, Comment, VideoAnalytics, CommentAnalytics
from YouTubeComputationalSocialScience.persistence.repository import VideoRepository, CommentRepository


@pytest.fixture
def mock_repositories():
    """Fixture for mock repositories."""
    video_repo = MagicMock(spec=VideoRepository)
    comment_repo = MagicMock(spec=CommentRepository)
    return video_repo, comment_repo


@pytest.fixture
def video_service(mock_repositories):
    """Fixture for VideoService with mock repositories."""
    video_repo, comment_repo = mock_repositories
    return VideoService(video_repo, comment_repo)


def test_analyze_video_success(video_service):
    """Test successful video analysis."""
    # Mock the scraper and data extraction
    with patch('YouTubeComputationalSocialScience.services.video_service.YouTubeScraper') as mock_scraper_class:
        with patch('YouTubeComputationalSocialScience.services.video_service.extract_video_data') as mock_extract_video:
            with patch('YouTubeComputationalSocialScience.services.video_service.extract_comment_data') as mock_extract_comment:
                
                # Setup mock scraper
                mock_scraper = MagicMock()
                mock_scraper_class.return_value = mock_scraper
                mock_scraper.extract_video_info.return_value = {
                    "id": "test_video", 
                    "title": "Test Video",
                    "channel_id": "test_channel",
                    "duration": 600,
                    "category": "Education",
                    "language": "en"
                }
                mock_scraper.extract_video_comments.return_value = [{"id": "comment1", "text": "Test comment"}]
                mock_scraper.collection_run.comments_collected = 1
                mock_scraper.get_collection_run.return_value = MagicMock()
                mock_scraper.get_collection_run.return_value.model_dump.return_value = {"collection_run_id": "test_run"}
                
                # Setup mock data extraction
                mock_video = Video(
                    video_id="test_video",
                    title="Test Video",
                    description="Test Description",
                    url="https://youtube.com/test_video",
                    channel_id="test_channel",
                    collection_run_id="test_run",
                    published_at=datetime.now(),
                    duration=600,
                    category="Education",
                    language="en",
                    view_count=1000,
                    like_count=100,
                    comment_count=50
                )
                mock_extract_video.return_value = mock_video
                
                mock_comment = Comment(
                    comment_id="comment1",
                    text="Test comment",
                    video_id="test_video",
                    channel_id="test_channel",
                    collection_run_id="test_run",
                    published_at=datetime.now(),
                    like_count=10,
                    reply_count=0
                )
                mock_extract_comment.return_value = mock_comment
                
                # Setup repository to return saved comments
                video_service.comment_repository.get_video_comments.return_value = [mock_comment]
                
                # Call the method
                result = video_service.analyze_video("https://youtube.com/test_video")
                
                # Assertions
                assert result["status"] == "success"
                assert result["video"]["video_id"] == "test_video"
                assert mock_scraper.create_collection_run.called
                assert mock_scraper.complete_collection_run.called


def test_analyze_video_failure(video_service):
    """Test video analysis failure."""
    # Mock the scraper to raise an exception
    with patch('YouTubeComputationalSocialScience.services.video_service.YouTubeScraper') as mock_scraper_class:
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.extract_video_info.side_effect = Exception("Test error")
        
        # Call the method
        result = video_service.analyze_video("https://youtube.com/test_video")
        
        # Assertions
        assert result["status"] == "failed"
        assert "Test error" in result["error"]
        assert mock_scraper.complete_collection_run.called


def test_get_video_analytics(video_service):
    """Test getting video analytics."""
    # Setup mock video
    mock_video = Video(
        video_id="test_video",
        title="Test Video",
        description="Test Description",
        url="https://youtube.com/test_video",
        channel_id="test_channel",
        collection_run_id="test_run",
        published_at=datetime.now(),
        duration=600,
        category="Education",
        language="en",
        view_count=1000,
        like_count=100,
        comment_count=50
    )
    
    # Setup mock comments
    mock_comments = [
        Comment(
            comment_id=f"comment{i}",
            text=f"Test comment {i}",
            video_id="test_video",
            channel_id="test_channel",
            collection_run_id="test_run",
            published_at=datetime.now() - timedelta(hours=i),
            like_count=i*10,
            collection_status="success"
        ) for i in range(3)
    ]
    
    # Setup mock repositories
    video_service.video_repository.get_video.return_value = mock_video
    video_service.comment_repository.get_video_comments.return_value = mock_comments
    
    # Call the method
    result = video_service.get_video_analytics("test_video")
    
    # Assertions
    assert result["status"] == "success"
    assert result["video_id"] == "test_video"
    assert "video_analytics" in result
    assert "comment_analytics" in result


def test_get_video_comment_samples(video_service):
    """Test getting comment samples from a video."""
    # Setup mock video
    mock_video = Video(
        video_id="test_video",
        title="Test Video",
        description="Test Description",
        url="https://youtube.com/test_video",
        channel_id="test_channel",
        collection_run_id="test_run",
        published_at=datetime.now(),
        duration=600,
        category="Education",
        language="en",
        view_count=1000,
        like_count=100,
        comment_count=50
    )
    
    # Setup mock comments with varying like counts and timestamps
    now = datetime.now()
    mock_comments = [
        Comment(
            comment_id=f"comment{i}",
            text=f"Test comment {i}",
            video_id="test_video",
            channel_id="test_channel",
            collection_run_id="test_run",
            published_at=now - timedelta(hours=i),
            like_count=(10 - i) * 10,  # Varying like counts
            collection_status="success"
        ) for i in range(10)
    ]
    
    # Setup mock repositories
    video_service.video_repository.get_video.return_value = mock_video
    video_service.comment_repository.get_video_comments.return_value = mock_comments
    
    # Test top_likes strategy
    result = video_service.get_video_comment_samples("test_video", "top_likes", 3)
    assert result["status"] == "success"
    assert result["sample_size"] == 3
    assert result["comments"][0]["like_count"] >= result["comments"][1]["like_count"]
    
    # Test latest strategy
    result = video_service.get_video_comment_samples("test_video", "latest", 3)
    assert result["status"] == "success"
    assert result["sample_size"] == 3
    
    # Test invalid strategy
    result = video_service.get_video_comment_samples("test_video", "invalid_strategy", 3)
    assert result["status"] == "invalid_strategy"


def test_analyze_video_engagement_temporal(video_service):
    """Test temporal analysis of video engagement."""
    # Setup mock video
    mock_video = Video(
        video_id="test_video",
        title="Test Video",
        description="Test Description",
        url="https://youtube.com/test_video",
        channel_id="test_channel",
        collection_run_id="test_run",
        published_at=datetime.now() - timedelta(days=2),
        duration=600,
        category="Education",
        language="en",
        view_count=1000,
        like_count=100,
        comment_count=50
    )
    
    # Setup mock comments with varying timestamps
    video_published = mock_video.published_at
    mock_comments = [
        # Comments in first hour
        Comment(
            comment_id="comment1",
            text="First hour comment",
            video_id="test_video",
            channel_id="test_channel",
            collection_run_id="test_run",
            published_at=video_published + timedelta(minutes=30),
            like_count=5,
            collection_status="success"
        ),
        # Comments in 1-6 hours
        Comment(
            comment_id="comment2",
            text="1-6 hour comment",
            video_id="test_video",
            channel_id="test_channel",
            collection_run_id="test_run",
            published_at=video_published + timedelta(hours=3),
            like_count=10,
            collection_status="success"
        ),
        # Comments in 6-24 hours
        Comment(
            comment_id="comment3",
            text="6-24 hour comment",
            video_id="test_video",
            channel_id="test_channel",
            collection_run_id="test_run",
            published_at=video_published + timedelta(hours=12),
            like_count=15,
            collection_status="success"
        ),
        # Comments after 1 day
        Comment(
            comment_id="comment4",
            text="After 1 day comment",
            video_id="test_video",
            channel_id="test_channel",
            collection_run_id="test_run",
            published_at=video_published + timedelta(days=1, hours=12),
            like_count=20,
            collection_status="success"
        )
    ]
    
    # Setup mock repositories
    video_service.video_repository.get_video.return_value = mock_video
    video_service.comment_repository.get_video_comments.return_value = mock_comments
    
    # Call the method
    result = video_service.analyze_video_engagement_temporal("test_video")
    
    # Assertions
    assert result["status"] == "success"
    assert result["video_id"] == "test_video"
    assert "comment_velocity" in result
    assert "engagement_decay" in result
    assert "comment_timing_distribution" in result
    assert result["comment_timing_distribution"]["<1 hour"] == 1
    assert result["comment_timing_distribution"]["1-6 hours"] == 1


def test_compare_videos(video_service):
    """Test comparing multiple videos."""
    # Setup mock videos
    mock_video1 = Video(
        video_id="video1",
        title="Video 1",
        description="Video 1 Description",
        url="https://youtube.com/video1",
        channel_id="channel1",
        collection_run_id="test_run",
        published_at=datetime.now(),
        duration=600,
        category="Education",
        language="en",
        view_count=1000,
        like_count=100,
        comment_count=50
    )
    
    mock_video2 = Video(
        video_id="video2",
        title="Video 2",
        description="Video 2 Description",
        url="https://youtube.com/video2",
        channel_id="channel2",
        collection_run_id="test_run",
        published_at=datetime.now(),
        duration=600,
        category="Education",
        language="en",
        view_count=2000,
        like_count=200,
        comment_count=100
    )
    
    # Setup mock comments
    mock_comments1 = [
        Comment(
            comment_id="comment1",
            text="Comment 1",
            video_id="video1",
            channel_id="channel1",
            collection_run_id="test_run",
            published_at=datetime.now(),
            like_count=10,
            collection_status="success"
        )
    ]
    
    mock_comments2 = [
        Comment(
            comment_id="comment2",
            text="Comment 2",
            video_id="video2",
            channel_id="channel2",
            collection_run_id="test_run",
            published_at=datetime.now(),
            like_count=20,
            collection_status="success"
        )
    ]
    
    # Setup mock repositories
    video_service.video_repository.get_video.side_effect = [mock_video1, mock_video2]
    video_service.comment_repository.get_video_comments.side_effect = [mock_comments1, mock_comments2]
    
    # Call the method
    result = video_service.compare_videos(["video1", "video2"])
    
    # Assertions
    assert result["status"] == "success"
    assert result["videos_compared"] == 2
    assert "video1" in result["comparison"]
    assert "video2" in result["comparison"]