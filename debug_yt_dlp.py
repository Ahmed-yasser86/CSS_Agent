"""Debug script to see what yt-dlp returns"""
import sys
sys.path.insert(0, 'C:\\Users\\DELL\\graph-rag-agent')

import yt_dlp

def debug_video_info():
    """Debug what yt-dlp returns for a video"""
    video_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        
        print("Keys in info dict:")
        for key in sorted(info.keys()):
            value = info[key]
            if isinstance(value, list):
                print(f"  {key}: list with {len(value)} items")
                if value and len(value) > 0:
                    if isinstance(value[0], dict):
                        print(f"    First item keys: {list(value[0].keys())[:10]}")
                    else:
                        print(f"    First item: {str(value[0])[:100]}")
            elif isinstance(value, dict):
                print(f"  {key}: dict with keys {list(value.keys())[:10]}")
            else:
                print(f"  {key}: {type(value).__name__} = {str(value)[:100]}")
        
        # Check for related videos
        print("\n\nLooking for related videos...")
        for key in info.keys():
            if 'related' in key.lower() or 'recommend' in key.lower():
                print(f"Found: {key}")
        
        # Check if there's a 'recommendations' field
        if 'recommendations' in info:
            print(f"\nrecommendations: {info['recommendations'][:2] if info['recommendations'] else 'empty'}")
        
        # Check for 'related' field
        if 'related' in info:
            print(f"\nrelated: {info['related'][:2] if info['related'] else 'empty'}")
            
        # Check for 'related_videos' field
        if 'related_videos' in info:
            print(f"\nrelated_videos: {info['related_videos'][:2] if info['related_videos'] else 'empty'}")

if __name__ == '__main__':
    debug_video_info()