"""Recommendation service for YouTube research and network analysis."""

from typing import List, Optional, Dict, Any
import networkx as nx
from ..domain.models import Video, CollectionRun, CollectionStatus
from ..persistence.repository import VideoRepository
from ..acquisition.youtube_scraper import YouTubeScraper
from ..acquisition.data_extractor import DataExtractor


class RecommendationService:
    """Service for video recommendation/feed analysis and network construction."""
    
    def __init__(
        self,
        video_repository: VideoRepository,
        scraper: Optional[YouTubeScraper] = None
    ):
        self.video_repository = video_repository
        self.scraper = scraper or YouTubeScraper()
        self.data_extractor = DataExtractor()
        self._recommendation_graph = None
    
    def collect_recommendations(
        self, 
        video_url: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Collect recommended videos from a video page.
        
        Args:
            video_url: URL of the source video
            limit: Maximum number of recommendations to collect
            
        Returns:
            List of recommendation relationship dictionaries
        """
        source_video_id = video_url.split('/')[-1].split('?')[0]
        
        # Extract recommendations
        raw_recommendations = self.scraper.extract_video_recommendations(video_url, limit)
        
        relationships = []
        for raw_rec in raw_recommendations:
            relationship = self.data_extractor.extract_recommendation_relationship(
                source_video_id, raw_rec
            )
            if relationship:
                relationships.append(relationship)
        
        # Update collection run
        collection_run = self.scraper.get_collection_run()
        collection_run.source_id = source_video_id
        collection_run.recommendations_collected = len(relationships)
        collection_run.status = CollectionStatus.SUCCESS
        
        return relationships
    
    def build_recommendation_graph(self) -> nx.DiGraph:
        """
        Build a directed graph of video recommendations.
        
        Nodes: Videos
        Edges: Recommendation relationships (source -> target)
        
        Returns:
            NetworkX directed graph of recommendations
        """
        self._recommendation_graph = nx.DiGraph()
        
        # Get all videos and build graph from stored recommendations
        videos = self.video_repository.list(limit=10000)
        
        for video in videos:
            if not self._recommendation_graph.has_node(video.video_id):
                self._recommendation_graph.add_node(
                    video.video_id,
                    title=video.title,
                    channel_id=video.channel_id,
                    view_count=video.view_count
                )
        
        return self._recommendation_graph
    
    def get_recommendation_graph(self) -> nx.DiGraph:
        """Get the current recommendation graph, building if needed."""
        if self._recommendation_graph is None:
            self._recommendation_graph = self.build_recommendation_graph()
        return self._recommendation_graph
    
    def add_recommendation_edge(
        self, 
        source_video_id: str, 
        target_video_id: str,
        target_title: str = '',
        target_channel: str = ''
    ) -> None:
        """
        Add a recommendation edge to the graph.
        
        Args:
            source_video_id: Source video ID
            target_video_id: Target video ID
            target_title: Title of target video
            target_channel: Channel of target video
        """
        graph = self.get_recommendation_graph()
        
        if not graph.has_node(source_video_id):
            graph.add_node(source_video_id)
        
        if not graph.has_node(target_video_id):
            graph.add_node(target_video_id, title=target_title, channel=target_channel)
        
        graph.add_edge(source_video_id, target_video_id, relationship='recommendation')
    
    def get_video_recommendations(self, video_id: str) -> List[str]:
        """
        Get video IDs recommended after the given video.
        
        Args:
            video_id: Source video ID
            
        Returns:
            List of recommended video IDs
        """
        graph = self.get_recommendation_graph()
        if graph.has_node(video_id):
            return list(graph.successors(video_id))
        return []
    
    def get_video_referrers(self, video_id: str) -> List[str]:
        """
        Get video IDs that recommend the given video.
        
        Args:
            video_id: Target video ID
            
        Returns:
            List of source video IDs
        """
        graph = self.get_recommendation_graph()
        if graph.has_node(video_id):
            return list(graph.predecessors(video_id))
        return []
    
    def calculate_network_metrics(self, video_id: str) -> Dict[str, Any]:
        """
        Calculate network metrics for a video.
        
        Args:
            video_id: Video ID to analyze
            
        Returns:
            Dictionary with network metrics
        """
        graph = self.get_recommendation_graph()
        
        if not graph.has_node(video_id):
            return {}
        
        metrics = {
            'in_degree': graph.in_degree(video_id),
            'out_degree': graph.out_degree(video_id),
            'in_recommendations': self.get_video_referrers(video_id),
            'out_recommendations': self.get_video_recommendations(video_id),
        }
        
        # Calculate PageRank if graph is large enough
        if graph.number_of_nodes() > 10:
            pagerank = nx.pagerank(graph)
            metrics['pagerank'] = pagerank.get(video_id, 0)
        
        return metrics