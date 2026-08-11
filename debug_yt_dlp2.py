"""Debug script to see if player_client helps get recommendations"""
import sys
sys.path.insert(0, 'C:\\Users\\DELL\\graph-rag-agent')

import yt_dlp

def debug_with_player_client():
    """Debug with different player_client"""
    video_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    
    # Try with android client which sometimes returns more data
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
        'player_client': 'android',
    }
    
    print("Testing with player_client=android...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        
        print(f"Keys: {sorted(info.keys())}")
        print(f"\nNumber of keys: {len(info.keys())}")
        
        # Check for related
        for key in ['related', 'related_videos', 'recommendations']:
            if key in info:
                val = info[key]
                if isinstance(val, list):
                    print(f"\n{key}: list with {len(val)} items")
                    if val:
                        print(f"  First item type: {type(val[0])}")
                        if isinstance(val[0], dict):
                            print(f"  First item keys: {list(val[0].keys())}")
                else:
                    print(f"\n{key}: {type(val)}")

def debug_player_response():
    """Try to get player response directly"""
    video_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
        'getplayerconfig': True,
    }
    
    print("\n\nTesting with getplayerconfig=True...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            if 'player_config' in info:
                print("player_config found!")
                config = info['player_config']
                if isinstance(config, dict):
                    print(f"player_config keys: {list(config.keys())}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    debug_with_player_client()
    debug_player_response()