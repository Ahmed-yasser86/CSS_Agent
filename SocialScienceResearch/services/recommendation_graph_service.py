"""Recommendation-network analysis over observed recommendation edges.

The recommendation repository stores *observed* relationships
(source video -> recommended video). This service loads those edges into a
directed :class:`networkx.DiGraph` and computes network metrics (degrees,
PageRank, hubs, reachable contexts) for the recommendation ecosystem.

The graph is rebuilt on demand from persisted observations - nothing is
fabricated, and edges are attributed to the run (or run set) that observed
them, so temporal network slices are possible (``run_id``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from SocialScienceResearch.persistence.base import Repositories


@dataclass
class NetworkSummary:
    """Aggregate metrics over a recommendation network slice."""

    node_count: int = 0
    edge_count: int = 0
    source_count: int = 0
    target_count: int = 0
    most_recommended: list[dict[str, Any]] = field(default_factory=list)
    most_active_sources: list[dict[str, Any]] = field(default_factory=list)
    highest_pagerank: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class VideoNetworkContext:
    """Ego-network view for one video."""

    video_id: str
    in_degree: int = 0
    out_degree: int = 0
    pagerank: float | None = None
    recommended_by: list[dict[str, Any]] = field(default_factory=list)
    recommends: list[dict[str, Any]] = field(default_factory=list)


class RecommendationGraphService:
    """Builds and analyzes the recommendation graph from stored edges."""

    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    # ------------------------------------------------------------------
    def build_graph(self, run_id: str | None = None) -> nx.DiGraph:
        """Build a directed graph from observed recommendation edges."""
        edges = self._repos.recommendations.list_recommendation_edges(run_id=run_id)
        graph = nx.DiGraph()
        for edge in edges:
            graph.add_edge(
                edge.source_video_id,
                edge.recommended_video_id,
                position=edge.position,
                run_id=edge.collection_run_id,
                title=edge.title,
            )
        return graph

    # ------------------------------------------------------------------
    def summary(self, run_id: str | None = None, top_n: int = 10) -> NetworkSummary:
        """Compute aggregate metrics for a network slice."""
        graph = self.build_graph(run_id)
        if graph.number_of_nodes() == 0:
            return NetworkSummary()

        in_degree = dict(graph.in_degree())
        out_degree = dict(graph.out_degree())
        pagerank = nx.pagerank(graph)

        most_recommended = sorted(
            in_degree.items(), key=lambda item: item[1], reverse=True
        )[:top_n]
        most_active = sorted(
            out_degree.items(), key=lambda item: item[1], reverse=True
        )[:top_n]
        top_rank = sorted(
            pagerank.items(), key=lambda item: item[1], reverse=True
        )[:top_n]

        return NetworkSummary(
            node_count=graph.number_of_nodes(),
            edge_count=graph.number_of_edges(),
            source_count=sum(1 for d in out_degree.values() if d > 0),
            target_count=sum(1 for d in in_degree.values() if d > 0),
            most_recommended=[
                {"video_id": video, "times_recommended": count}
                for video, count in most_recommended
            ],
            most_active_sources=[
                {"video_id": video, "outgoing": count}
                for video, count in most_active
            ],
            highest_pagerank=[
                {"video_id": video, "pagerank": round(rank, 6)}
                for video, rank in top_rank
            ],
        )

    # ------------------------------------------------------------------
    def video_context(
        self, video_id: str, run_id: str | None = None, top_n: int = 50
    ) -> VideoNetworkContext:
        """Ego-network context for one video (who recommends it, whom it recommends)."""
        graph = self.build_graph(run_id)
        context = VideoNetworkContext(video_id=video_id)

        if graph.number_of_nodes() == 0:
            return context

        context.in_degree = int(graph.in_degree(video_id))
        context.out_degree = int(graph.out_degree(video_id))
        context.pagerank = round(float(nx.pagerank(graph).get(video_id, 0.0)), 6)

        for source, _, data in graph.in_edges(video_id, data=True):
            context.recommended_by.append(
                {
                    "source_video_id": source,
                    "position": data.get("position"),
                    "run_id": data.get("run_id"),
                    "title": data.get("title"),
                }
            )
        for _, target, data in graph.out_edges(video_id, data=True):
            context.recommends.append(
                {
                    "recommended_video_id": target,
                    "position": data.get("position"),
                    "run_id": data.get("run_id"),
                    "title": data.get("title"),
                }
            )
        # Feed-rank ordering: position is the slot a recommendation occupied in
        # the source's "Up Next" rail, so the observed rail order (ranked items
        # first, unranked last) is the canonical display order everywhere.
        context.recommended_by = self._by_feed_rank(
            context.recommended_by, "source_video_id"
        )
        context.recommends = self._by_feed_rank(
            context.recommends, "recommended_video_id"
        )
        context.recommended_by = context.recommended_by[:top_n]
        context.recommends = context.recommends[:top_n]
        return context

    @staticmethod
    def _by_feed_rank(
        rows: list[dict[str, Any]], id_key: str
    ) -> list[dict[str, Any]]:
        """Order rows by ascending feed ``position`` (None/unknown last)."""
        return sorted(
            rows,
            key=lambda row: (
                row.get("position") is None,
                row.get("position") if row.get("position") is not None else 0,
                row.get("run_id") or "",
                str(row.get(id_key) or ""),
            ),
        )
