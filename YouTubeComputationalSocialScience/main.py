"""
Main entry point for YouTube Computational Social Science research module.

Provides CLI interface for channel, video, and recommendation analysis.
"""

import argparse
import logging
from typing import List, Optional
from datetime import datetime
from services.channel_service import ChannelService
from services.video_service import VideoService
from services.recommendation_service import RecommendationService
from persistence.excel_repository import ExcelChannelRepository, ExcelVideoRepository, ExcelCommentRepository, ExcelRecommendationRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize repositories
channel_repo = ExcelChannelRepository()
video_repo = ExcelVideoRepository()
comment_repo = ExcelCommentRepository()
recommendation_repo = ExcelRecommendationRepository()

# Initialize services
channel_service = ChannelService(channel_repo, video_repo, comment_repo)
video_service = VideoService(video_repo, comment_repo)
recommendation_service = RecommendationService(video_repo, recommendation_repo)


def analyze_channel_command(args):
    """Handle channel analysis command."""
    logger.info(f"Analyzing channel: {args.channel_url}")
    
    result = channel_service.analyze_channel(
        channel_url=args.channel_url,
        video_limit=args.video_limit,
        comment_limit=args.comment_limit,
        sampling_strategy=args.sampling_strategy
    )
    
    if result["status"] == "success":
        logger.info(f"Successfully analyzed channel: {result['channel']['title']}")
        logger.info(f"Collection run ID: {result['collection_run_id']}")
        logger.info(f"Videos collected: {result['videos_collected']}")
        logger.info(f"Videos sampled: {result['videos_sampled']}")
        logger.info(f"Total views: {result['analytics']['total_views']}")
        logger.info(f"Total subscribers: {result['analytics']['subscriber_count']}")
    else:
        logger.error(f"Failed to analyze channel: {result['error']}")
    
    return result


def get_channel_analytics_command(args):
    """Handle get channel analytics command."""
    logger.info(f"Getting analytics for channel: {args.channel_id}")
    
    result = channel_service.get_channel_analytics(args.channel_id)
    
    if result["status"] == "success":
        logger.info(f"Channel analytics for: {args.channel_id}")
        logger.info(f"Total videos: {result['analytics']['total_videos']}")
        logger.info(f"Total views: {result['analytics']['total_views']}")
        logger.info(f"Average views per video: {result['analytics']['avg_views_per_video']}")
        logger.info(f"Engagement rate: {result['analytics']['engagement_rate']:.2%}")
    else:
        logger.error(f"Failed to get channel analytics: {result['error']}")
    
    return result


def compare_channels_command(args):
    """Handle compare channels command."""
    logger.info(f"Comparing channels: {args.channel_ids}")
    
    # Parse date range if provided
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date else None
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else None
    period = (start_date, end_date) if start_date and end_date else None
    
    result = channel_service.compare_channels(args.channel_ids, period)
    
    if result["status"] == "success":
        logger.info(f"Successfully compared {result['channels_compared']} channels")
        for channel_id, data in result["comparison"].items():
            logger.info(f"Channel: {data['channel']['title']}")
            logger.info(f"  Total videos: {data['video_count']}")
            logger.info(f"  Total views: {data['analytics']['total_views']}")
            logger.info(f"  Engagement rate: {data['analytics']['engagement_rate']:.2%}")
    else:
        logger.error(f"Failed to compare channels")
    
    return result


def get_channel_upload_pattern_command(args):
    """Handle get channel upload pattern command."""
    logger.info(f"Getting upload pattern for channel: {args.channel_id}")
    
    result = channel_service.get_channel_upload_pattern(args.channel_id)
    
    if result["status"] == "success":
        logger.info(f"Upload pattern for channel: {args.channel_id}")
        logger.info(f"Total videos: {result['total_videos']}")
        logger.info(f"Average gap between uploads: {result['avg_gap_between_uploads_days']:.1f} days")
        logger.info(f"First upload: {result['first_upload']}")
        logger.info(f"Last upload: {result['last_upload']}")
        
        # Show some upload pattern details
        logger.info("Hourly upload distribution:")
        for hour, count in sorted(result["upload_pattern"]["hourly"].items()):
            logger.info(f"  Hour {hour}: {count} videos")
            
        logger.info("Weekly upload distribution:")
        for day, count in result["upload_pattern"]["daily"].items():
            logger.info(f"  {day}: {count} videos")
    else:
        logger.error(f"Failed to get channel upload pattern: {result['error']}")
    
    return result


