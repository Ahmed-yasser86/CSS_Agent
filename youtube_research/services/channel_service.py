"""Channel service for YouTube research."""

from typing import List, Optional, Dict, Any
from ..domain.models import Channel, Observation, CollectionRun, CollectionStatus
from ..persistence.repository import ChannelRepository
from ..acquisition.youtube_scraper import YouTubeScraper
from ..acquisition.data_extractor import DataExtractor


class ChannelService:
    """Service for channel-related research operations."""
    
    def __init__(
        self,
        channel_repository: ChannelRepository,
        scraper: Optional[YouTubeScraper] = None
    ):
        self.channel_repository = channel_repository
        self.scraper = scraper or YouTubeScraper()
        self.data_extractor = DataExtractor()
    
    def collect_channel(self, channel_url: str) -> Optional[Channel]:
        """
        Collect channel data from YouTube and persist.
        
        Args:
            channel_url: URL of the YouTube channel
            
        Returns:
            Collected Channel or None if collection failed
        """
        # Extract channel info
        raw_data = self.scraper.extract_channel_info(channel_url)
        if not raw_data:
            return None
        
        # Transform to domain model
        channel = self.data_extractor.extract_channel(raw_data)
        if not channel:
            return None
        
        # Save to repository
        self.channel_repository.save(channel)
        
        # Create collection run record
        collection_run = self.scraper.get_collection_run()
        collection_run.source_id = channel.channel_id
        collection_run.status = CollectionStatus.SUCCESS
        
        return channel
    
    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get a channel by ID."""
        return self.channel_repository.get(channel_id)
    
    def list_channels(self, limit: int = 100) -> List[Channel]:
        """List all channels."""
        return self.channel_repository.list(limit)
    
    def channel_exists(self, channel_id: str) -> bool:
        """Check if a channel exists."""
        return self.channel_repository.exists(channel_id)
    
    def update_subscriber_observation(self, channel_id: str) -> Optional[Observation]:
        """
        Update subscriber count observation for historical tracking.
        
        Args:
            channel_id: Channel ID to update
            
        Returns:
            New Observation or None if channel not found
        """
        channel = self.channel_repository.get(channel_id)
        if not channel:
            return None
        
        # Re-scrape to get current subscriber count
        raw_data = self.scraper.extract_channel_info(channel.collection_run_related_urls[0] if channel.collection_run_related_urls else '')
        if not raw_data:
            return None
        
        # Create observation
        observation = self.data_extractor.extract_observation(raw_data, 'subscriber_count')
        if observation:
            observation.source_id = channel_id
            channel.subscriber_count_observations.append(observation)
            self.channel_repository.save(channel)
        
        return observation