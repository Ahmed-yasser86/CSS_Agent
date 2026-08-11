"""
Recommendation network analysis service for YouTube Computational Social Science research.

Orchestrates the recommendation network analysis workflow including data acquisition,
persistence, network analysis, and research output generation.
"""

import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import networkx as nx
from ..domain.models import Video, Recommendation, CollectionRun, CollectionStatus, RecommendationNetwork
from ..acquisition.youtube_scraper import YouTubeScraper
from ..acquisition.data_extractor import extract_recommendation_data, extract_video_data
from ..persistence.repository import VideoRepository, RecommendationRepository


class RecommendationService:
    """
    Service for YouTube recommendation network analysis.
    
    Orchestrates the complete recommendation analysis pipeline from data acquisition
    to network analysis and research output generation.
    """
    
    def __init__(self, 
                 video_repository: VideoRepository,
                 recommendation_repository: RecommendationRepository):
        """
        Initialize the recommendation service.
        
        Args:
            video_repository: Repository for video persistence
            recommendation_repository: Repository for recommendation persistence
        """
        self.video_repository = video_repository
        self.recommendation_repository = recommendation_repository
    
    def analyze_video_recommendations(self, video_url: str, depth: int = 1) -> Dict[str, Any]:
        """
        Analyze the recommendation network for a YouTube video.
        
        Args:
            video_url: URL of the YouTube video to analyze
            depth: Depth of recommendation network to collect (1 = direct recommendations only)
            
        Returns:
            Dictionary containing analysis results and metadata
        """
        # Create collection run
        collection_run_id = str(uuid.uuid4())
        scraper = YouTubeScraper(collection_run_id)
        scraper.create_collection_run("recommendation", video_url.split('/')[-1], video_url)
        
        try:
            # Step 1: Extract source video metadata
            video_info = scraper.extract_video_info(video_url)
            if not video_info:
                return {"status": "failed", "error": "Could not extract video info", "collection_run_id": collection_run_id}
            
            # Step 2: Normalize and save source video
            source_video = extract_video_data(video_info, collection_run_id, video_info.get('channel_id', ''))
            self.video_repository.save_video(source_video)
            
            # Step 3: Extract and save recommendations
            self._collect_recommendation_network(scraper, source_video, depth)
            
            # Step 4: Build and analyze network
            network = self._build_recommendation_network(source_video.video_id)
            
            # Complete collection run
            scraper.complete_collection_run()
            
            return {
                "status": "success",
                "collection_run_id": collection_run_id,
                "source_video": source_video.model_dump(),
                "network_stats": network.stats,
                "collection_run": scraper.get_collection_run().model_dump()
            }
            
        except Exception as e:
            # Mark collection as failed
            scraper.complete_collection_run(CollectionStatus.FAILED)
            return {
                "status": "failed",
                "error": str(e),
                "collection_run_id": collection_run_id,
                "collection_run": scraper.get_collection_run().model_dump()
            }
    
    def _collect_recommendation_network(self, scraper: YouTubeScraper, source_video: Video, depth: int):
        """Collect the recommendation network starting from a source video."""
        from collections import deque
        
        # Use BFS to collect recommendations up to specified depth
        queue = deque([(source_video, 0)])
        visited = set([source_video.video_id])
        
        while queue:
            current_video, current_depth = queue.popleft()
            
            # Stop if we've reached the desired depth
            if current_depth >= depth:
                continue
            
            try:
                # Extract recommendations for current video
                recommendations_data = scraper.extract_video_recommendations(current_video.url)
                
                for rec_data in recommendations_data:
                    try:
                        # Save recommendation relationship
                        recommendation = extract_recommendation_data(
                            rec_data, 
                            scraper.collection_run_id, 
                            current_video.video_id
                        )
                        self.recommendation_repository.save_recommendation(recommendation)
                        
                        # Save recommended video if not already saved
                        if recommendation.recommended_video_id not in visited:
                            recommended_video_info = scraper.extract_video_info(recommendation.recommended_video_url)
                            if recommended_video_info:
                                recommended_video = extract_video_data(
                                    recommended_video_info, 
                                    scraper.collection_run_id, 
                                    recommended_video_info.get('channel_id', '')
                                )
                                self.video_repository.save_video(recommended_video)
                                visited.add(recommended_video.video_id)
                                queue.append((recommended_video, current_depth + 1))
                                
                    except Exception as e:
                        scraper.collection_run.errors.append(f"Recommendation extraction failed: {str(e)}")
                        scraper.collection_run.recommendations_failed += 1
                        continue
                        
            except Exception as e:
                scraper.collection_run.errors.append(f"Recommendations for video {current_video.video_id} failed: {str(e)}")
                continue
    
    def _build_recommendation_network(self, source_video_id: str) -> RecommendationNetwork:
        """Build a network graph from collected recommendations."""
        # Get all recommendations involving the source video
        recommendations = self.recommendation_repository.get_video_recommendations(source_video_id)
        
        # Create a directed graph
        graph = nx.DiGraph()
        
        # Add nodes and edges
        for rec in recommendations:
            # Add source node
            graph.add_node(rec.source_video_id, 
                          title=rec.source_video_title,
                          channel_id=rec.source_channel_id,
                          channel_title=rec.source_channel_title)
            
            # Add recommended node
            graph.add_node(rec.recommended_video_id, 
                          title=rec.recommended_video_title,
                          channel_id=rec.recommended_channel_id,
                          channel_title=rec.recommended_channel_title)
            
            # Add edge with recommendation data
            graph.add_edge(rec.source_video_id, rec.recommended_video_id, 
                          rank=rec.rank,
                          position=rec.position,
                          collection_run_id=rec.collection_run_id)
        
        # Calculate network statistics
        num_nodes = graph.number_of_nodes()
        num_edges = graph.number_of_edges()
        density = nx.density(graph) if num_nodes > 1 else 0.0
        avg_degree = sum(dict(graph.degree()).values()) / num_nodes if num_nodes > 0 else 0.0
        
        stats = {
            "nodes": num_nodes,
            "edges": num_edges,
            "density": density,
            "average_degree": avg_degree,
            "is_strongly_connected": nx.is_strongly_connected(graph) if num_nodes > 0 else False,
            "strongly_connected_components": nx.number_strongly_connected_components(graph) if num_nodes > 0 else 0,
            "average_clustering": nx.average_clustering(graph.to_undirected()) if num_nodes > 0 else 0.0
        }
        
        return RecommendationNetwork(
            network_id=str(uuid.uuid4()),
            source_video_id=source_video_id,
            collection_run_id=str(uuid.uuid4()),
            nodes=list(graph.nodes()),
            edges=[{"source": u, "target": v, **d} for u, v, d in graph.edges(data=True)],
            network_size=num_nodes,
            network_density=density,
            average_degree=avg_degree,
            observed_at=datetime.now(),
            graph=graph,
            stats=stats
        )
    
    def get_recommendation_network(self, video_id: str) -> Dict[str, Any]:
        """
        Get the recommendation network for a video.
        
        Args:
            video_id: ID of the source video
            
        Returns:
            Dictionary containing network data and statistics
        """
        network = self._build_recommendation_network(video_id)
        
        # Convert graph to serializable format
        nodes = []
        for node_id, node_data in network.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "title": node_data.get('title', ''),
                "channel_id": node_data.get('channel_id', ''),
                "channel_title": node_data.get('channel_title', '')
            })
        
        edges = []
        for source, target, edge_data in network.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "rank": edge_data.get('rank', 0),
                "position": edge_data.get('position', 'unknown')
            })
        
        return {
            "status": "success",
            "video_id": video_id,
            "network": {
                "nodes": nodes,
                "edges": edges,
                "stats": network.stats
            }
        }
    
    def analyze_recommendation_patterns(self, video_id: str) -> Dict[str, Any]:
        """
        Analyze patterns in the recommendation network.
        
        Args:
            video_id: ID of the source video
            
        Returns:
            Dictionary containing pattern analysis
        """
        network = self._build_recommendation_network(video_id)
        graph = network.graph
        
        if graph.number_of_nodes() == 0:
            return {"status": "no_data", "error": "No recommendation network found"}
        
        # Calculate centrality measures
        in_degree_centrality = nx.in_degree_centrality(graph)
        out_degree_centrality = nx.out_degree_centrality(graph)
        betweenness_centrality = nx.betweenness_centrality(graph)
        
        # Find most central videos
        top_in_degree = sorted(in_degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        top_out_degree = sorted(out_degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        top_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Calculate channel diversity
        channel_videos = {}
        for node_id, node_data in graph.nodes(data=True):
            channel_id = node_data.get('channel_id', 'unknown')
            channel_videos[channel_id] = channel_videos.get(channel_id, 0) + 1
        
        channel_diversity = len(channel_videos) / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0
        
        # Calculate reciprocity
        reciprocity = nx.reciprocity(graph)
        
        return {
            "status": "success",
            "video_id": video_id,
            "centrality_analysis": {
                "top_in_degree": [{"video_id": vid, "score": score} for vid, score in top_in_degree],
                "top_out_degree": [{"video_id": vid, "score": score} for vid, score in top_out_degree],
                "top_betweenness": [{"video_id": vid, "score": score} for vid, score in top_betweenness]
            },
            "network_properties": {
                "channel_diversity": channel_diversity,
                "reciprocity": reciprocity,
                "density": network.stats["density"]
            }
        }
    
    def get_recommendation_temporal_analysis(self, video_id: str) -> Dict[str, Any]:
        """
        Analyze how recommendation patterns change over time.
        
        Args:
            video_id: ID of the source video
            
        Returns:
            Dictionary containing temporal analysis
        """
        # Get all collection runs for this video
        collection_runs = self.recommendation_repository.get_collection_runs_for_video(video_id)
        
        if not collection_runs:
            return {"status": "no_data", "error": "No collection runs found for video"}
        
        # Group recommendations by collection run
        temporal_data = {}
        for run in collection_runs:
            recommendations = self.recommendation_repository.get_recommendations_by_run(run.collection_run_id)
            
            # Build network for this run
            graph = nx.DiGraph()
            for rec in recommendations:
                graph.add_node(rec.source_video_id)
                graph.add_node(rec.recommended_video_id)
                graph.add_edge(rec.source_video_id, rec.recommended_video_id)
            
            # Store network stats for this run
            temporal_data[run.collection_run_id] = {
                "timestamp": run.collection_time.isoformat(),
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
                "density": nx.density(graph),
                "collection_run": run.model_dump()
            }
        
        return {
            "status": "success",
            "video_id": video_id,
            "temporal_analysis": temporal_data
        }