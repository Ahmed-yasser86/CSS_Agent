"""Test script for youtube_research scraper"""
import sys
sys.path.insert(0, 'C:\\Users\\DELL\\graph-rag-agent')

# Direct imports to avoid __init__.py issues
from youtube_research.acquisition.youtube_scraper import YouTubeScraper

def test_video_scraper():
    """Test video info extraction"""
    print("Testing YouTubeScraper (youtube_research)...")
    
    scraper = YouTubeScraper()
    scraper.create_collection_run('video', 'dQw4w9WgXcQ', 'https://youtube.com/watch?v=dQw4w9WgXcQ')
    
    # Test video info extraction
    print("Extracting video info...")
    video_info = scraper.extract_video_info('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
    
    if video_info:
        print(f"SUCCESS! Video title: {video_info.get('title', 'N/A')}")
        print(f"Channel: {video_info.get('channel', 'N/A')}")
        print(f"View count: {video_info.get('view_count', 'N/A')}")
    else:
        print("FAILED: Could not extract video info")
    
    print(f"Collection run status: {scraper.collection_run.status.value}")
    print(f"Errors: {scraper.collection_run.errors}")
    
    return video_info is not None

def test_data_extractor():
    """Test data extraction and normalization"""
    print("\nTesting data extractor...")
    
    from youtube_research.acquisition.data_extractor import DataExtractor
    
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
    }
    
    try:
        video = DataExtractor.extract_video(sample_video)
        if video:
            print(f"SUCCESS! Extracted video: {video.title}")
            print(f"Video ID: {video.video_id}")
            print(f"Channel ID: {video.channel_id}")
            print(f"View count: {video.view_count}")
            print(f"Engagement rate: {video.engagement_rate}")
            return True
        else:
            print("FAILED: DataExtractor.extract_video returned None")
            return False
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Research - Integration Test")
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