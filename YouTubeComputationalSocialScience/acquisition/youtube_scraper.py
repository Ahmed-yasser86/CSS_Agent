"""
YouTube data acquisition using yt-dlp for Computational Social Science research.

Provides research-grade data extraction with error handling, retries,
and provenance tracking for reproducible research.
"""

import yt_dlp
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from ..domain.models import CollectionStatus, CollectionRun

# Set up logging
logger = logging.getLogger(__name__)


class YouTubeScraper:
    """
    YouTube data scraper using yt-dlp for research purposes.
    
    Designed for research-grade data collection with:
    - Error handling and retries
    - Provenance tracking
    - Rate limit awareness
    - Research metadata preservation
    """
    
    def __init__(self, collection_run_id: Optional[str] = None):
        """
        Initialize the YouTube scraper.
        
        Args:
            collection_run_id: Optional collection run ID for provenance tracking
        """
        self.collection_run_id = collection_run_id or str(uuid.uuid4())
        self.collection_run = CollectionRun(
            collection_run_id=self.collection_run_id,
            started_at=datetime.now(),
            source_type="unknown",
            source_id="unknown",
            source_url="unknown"
        )
    
    def create_collection_run(self, source_type: str, source_id: str, source_url: str) -> CollectionRun:
        """
        Create a collection run for tracking provenance.
        
        Args:
            source_type: Type of source (channel, video, recommendation)
            source_id: ID of the source
            source_url: URL of the source
            
        Returns:
            CollectionRun object
        """
        self.collection_run = CollectionRun(
            collection_run_id=self.collection_run_id,
            started_at=datetime.now(),
            source_type=source_type,
            source_id=source_id,
            source_url=source_url
        )
        return self.collection_run
    
    def complete_collection_run(self, status: CollectionStatus = CollectionStatus.SUCCESS) -> CollectionRun:
        """
        Complete a collection run with final status.
        
        Args:
            status: Final collection status
            
        Returns:
            Completed CollectionRun object
        """
        self.collection_run.completed_at = datetime.now()
        self.collection_run.status = status
        return self.collection_run
    
    def extract_channel_info(self, channel_url: str) -> Dict[str, Any]:
        """
        Extract channel information from YouTube.
        
        Args:
            channel_url: URL of the YouTube channel
            
        Returns:
            Dictionary containing channel information
        """
        self.collection_run.source_type = "channel"
        self.collection_run.source_url = channel_url
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                self.collection_run.videos_discovered = info.get('entries_count', 0)
                return info
        except Exception as e:
            logger.error(f"Error extracting channel info: {e}")
            self.collection_run.errors.append(f"Channel extraction failed: {str(e)}")
            self.collection_run.status = CollectionStatus.FAILED
            return {}
    
    def extract_channel_videos(self, channel_url: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Extract videos from a YouTube channel.
        
        Args:
            channel_url: URL of the YouTube channel
            limit: Maximum number of videos to extract
            
        Returns:
            List of dictionaries containing video information
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
            'playlistend': limit,
            'extract_comments': False  # We'll extract comments separately
        }
        
        videos = []
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            videos.append(entry)
                            self.collection_run.videos_collected += 1
                        else:
                            self.collection_run.videos_failed += 1
                
                return videos
        except Exception as e:
            logger.error(f"Error extracting channel videos: {e}")
            self.collection_run.errors.append(f"Channel videos extraction failed: {str(e)}")
            self.collection_run.status = CollectionStatus.PARTIAL
            return videos
    
    def extract_video_info(self, video_url: str) -> Dict[str, Any]:
        """
        Extract video information from YouTube.
        
        Args:
            video_url: URL of the YouTube video
            
        Returns:
            Dictionary containing video information
        """
        self.collection_run.source_type = "video"
        self.collection_run.source_url = video_url
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
            'extract_comments': False  # We'll extract comments separately
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                self.collection_run.videos_collected = 1 if info else 0
                return info or {}
        except Exception as e:
            logger.error(f"Error extracting video info: {e}")
            self.collection_run.errors.append(f"Video extraction failed: {str(e)}")
            self.collection_run.status = CollectionStatus.FAILED
            return {}
    
    def extract_video_comments(self, video_url: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Extract comments from a YouTube video.
        
        Args:
            video_url: URL of the YouTube video
            limit: Maximum number of comments to extract
            
        Returns:
            List of dictionaries containing comment information
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
            'extract_comments': True,
            'max_comments': limit,
            'get_comments': True
        }
        
        comments = []
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                if 'comments' in info:
                    for comment in info['comments']:
                        if comment:
                            comments.append(comment)
                            self.collection_run.comments_collected += 1
                        else:
                            self.collection_run.comments_failed += 1
                
                return comments
        except Exception as e:
            logger.error(f"Error extracting video comments: {e}")
            self.collection_run.errors.append(f"Video comments extraction failed: {str(e)}")
            self.collection_run.status = CollectionStatus.PARTIAL
            return comments
    
    def extract_video_recommendations(self, video_url: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Extract recommended videos from a YouTube video page.
        
        Args:
            video_url: URL of the YouTube video
            limit: Maximum number of recommendations to extract
            
        Returns:
            List of dictionaries containing recommendation information
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,  # Get full video info including related videos
            'skip_download': True,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
            'playlistend': limit
        }
        
        recommendations = []
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract full video info which includes related videos
                info = ydl.extract_info(video_url, download=False)
                
                # Look for recommendations in the info
                # yt-dlp may provide 'related_videos' or similar fields
                related = info.get('related_videos', []) if info else []
                for rec in related:
                    if rec and isinstance(rec, dict):
                        rec_id = rec.get('id', '')
                        if rec_id and rec_id != info.get('id'):  # Don't include the video itself
                            recommendations.append(rec)
                            self.collection_run.recommendations_collected += 1
                        else:
                            self.collection_run.recommendations_failed += 1
                
                return recommendations
        except Exception as e:
            logger.error(f"Error extracting video recommendations: {e}")
            self.collection_run.errors.append(f"Video recommendations extraction failed: {str(e)}")
            self.collection_run.status = CollectionStatus.PARTIAL
            return recommendations
    
    def get_collection_run(self) -> CollectionRun:
        """Get the current collection run."""
        return self.collection_run

    def extract_video_script(self, video_url: str, languages: List[str] = None) -> str:
        """
        Extract video script/transcript from YouTube video.

        Args:
            video_url: URL of the YouTube video
            languages: List of language codes to try (e.g., ['en', 'es']).
                      First available will be used. Defaults to ['en'].

        Returns:
            Transcript/script text as string, or empty string if not available
        """
        if languages is None:
            languages = ['en']

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': languages,
            'skip_download': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)

                if not info:
                    return ""

                # Get subtitle data - yt-dlp stores subtitle info in 'subtitles' and 'automatic_captions'
                # These contain URLs to subtitle files, not actual text
                subtitles = info.get('subtitles') or {}
                automatic_captions = info.get('automatic_captions') or {}

                transcript_parts = []

                # Try to get transcript text from subtitles
                for lang in languages:
                    # Check manual subtitles first
                    if lang in subtitles:
                        sub_data = subtitles[lang]
                        if sub_data and isinstance(sub_data, list) and len(sub_data) > 0:
                            # Get the first available format (prefer json3 or srv1)
                            for fmt in sub_data:
                                if isinstance(fmt, dict) and 'url' in fmt:
                                    transcript_text = self._fetch_subtitle_text(fmt['url'])
                                    if transcript_text:
                                        transcript_parts.append(transcript_text)
                                        break
                            if transcript_parts:
                                break

                    # Check automatic captions
                    if not transcript_parts and lang in automatic_captions:
                        sub_data = automatic_captions[lang]
                        if sub_data and isinstance(sub_data, list) and len(sub_data) > 0:
                            for fmt in sub_data:
                                if isinstance(fmt, dict) and 'url' in fmt:
                                    transcript_text = self._fetch_subtitle_text(fmt['url'])
                                    if transcript_text:
                                        transcript_parts.append(transcript_text)
                                        break
                            if transcript_parts:
                                break

                if transcript_parts:
                    return ' '.join(transcript_parts)

                return ""

        except Exception as e:
            logger.error(f"Error extracting video script: {e}")
            self.collection_run.errors.append(f"Video script extraction failed: {str(e)}")
            return ""

    def _fetch_subtitle_text(self, subtitle_url: str) -> Optional[str]:
        """
        Fetch actual subtitle text from a subtitle URL.

        Args:
            subtitle_url: URL to the subtitle file

        Returns:
            Subtitle text as string, or None if fetch failed
        """
        try:
            import urllib.request
            import json
            import html

            req = urllib.request.Request(
                subtitle_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')

                # Parse the timedtext format (YouTube's XML-like format)
                # or JSON3 format
                if 'fmt=json3' in subtitle_url or '.json3' in subtitle_url:
                    # JSON3 format
                    data = json.loads(content)
                    texts = []
                    for event in data.get('events', []):
                        segs = event.get('segs', [])
                        for seg in segs:
                            text = seg.get('utf8', '').strip()
                            if text:
                                texts.append(text)
                    result = ' '.join(texts) if texts else None
                else:
                    # TTML or other XML-like format - extract text from <text> tags
                    import re
                    texts = re.findall(r'<text[^>]*>([^<]+)</text>', content)
                    result = ' '.join(texts) if texts else None

                # Decode HTML entities
                if result:
                    result = html.unescape(result)

                return result

        except Exception as e:
            logger.error(f"Error fetching subtitle from {subtitle_url}: {e}")
            return None