def analyze_video_command(args):
    """Handle video analysis command."""
    logger.info(f"Analyzing video: {args.video_url}")
    
    result = video_service.analyze_video(
        video_url=args.video_url,
        comment_limit=args.comment_limit,
        collect_recommendations=args.collect_recommendations
    )
    
    if result["status"] == "success":
        logger.info(f"Successfully analyzed video: {result['video']['title']}")
        logger.info(f"Collection run ID: {result['collection_run_id']}")
        logger.info(f"Views: {result['video']['view_count']}")
        logger.info(f"Likes: {result['video']['like_count']}")
        logger.info(f"Comments collected: {result['comments_collected']}")
        logger.info(f"Engagement rate: {result['video_analytics']['engagement_rate']:.2%}")
        logger.info(f"Comment sentiment: {result['comment_analytics']['avg_sentiment']:.2f}")
    else:
        logger.error(f"Failed to analyze video: {result['error']}")
    
    return result


def get_video_analytics_command(args):
    """Handle get video analytics command."""
    logger.info(f"Getting analytics for video: {args.video_id}")
    
    result = video_service.get_video_analytics(args.video_id)
    
    if result["status"] == "success":
        logger.info(f"Video analytics for: {args.video_id}")
        logger.info(f"Views: {result['video_analytics']['view_count']}")
        logger.info(f"Likes: {result['video_analytics']['like_count']}")
        logger.info(f"Engagement rate: {result['video_analytics']['engagement_rate']:.2%}")
        logger.info(f"Comment sentiment: {result['comment_analytics']['avg_sentiment']:.2f}")
        logger.info(f"Comment velocity (first hour): {result['comment_analytics']['comment_velocity_first_hour']}")
    else:
        logger.error(f"Failed to get video analytics: {result['error']}")
    
    return result


def get_video_comment_samples_command(args):
    """Handle get video comment samples command."""
    logger.info(f"Getting comment samples for video: {args.video_id}")
    
    result = video_service.get_video_comment_samples(
        video_id=args.video_id,
        sample_strategy=args.sample_strategy,
        sample_size=args.sample_size
    )
    
    if result["status"] == "success":
        logger.info(f"Comment samples for video: {args.video_id}")
        logger.info(f"Sampling strategy: {result['sample_strategy']}")
        logger.info(f"Sample size: {result['sample_size']}")
        
        for i, comment in enumerate(result["comments"]):
            logger.info(f"Comment {i+1}:")
            logger.info(f"  Text: {comment['text'][:100]}...")
            logger.info(f"  Likes: {comment['like_count']}")
            logger.info(f"  Published: {comment['published_at']}")
            logger.info(f"  Sentiment: {comment.get('sentiment', 0):.2f}")
    else:
        logger.error(f"Failed to get video comment samples: {result['error']}")
    
    return result


def analyze_video_engagement_temporal_command(args):
    """Handle analyze video engagement temporal command."""
    logger.info(f"Analyzing temporal engagement for video: {args.video_id}")
    
    result = video_service.analyze_video_engagement_temporal(args.video_id)
    
    if result["status"] == "success":
        logger.info(f"Temporal engagement analysis for video: {args.video_id}")
        logger.info(f"Total comments: {result['total_comments']}")
        
        logger.info("Comment timing distribution:")
        for time_range, count in result["comment_timing_distribution"].items():
            logger.info(f"  {time_range}: {count} comments")
            
        logger.info("Comment velocity (first 24 hours):")
        for hour, count in sorted([(k, v) for k, v in result["comment_velocity"].items()]):
            logger.info(f"  Hour {hour.replace('hour_', '')}: {count} comments")
    else:
        logger.error(f"Failed to analyze video engagement temporal: {result['error']}")
    
    return result


def compare_videos_command(args):
    """Handle compare videos command."""
    logger.info(f"Comparing videos: {args.video_ids}")
    
    result = video_service.compare_videos(args.video_ids)
    
    if result["status"] == "success":
        logger.info(f"Successfully compared {result['videos_compared']} videos")
        for video_id, data in result["comparison"].items():
            logger.info(f"Video: {data['video']['title']}")
            logger.info(f"  Views: {data['video']['view_count']}")
            logger.info(f"  Likes: {data['video']['like_count']}")
            logger.info(f"  Engagement rate: {data['analytics']['engagement_rate']:.2%}")
            logger.info(f"  Comment sentiment: {data['analytics']['comment_sentiment']:.2f}")
    else:
        logger.error(f"Failed to compare videos")
    
    return result


