"""
API endpoints for YouTube Computational Social Science research module.

Provides FastAPI endpoints for channel, video, and recommendation analysis.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
from ..services.channel_service import ChannelService
from ..services.video_service import VideoService
from ..services.recommendation_service import RecommendationService
from ..persistence.excel_repository import ExcelChannelRepository, ExcelVideoRepository, ExcelCommentRepository, ExcelRecommendationRepository

# Initialize FastAPI app
app = FastAPI(title="YouTube Computational Social Science API", 
              description="API for research-grade YouTube data analysis",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize repositories
channel_repo = ExcelChannelRepository()
video_repo = ExcelVideoRepository()
comment_repo = ExcelCommentRepository()
recommendation_repo = ExcelRecommendationRepository()

# Initialize services
channel_service = ChannelService(channel_repo, video_repo, comment_repo)
video_service = VideoService(video_repo, comment_repo)
recommendation_service = RecommendationService(video_repo, recommendation_repo)


# Channel Endpoints
@app.post("/channels/analyze")
async def analyze_channel(
    channel_url: str = Query(..., description="URL of the YouTube channel to analyze"),
    video_limit: int = Query(100, description="Maximum number of videos to collect"),
    comment_limit: int = Query(1000, description="Maximum number of comments to collect per video"),
    sampling_strategy: str = Query("stratified", description="Strategy for sampling videos")
):
    """
    Analyze a YouTube channel and return comprehensive research data.
    """
    result = channel_service.analyze_channel(
        channel_url=channel_url,
        video_limit=video_limit,
        comment_limit=comment_limit,
        sampling_strategy=sampling_strategy
    )
    
    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/channels/{channel_id}/analytics")
async def get_channel_analytics(channel_id: str):
    """
    Get pre-calculated analytics for a channel.
    """
    result = channel_service.get_channel_analytics(channel_id)
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.post("/channels/compare")
async def compare_channels(
    channel_ids: List[str] = Query(..., description="List of channel IDs to compare"),
    start_date: Optional[datetime] = Query(None, description="Start date for comparison period"),
    end_date: Optional[datetime] = Query(None, description="End date for comparison period")
):
    """
    Compare multiple channels across various metrics.
    """
    period = (start_date, end_date) if start_date and end_date else None
    result = channel_service.compare_channels(channel_ids, period)
    
    return result

@app.get("/channels/{channel_id}/upload-pattern")
async def get_channel_upload_pattern(channel_id: str):
    """
    Analyze the upload pattern of a channel.
    """
    result = channel_service.get_channel_upload_pattern(channel_id)
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["error"])
    if result["status"] == "no_data":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@app.get("/channels/{channel_id}/engagement-analysis")
async def get_channel_engagement_analysis(channel_id: str):
    """
    Get comprehensive engagement analysis for a channel.
    
    Provides detailed engagement metrics including distribution
    percentiles for views, likes, and comments.
    """
    result = channel_service.get_channel_engagement_analysis(channel_id)
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["error"])
    if result["status"] == "no_data":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@app.get("/channels/{channel_id}/performance-distribution")
async def get_channel_performance_distribution(channel_id: str):
    """
    Get performance distribution analysis for a channel.
    
    Provides top/bottom percentile analysis for video performance,
    identifying outliers and high/low performers.
    """
    result = channel_service.get_channel_performance_distribution(channel_id)
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["error"])
    if result["status"] == "no_data":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


# Video Endpoints
@app.post("/videos/analyze")
async def analyze_video(
    video_url: str = Query(..., description="URL of the YouTube video to analyze"),
    comment_limit: int = Query(1000, description="Maximum number of comments to collect"),
    collect_recommendations: bool = Query(False, description="Whether to collect video recommendations")
):
    """
    Analyze a YouTube video and return comprehensive research data.
    """
    result = video_service.analyze_video(
        video_url=video_url,
        comment_limit=comment_limit,
        collect_recommendations=collect_recommendations
    )
    
    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/videos/{video_id}/analytics")
async def get_video_analytics(video_id: str):
    """
    Get pre-calculated analytics for a video.
    """
    result = video_service.get_video_analytics(video_id)
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.get("/videos/{video_id}/comments/sample")
async def get_video_comment_samples(
    video_id: str,
    sample_strategy: str = Query("top_likes", description="Sampling strategy for comments"),
    sample_size: int = Query(20, description="Number of comments to sample")
):
    """
    Get comment samples from a video using different sampling strategies.
    """
    result = video_service.get_video_comment_samples(
        video_id=video_id,
        sample_strategy=sample_strategy,
        sample_size=sample_size
    )
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["error"])
    if result["status"] == "no_data":
        raise HTTPException(status_code=404, detail=result["error"])
    if result["status"] == "invalid_strategy":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/videos/{video_id}/engagement/temporal")
async def get_video_engagement_temporal(video_id: str):
    """
    Analyze the temporal pattern of video engagement.
    """
    result = video_service.analyze_video_engagement_temporal(video_id)
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["error"])
    if result["status"] == "no_data":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.post("/videos/compare")
async def compare_videos(video_ids: List[str] = Query(..., description="List of video IDs to compare")):
    """
    Compare multiple videos across various metrics.
    """
    result = video_service.compare_videos(video_ids)
    
    return result


# Recommendation Endpoints
@app.post("/recommendations/analyze")
async def analyze_video_recommendations(
    video_url: str = Query(..., description="URL of the YouTube video to analyze recommendations for"),
    depth: int = Query(1, description="Depth of recommendation network to collect")
):
    """
    Analyze the recommendation network for a YouTube video.
    """
    result = recommendation_service.analyze_video_recommendations(
        video_url=video_url,
        depth=depth
    )
    
    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/recommendations/{video_id}/network")
async def get_recommendation_network(video_id: str):
    """
    Get the recommendation network for a video.
    """
    result = recommendation_service.get_recommendation_network(video_id)
    
    return result

@app.get("/recommendations/{video_id}/patterns")
async def get_recommendation_patterns(video_id: str):
    """
    Analyze patterns in the recommendation network.
    """
    result = recommendation_service.analyze_recommendation_patterns(video_id)
    
    if result["status"] == "no_data":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.get("/recommendations/{video_id}/temporal")
async def get_recommendation_temporal_analysis(video_id: str):
    """
    Analyze how recommendation patterns change over time.
    """
    result = recommendation_service.get_recommendation_temporal_analysis(video_id)
    
    if result["status"] == "no_data":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


# Video Advanced Analytics Endpoints
@app.get("/videos/{video_id}/engagement-analysis")
async def get_video_engagement_analysis(video_id: str):
    """
    Get comprehensive engagement analysis for a video.
    
    Provides detailed engagement metrics including rates, comment analytics,
    and distribution data.
    """
    result = video_service.get_video_engagement_analysis(video_id)
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@app.get("/videos/{video_id}/comment-analysis")
async def get_video_comment_analysis(video_id: str):
    """
    Get comprehensive comment analysis for a video.
    
    Provides detailed comment metrics including timing, engagement,
    distribution, and participation patterns.
    """
    result = video_service.get_video_comment_analysis(video_id)
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@app.get("/videos/{video_id}/comment-distribution")
async def get_video_comment_distribution(video_id: str):
    """
    Get comment distribution analysis for a video.
    
    Provides percentiles for likes, replies, and length distributions.
    """
    result = video_service.get_video_comment_distribution(video_id)
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["error"])
    if result["status"] == "no_data":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@app.get("/videos/{video_id}/comment-concentration")
async def get_video_comment_concentration(video_id: str):
    """
    Get comment concentration analysis for a video.
    
    Measures how engagement is concentrated in a small number of comments.
    Includes Gini coefficient and top X% share metrics.
    """
    result = video_service.get_video_comment_concentration(video_id)
    
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail=result["error"])
    if result["status"] == "no_data":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result