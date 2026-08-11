"""
Test cases for RecommendationService.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from YouTubeComputationalSocialScience.services.recommendation_service import RecommendationService
from YouTubeComputationalSocialScience.domain.models import Video, Recommendation, CollectionRun
from YouTubeComputationalSocialScience.persistence.repository import VideoRepository, RecommendationRepository


@pytest.fixture
def mock_repositories():
    """Fixture for mock repositories."""
    video_repo = MagicMock(spec=VideoRepository)
    recommendation_repo = MagicMock(spec=RecommendationRepository)
    return video_repo, recommendation_repo


@pytest.fixture
def recommendation_service(mock_repositories):
    """Fixture for RecommendationService with mock repositories."""
    video_repo, recommendation_repo = mock_repositories
    return RecommendationService(video_repo, recommendation_repo)


def test_analyze_video_recommendations_success(recommendation_service):
    """Test successful recommendation network analysis."""
    # Mock the scraper and data extraction
    with patch('YouTubeComputationalSocialScience.services.recommendation_service.YouTubeScraper') as mock_scraper_class:
        with patch('YouTubeComputationalSocialScience.services.recommendation_service.extract_video_data') as mock_extract_video:
            with patch('YouTubeComputationalSocialScience.services.recommendation_service.extract_recommendation_data') as mock_extract_recommendation:
                
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
                mock_scraper.extract_video_recommendations.return_value = [
                    {"id": "rec1", "title": "Recommended Video 1"}
                ]
                
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
                
                mock_recommendation = Recommendation(
                    recommendation_id="rec1",
                    source_video_id="test_video",
                    source_video_title="Test Video",
                    source_channel_id="test_channel",
                    recommended_video_id="rec1",
                    recommended_video_title="Recommended Video 1",
                    recommended_video_url="https://youtube.com/rec1",
                    recommended_channel_id="rec_channel",
                    collection_run_id="test_run",
                    rank=1,
                    position="sidebar"
                )
                mock_extract_recommendation.return_value = mock_recommendation
                
                # Call the method
                result = recommendation_service.analyze_video_recommendations("https://youtube.com/test_video")
                
                # Assertions
                assert result["status"] == "success"
                assert result["source_video"]["video_id"] == "test_video"
                assert mock_scraper.create_collection_run.called
                assert mock_scraper.complete_collection_run.called


def test_analyze_video_recommendations_failure(recommendation_service):
    """Test recommendation network analysis failure."""
    # Mock the scraper to raise an exception
    with patch('YouTubeComputationalSocialScience.services.recommendation_service.YouTubeScraper') as mock_scraper_class:
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.extract_video_info.side_effect = Exception("Test error")
        
        # Call the method
        result = recommendation_service.analyze_video_recommendations("https://youtube.com/test_video")
        
        # Assertions
        assert result["status"] == "failed"
        assert "Test error" in result["error"]
        assert mock_scraper.complete_collection_run.called


def test_get_recommendation_network(recommendation_service):
    """Test getting recommendation network."""
    # Setup mock recommendations
    mock_recommendations = [
        Recommendation(
            recommendation_id="rec1",
            source_video_id="video1",
            source_video_title="Video 1",
            source_channel_id="channel1",
            recommended_video_id="video2",
            recommended_video_title="Video 2",
            recommended_video_url="https://youtube.com/video2",
            recommended_channel_id="channel2",
            collection_run_id="test_run",
            rank=1,
            position="sidebar"
        ),
        Recommendation(
            recommendation_id="rec2",
            source_video_id="video1",
            source_video_title="Video 1",
            source_channel_id="channel1",
            recommended_video_id="video3",
            recommended_video_title="Video 3",
            recommended_video_url="https://youtube.com/video3",
            recommended_channel_id="channel3",
            collection_run_id="test_run",
            rank=2,
            position="sidebar"
        )
    ]
    
    # Setup mock repository
    recommendation_service.recommendation_repository.get_video_recommendations.return_value = mock_recommendations
    
    # Call the method
    result = recommendation_service.get_recommendation_network("video1")
    
    # Assertions
    assert result["status"] == "success"
    assert result["video_id"] == "video1"
    assert "network" in result
    assert len(result["network"]["nodes"]) == 3  # video1, video2, video3
    assert len(result["network"]["edges"]) == 2  # Two recommendations


def test_analyze_recommendation_patterns(recommendation_service):
    """Test analyzing recommendation patterns."""
    # Setup mock recommendations to create a network
    mock_recommendations = [
        Recommendation(
            recommendation_id="rec1",
            source_video_id="video1",
            source_video_title="Video 1",
            source_channel_id="channel1",
            recommended_video_id="video2",
            recommended_video_title="Video 2",
            recommended_video_url="https://youtube.com/video2",
            recommended_channel_id="channel1",  # Same channel
            collection_run_id="test_run",
            rank=1,
            position="sidebar"
        ),
        Recommendation(
            recommendation_id="rec2",
            source_video_id="video1",
            source_video_title="Video 1",
            source_channel_id="channel1",
            recommended_video_id="video3",
            recommended_video_title="Video 3",
            recommended_video_url="https://youtube.com/video3",
            recommended_channel_id="channel2",  # Different channel
            collection_run_id="test_run",
            rank=2,
            position="sidebar"
        ),
        Recommendation(
            recommendation_id="rec3",
            source_video_id="video2",
            source_video_title="Video 2",
            source_channel_id="channel1",
            recommended_video_id="video1",
            recommended_video_title="Video 1",
            recommended_video_url="https://youtube.com/video1",
            recommended_channel_id="channel1",
            collection_run_id="test_run",
            rank=1,
            position="sidebar"
        )
    ]
    
    # Setup mock repository
    recommendation_service.recommendation_repository.get_video_recommendations.return_value = mock_recommendations
    
    # Call the method
    result = recommendation_service.analyze_recommendation_patterns("video1")
    
    # Assertions
    assert result["status"] == "success"
    assert result["video_id"] == "video1"
    assert "centrality_analysis" in result
    assert "network_properties" in result
    assert result["network_properties"]["channel_diversity"] > 0
    assert result["network_properties"]["reciprocity"] > 0


def test_get_recommendation_temporal_analysis(recommendation_service):
    """Test temporal analysis of recommendation patterns."""
    # Setup mock collection runs
    mock_runs = [
        CollectionRun(
            collection_run_id="run1",
            collection_type="recommendation",
            target_id="video1",
            target_url="https://youtube.com/video1",
            collection_time=datetime.now() - timedelta(days=1),
            status="completed"
        ),
        CollectionRun(
            collection_run_id="run2",
            collection_type="recommendation",
            target_id="video1",
            target_url="https://youtube.com/video1",
            collection_time=datetime.now(),
            status="completed"
        )
    ]
    
    # Setup mock recommendations for each run
    mock_recommendations_run1 = [
        Recommendation(
            recommendation_id="rec1",
            source_video_id="video1",
            source_video_title="Video 1",
            source_channel_id="channel1",
            recommended_video_id="video2",
            recommended_video_title="Video 2",
            recommended_video_url="https://youtube.com/video2",
            recommended_channel_id="channel2",
            collection_run_id="run1",
            rank=1,
            position="sidebar"
        )
    ]
    
    mock_recommendations_run2 = [
        Recommendation(
            recommendation_id="rec2",
            source_video_id="video1",
            source_video_title="Video 1",
            source_channel_id="channel1",
            recommended_video_id="video2",
            recommended_video_title="Video 2",
            recommended_video_url="https://youtube.com/video2",
            recommended_channel_id="channel2",
            collection_run_id="run2",
            rank=1,
            position="sidebar"
        ),
        Recommendation(
            recommendation_id="rec3",
            source_video_id="video1",
            source_video_title="Video 1",
            source_channel_id="channel1",
            recommended_video_id="video3",
            recommended_video_title="Video 3",
            recommended_video_url="https://youtube.com/video3",
            recommended_channel_id="channel3",
            collection_run_id="run2",
            rank=2,
            position="sidebar"
        )
    ]
    
    # Setup mock repositories
    recommendation_service.recommendation_repository.get_collection_runs_for_video.return_value = mock_runs
    recommendation_service.recommendation_repository.get_recommendations_by_run.side_effect = [
        mock_recommendations_run1, 
        mock_recommendations_run2
    ]
    
    # Call the method
    result = recommendation_service.get_recommendation_temporal_analysis("video1")
    
    # Assertions
    assert result["status"] == "success"
    assert result["video_id"] == "video1"
    assert "temporal_analysis" in result
    assert len(result["temporal_analysis"]) == 2  # Two collection runs
    assert result["temporal_analysis"]["run1"]["nodes"] == 2  # video1 and video2
    assert result["temporal_analysis"]["run2"]["nodes"] == 3  # video1, video2, and video3