def analyze_video_recommendations_command(args):
    """Handle analyze video recommendations command."""
    logger.info(f"Analyzing recommendations for video: {args.video_url}")
    
    result = recommendation_service.analyze_video_recommendations(
        video_url=args.video_url,
        depth=args.depth
    )
    
    if result["status"] == "success":
        logger.info(f"Successfully analyzed recommendations for video: {result['source_video']['title']}")
        logger.info(f"Collection run ID: {result['collection_run_id']}")
        logger.info(f"Network nodes: {result['network_stats']['nodes']}")
        logger.info(f"Network edges: {result['network_stats']['edges']}")
        logger.info(f"Network density: {result['network_stats']['density']:.3f}")
        logger.info(f"Average degree: {result['network_stats']['average_degree']:.2f}")
    else:
        logger.error(f"Failed to analyze video recommendations: {result['error']}")
    
    return result


def get_recommendation_network_command(args):
    """Handle get recommendation network command."""
    logger.info(f"Getting recommendation network for video: {args.video_id}")
    
    result = recommendation_service.get_recommendation_network(args.video_id)
    
    if result["status"] == "success":
        logger.info(f"Recommendation network for video: {args.video_id}")
        logger.info(f"Network nodes: {len(result['network']['nodes'])}")
        logger.info(f"Network edges: {len(result['network']['edges'])}")
        logger.info(f"Network density: {result['network']['stats']['density']:.3f}")
        
        # Show some network details
        logger.info("Sample nodes:")
        for node in result["network"]["nodes"][:5]:  # Show first 5 nodes
            logger.info(f"  {node['id']}: {node['title']}")
            
        logger.info("Sample edges:")
        for edge in result["network"]["edges"][:5]:  # Show first 5 edges
            logger.info(f"  {edge['source']} -> {edge['target']} (rank: {edge['rank']})")
    else:
        logger.error(f"Failed to get recommendation network")
    
    return result


def get_recommendation_patterns_command(args):
    """Handle get recommendation patterns command."""
    logger.info(f"Getting recommendation patterns for video: {args.video_id}")
    
    result = recommendation_service.analyze_recommendation_patterns(args.video_id)
    
    if result["status"] == "success":
        logger.info(f"Recommendation patterns for video: {args.video_id}")
        
        logger.info("Top in-degree videos:")
        for video in result["centrality_analysis"]["top_in_degree"]:
            logger.info(f"  {video['video_id']}: {video['score']:.3f}")
            
        logger.info("Top out-degree videos:")
        for video in result["centrality_analysis"]["top_out_degree"]:
            logger.info(f"  {video['video_id']}: {video['score']:.3f}")
            
        logger.info("Network properties:")
        logger.info(f"  Channel diversity: {result['network_properties']['channel_diversity']:.3f}")
        logger.info(f"  Reciprocity: {result['network_properties']['reciprocity']:.3f}")
        logger.info(f"  Density: {result['network_properties']['density']:.3f}")
    else:
        logger.error(f"Failed to get recommendation patterns: {result['error']}")
    
    return result


def get_recommendation_temporal_analysis_command(args):
    """Handle get recommendation temporal analysis command."""
    logger.info(f"Getting temporal analysis for recommendations of video: {args.video_id}")
    
    result = recommendation_service.get_recommendation_temporal_analysis(args.video_id)
    
    if result["status"] == "success":
        logger.info(f"Temporal analysis for recommendations of video: {args.video_id}")
        
        for run_id, data in result["temporal_analysis"].items():
            logger.info(f"Collection run: {run_id}")
            logger.info(f"  Timestamp: {data['timestamp']}")
            logger.info(f"  Nodes: {data['nodes']}")
            logger.info(f"  Edges: {data['edges']}")
            logger.info(f"  Density: {data['density']:.3f}")
    else:
        logger.error(f"Failed to get recommendation temporal analysis: {result['error']}")
    
    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="YouTube Computational Social Science Research Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a channel
  python main.py analyze-channel https://www.youtube.com/@ExampleChannel
  
  # Analyze a video
  python main.py analyze-video https://www.youtube.com/watch?v=examplevideo
  
  # Get recommendation network for a video
  python main.py analyze-recommendations https://www.youtube.com/watch?v=examplevideo
  
  # Compare multiple channels
  python main.py compare-channels channel1 channel2 channel3
  
  # Get channel analytics
  python main.py get-channel-analytics channel123
