"""Test script for YouTube scraper"""
import sys
sys.path.insert(0, 'C:\\Users\\DELL\\graph-rag-agent')

# Direct imports to avoid __init__.py issues
from YouTubeComputationalSocialScience.acquisition.youtube_scraper import YouTubeScraper

def test_video_scraper():
    """Test video info extraction"""
    print("Testing YouTubeScraper...")
    
    scraper = YouTubeScraper()
    scraper.create_collection_run('video', 'dQw4w9WgXcQ', 'https://youtube.com/watch?v=dQw4w9WgXcQ')
    
    # Test video info extraction
    print("Extracting video info...")
    video_info = scraper.extract_video_info('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
    
    if video_info:
        print(f"SUCCESS! Video title: {video_info.get('title', 'N/A')}")
        print(f"Channel: {video_info.get('channel', 'N/A')}")
        print(f"View count: {video_info.get('view_count', 'N/A')}")
        print(f"Like count: {video_info.get('like_count', 'N/A')}")
        print(f"Comment count: {video_info.get('comment_count', 'N/A')}")
    else:
        print("FAILED: Could not extract video info")
    
    print(f"Collection run status: {scraper.collection_run.status.value}")
    print(f"Errors: {scraper.collection_run.errors}")
    
    return video_info is not None

def test_data_extractor():
    """Test data extraction and normalization"""
    print("\nTesting data extractor...")
    
    from YouTubeComputationalSocialScience.acquisition.data_extractor import extract_video_data
    
    # Sample yt-dlp result
    sample_video = {
        'id': 'dQw4w9WgXcQ',
        'title': 'Test Video',
        'description': 'Test description',
        'upload_date': '20240101',
        'duration': 212,
        'channel_id': 'UCuAXFkgsw1L7xaCfnd5JJOw',
        'channel': 'Test Channel',
        'view_count': 1000000,
        'like_count': 50000,
        'comment_count': 10000,
        'webpage_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'tags': ['test', 'sample'],
        'categories': ['Music'],
        'language': 'en'
    }
    
    try:
        video = extract_video_data(sample_video, 'test-run-123', 'UCuAXFkgsw1L7xaCfnd5JJOw')
        print(f"SUCCESS! Extracted video: {video.title}")
        print(f"Video ID: {video.video_id}")
        print(f"Channel ID: {video.channel_id}")
        print(f"View count: {video.view_count}")
        print(f"Engagement rate: {video.engagement_rate}")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Computational Social Science - Integration Test")
    print("=" * 60)
    
    success = True
    success &= test_video_scraper()
    success &= test_data_extractor()
    
    print("\n" + "=" * 60)
    if success:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("=" * 60)