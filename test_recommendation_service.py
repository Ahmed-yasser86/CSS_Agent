"""Test script for recommendation service"""
import sys
sys.path.insert(0, 'C:\\Users\\DELL\\graph-rag-agent')

# Direct imports to avoid __init__.py issues
from YouTubeComputationalSocialScience.acquisition.youtube_scraper import YouTubeScraper
from YouTubeComputationalSocialScience.acquisition.data_extractor import extract_video_data, extract_recommendation_data

def test_recommendation_extraction():
    """Test recommendation extraction"""
    print("Testing recommendation extraction...")
    
    scraper = YouTubeScraper()
    scraper.create_collection_run('video', 'dQw4w9WgXcQ', 'https://youtube.com/watch?v=dQw4w9WgXcQ')
    
    # Test video info extraction
    print("Extracting video info...")
    video_info = scraper.extract_video_info('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
    
    if not video_info:
        print("FAILED: Could not extract video info")
        return False
    
    print(f"Video: {video_info.get('title')}")
    
    # Test recommendations extraction
    print("\nExtracting recommendations...")
    recommendations = scraper.extract_video_recommendations('https://www.youtube.com/watch?v=dQw4w9WgXcQ', limit=5)
    
    print(f"Found {len(recommendations)} recommendations")
    
    for i, rec in enumerate(recommendations[:3]):
        print(f"  {i+1}. {rec.get('title', 'N/A')} (channel: {rec.get('channel', 'N/A')})")
    
    # Test data extraction
    print("\nTesting recommendation data extraction...")
    if recommendations:
        rec_data = recommendations[0]
        recommendation = extract_recommendation_data(rec_data, 'test-run-123', 'dQw4w9WgXcQ')
        print(f"Extracted recommendation:")
        print(f"  Source video: {recommendation.source_video_id}")
        print(f"  Recommended video: {recommendation.recommended_video_id}")
        print(f"  Title: {recommendation.recommended_video_title}")
        print(f"  URL: {recommendation.recommended_video_url}")
    
    return True

def test_networkx():
    """Test networkx integration"""
    print("\nTesting networkx integration...")
    
    import networkx as nx
    
    # Create a simple graph
    G = nx.DiGraph()
    G.add_edge('A', 'B')
    G.add_edge('B', 'C')
    G.add_edge('A', 'C')
    
    print(f"Nodes: {list(G.nodes())}")
    print(f"Edges: {list(G.edges())}")
    print(f"Density: {nx.density(G)}")
    print(f"Average degree: {sum(dict(G.degree()).values()) / G.number_of_nodes()}")
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("Recommendation Service - Integration Test")
    print("=" * 60)
    
    success = True
    success &= test_recommendation_extraction()
    success &= test_networkx()
    
    print("\n" + "=" * 60)
    if success:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("=" * 60)