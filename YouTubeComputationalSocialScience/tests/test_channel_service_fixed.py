"""
Test cases for ChannelService.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from YouTubeComputationalSocialScience.services.channel_service import ChannelService
from YouTubeComputationalSocialScience.domain.models import Channel, Video, Comment, CollectionRun, ChannelAnalytics
from YouTubeComputationalSocialScience.persistence.repository import ChannelRepository, VideoRepository, CommentRepository


@pytest.fixture
def mock_repositories():
    """Fixture for mock repositories."""
    channel_repo = MagicMock(spec=ChannelRepository)
    video_repo = MagicMock(spec=VideoRepository)
    comment_repo = MagicMock(spec=CommentRepository)
    return channel_repo, video_repo, comment_repo


@pytest.fixture
def channel_service(mock_repositories):
    """Fixture for ChannelService with mock repositories."""
    channel_repo, video_repo, comment_repo = mock_repositories
    return ChannelService(channel_repo, video_repo, comment_repo)


def test_analyze_channel_success(channel_service):
    """Test successful channel analysis."""
    # Mock the scraper and data extraction
    with patch('YouTubeComputationalSocialScience.services.channel_service.YouTubeScraper') as mock_scraper_class:
        with patch('YouTubeComputationalSocialScience.services.channel_service.extract_channel_data') as mock_extract_channel:
            with patch('YouTubeComputationalSocialScience.services.channel_service.extract_video_data') as mock_extract_video:
                
                # Setup mock scraper
                mock_scraper = MagicMock()
                mock_scraper_class.return_value = mock_scraper
                mock_scraper.extract_channel_info.return_value = {"id": "test_channel", "title": "Test Channel"}
                mock_scraper.extract_channel_videos.return_value = [{"id": "video1", "title": "Test Video"}]
                mock_scraper.extract_video_comments.return_value = []
                
                # Setup mock data extraction
                mock_channel = Channel(
                    channel_id="test_channel",
                    title="Test Channel",
                    description="Test Description",
                    url="https://youtube.com/test_channel",
                    collection_run_id="test_run",
                    published_at=datetime.now(),
                    subscriber_count=1000,
                    video_count=100,
                    view_count=100000
                )
                mock_extract_channel.return_value = mock_channel
                
                mock_video = Video(
                    video_id="video1",
                    title="Test Video",
                    description="Test Video Description",
                    url="https://youtube.com/video1",
                    channel_id="test_channel",
                    collection_run_id="test_run",
                    published_at=datetime.now(),
                    duration=600,
                    view_count=1000,
                    like_count=100,
                    comment_count=50
                )
                mock_extract_video.return_value = mock_video
                
                # Call the method
                result = channel_service.analyze_channel("https://youtube.com/test_channel")
                
                # Assertions
                assert result["status"] == "success"
                assert result["channel"]["channel_id"] == "test_channel"
                assert result["videos_collected"] == 1
                assert mock_scraper.create_collection_run.called
                assert mock_scraper.complete_collection_run.called


def test_analyze_channel_failure(channel_service):
    """Test channel analysis failure."""
    # Mock the scraper to raise an exception
    with patch('YouTubeComputationalSocialScience.services.channel_service.YouTubeScraper') as mock_scraper_class:
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.extract_channel_info.side_effect = Exception("Test error")
        
        # Call the method
        result = channel_service.analyze_channel("https://youtube.com/test_channel")
        
        # Assertions
        assert result["status"] == "failed"
        assert "Test error" in result["error"]
        assert mock_scraper.complete_collection_run.called


def test_get_channel_analytics(channel_service):
    """Test getting channel analytics."""
    # Setup mock channel
    mock_channel = Channel(
        channel_id="test_channel",
        title="Test Channel",
        description="Test Description",
        url="https://youtube.com/test_channel",
        collection_run_id="test_run",
        published_at=datetime.now(),
        subscriber_count=1000,
        video_count=100,
        view_count=100000
    )
    
    # Setup mock videos
    mock_videos = [
        Video(
            video_id="video1",
            title="Test Video 1",
            description="Test Video Description 1",
            url="https://youtube.com/video1",
            channel_id="test_channel",
            collection_run_id="test_run",
            published_at=datetime.now() - timedelta(days=1),
            duration=600,
            view_count=1000,
            like_count=100,
            comment_count=50
        ),
        Video(
            video_id="video2",
            title="Test Video 2",
            description="Test Video Description 2",
            url="https://youtube.com/video2",
            channel_id="test_channel",
            collection_run_id="test_run",
            published_at=datetime.now(),
            duration=600,
            view_count=2000,
            like_count=200,
            comment_count=100
        )
    ]
    
    # Setup mock repositories
    channel_service.channel_repository.get_channel.return_value = mock_channel
    channel_service.channel_repository.get_channel_videos.return_value = mock_videos
    
    # Call the method
    result = channel_service.get_channel_analytics("test_channel")
    
    # Assertions
    assert result["status"] == "success"
    assert result["channel_id"] == "test_channel"
    assert "analytics" in result
    assert result["analytics"]["total_videos"] == 2


def test_compare_channels(channel_service):
    """Test comparing multiple channels."""
    # Setup mock channels
    mock_channel1 = Channel(
        channel_id="channel1",
        title="Channel 1",
        description="Channel 1 Description",
        url="https://youtube.com/channel1",
        collection_run_id="test_run",
        published_at=datetime.now(),
        subscriber_count=1000,
        video_count=50,
        view_count=50000
    )
    
    mock_channel2 = Channel(
        channel_id="channel2",
        title="Channel 2",
        description="Channel 2 Description",
        url="https://youtube.com/channel2",
        collection_run_id="test_run",
        published_at=datetime.now(),
        subscriber_count=2000,
        video_count=100,
        view_count=200000
    )
    
    # Setup mock videos
    mock_videos1 = [
        Video(
            video_id="video1",
            title="Video 1",
            description="Video 1 Description",
            url="https://youtube.com/video1",
            channel_id="channel1",
            collection_run_id="test_run",
            published_at=datetime.now(),
            duration=600,
            view_count=1000,
            like_count=100,
            comment_count=50
        )
    ]
    
    mock_videos2 = [
        Video(
            video_id="video2",
            title="Video 2",
            description="Video 2 Description",
            url="https://youtube.com/video2",
            channel_id="channel2",
            collection_run_id="test_run",
            published_at=datetime.now(),
            duration=600,
            view_count=2000,
            like_count=200,
            comment_count=100
        )
    ]
    
    # Setup mock repositories
    channel_service.channel_repository.get_channel.side_effect = [mock_channel1, mock_channel2]
    channel_service.channel_repository.get_channel_videos.side_effect = [mock_videos1, mock_videos2]
    
    # Call the method
    result = channel_service.compare_channels(["channel1", "channel2"])
    
    # Assertions
    assert result["status"] == "success"
    assert result["channels_compared"] == 2
    assert "channel1" in result["comparison"]
    assert "channel2" in result["comparison"]


def test_get_channel_upload_pattern(channel_service):
    """Test getting channel upload pattern."""
    # Setup mock channel
    mock_channel = Channel(
        channel_id="test_channel",
        title="Test Channel",
        description="Test Description",
        url="https://youtube.com/test_channel",
        collection_run_id="test_run",
        published_at=datetime.now(),
        subscriber_count=1000,
        video_count=100,
        view_count=100000
    )
    
    # Setup mock videos with different publication dates
    now = datetime.now()
    mock_videos = [
        Video(
            video_id=f"video{i}",
            title=f"Video {i}",
            description=f"Video {i} Description",
            url=f"https://youtube.com/video{i}",
            channel_id="test_channel",
            collection_run_id="test_run",
            published_at=now - timedelta(days=i*7),  # Weekly uploads
            duration=600,
            view_count=1000,
            like_count=100,
            comment_count=50
        ) for i in range(5)
    ]
    
    # Setup mock repositories
    channel_service.channel_repository.get_channel.return_value = mock_channel
    channel_service.channel_repository.get_channel_videos.return_value = mock_videos
    
    # Call the method
    result = channel_service.get_channel_upload_pattern("test_channel")
    
    # Assertions
    assert result["status"] == "success"
    assert result["channel_id"] == "test_channel"
    assert "upload_pattern" in result
    assert result["total_videos"] == 5