"""
    )
    
    # Main subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Channel commands
    channel_parser = subparsers.add_parser('analyze-channel', help='Analyze a YouTube channel')
    channel_parser.add_argument('channel_url', help='URL of the YouTube channel to analyze')
    channel_parser.add_argument('--video-limit', type=int, default=100, help='Maximum number of videos to collect')
    channel_parser.add_argument('--comment-limit', type=int, default=1000, help='Maximum number of comments to collect per video')
    channel_parser.add_argument('--sampling-strategy', default='stratified', help='Strategy for sampling videos')
    channel_parser.set_defaults(func=analyze_channel_command)
    
    get_channel_analytics_parser = subparsers.add_parser('get-channel-analytics', help='Get analytics for a channel')
    get_channel_analytics_parser.add_argument('channel_id', help='ID of the channel to get analytics for')
    get_channel_analytics_parser.set_defaults(func=get_channel_analytics_command)
    
    compare_channels_parser = subparsers.add_parser('compare-channels', help='Compare multiple channels')
    compare_channels_parser.add_argument('channel_ids', nargs='+', help='List of channel IDs to compare')
    compare_channels_parser.add_argument('--start-date', help='Start date for comparison period (YYYY-MM-DD)')
    compare_channels_parser.add_argument('--end-date', help='End date for comparison period (YYYY-MM-DD)')
    compare_channels_parser.set_defaults(func=compare_channels_command)
    
    get_upload_pattern_parser = subparsers.add_parser('get-channel-upload-pattern', help='Get upload pattern for a channel')
    get_upload_pattern_parser.add_argument('channel_id', help='ID of the channel to get upload pattern for')
    get_upload_pattern_parser.set_defaults(func=get_channel_upload_pattern_command)
    
    # Video commands
    video_parser = subparsers.add_parser('analyze-video', help='Analyze a YouTube video')
    video_parser.add_argument('video_url', help='URL of the YouTube video to analyze')
    video_parser.add_argument('--comment-limit', type=int, default=1000, help='Maximum number of comments to collect')
    video_parser.add_argument('--collect-recommendations', action='store_true', help='Whether to collect video recommendations')
    video_parser.set_defaults(func=analyze_video_command)
    
    get_video_analytics_parser = subparsers.add_parser('get-video-analytics', help='Get analytics for a video')
    get_video_analytics_parser.add_argument('video_id', help='ID of the video to get analytics for')
    get_video_analytics_parser.set_defaults(func=get_video_analytics_command)
    
    get_comment_samples_parser = subparsers.add_parser('get-video-comment-samples', help='Get comment samples from a video')
    get_comment_samples_parser.add_argument('video_id', help='ID of the video to get comment samples from')
    get_comment_samples_parser.add_argument('--sample-strategy', default='top_likes', help='Sampling strategy for comments')
    get_comment_samples_parser.add_argument('--sample-size', type=int, default=20, help='Number of comments to sample')
    get_comment_samples_parser.set_defaults(func=get_video_comment_samples_command)
    
    analyze_temporal_parser = subparsers.add_parser('analyze-video-engagement-temporal', help='Analyze temporal engagement for a video')
    analyze_temporal_parser.add_argument('video_id', help='ID of the video to analyze temporal engagement for')
    analyze_temporal_parser.set_defaults(func=analyze_video_engagement_temporal_command)
    
    compare_videos_parser = subparsers.add_parser('compare-videos', help='Compare multiple videos')
    compare_videos_parser.add_argument('video_ids', nargs='+', help='List of video IDs to compare')
    compare_videos_parser.set_defaults(func=compare_videos_command)
    
    # Recommendation commands
    recommendation_parser = subparsers.add_parser('analyze-recommendations', help='Analyze recommendations for a video')
    recommendation_parser.add_argument('video_url', help='URL of the YouTube video to analyze recommendations for')
    recommendation_parser.add_argument('--depth', type=int, default=1, help='Depth of recommendation network to collect')
    recommendation_parser.set_defaults(func=analyze_video_recommendations_command)
    
    get_network_parser = subparsers.add_parser('get-recommendation-network', help='Get recommendation network for a video')
    get_network_parser.add_argument('video_id', help='ID of the video to get recommendation network for')
    get_network_parser.set_defaults(func=get_recommendation_network_command)
    
    get_patterns_parser = subparsers.add_parser('get-recommendation-patterns', help='Get recommendation patterns for a video')
    get_patterns_parser.add_argument('video_id', help='ID of the video to get recommendation patterns for')
    get_patterns_parser.set_defaults(func=get_recommendation_patterns_command)
    
    get_temporal_parser = subparsers.add_parser('get-recommendation-temporal-analysis', help='Get temporal analysis for recommendations of a video')
    get_temporal_parser.add_argument('video_id', help='ID of the video to get temporal analysis for')
    get_temporal_parser.set_defaults(func=get_recommendation_temporal_analysis_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute the appropriate function
    try:
        result = args.func(args)
        return result
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    main()