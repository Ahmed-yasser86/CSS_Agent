"""Full network analytics over persisted recommendation edges (module B6).

Extends :class:`RecommendationGraphService` with:

* ``metrics`` - macro statistics for one network slice: density, reciprocity,
  degree-distribution percentiles, clustering, weak components, detected
  communities (greedy modularity) and the top HITS hubs/authorities;
* ``temporal`` - per-run ``NetworkSlice`` snapshots plus growth between
  consecutive requested runs;
* ``edges`` / ``export_edges`` - raw edge listing and
  graphml/edgelist/gexf export for interoperability with external tools;
* ``channel_projection`` - a lightweight channel-level projection.

NetworkX semantics (ADR-0009)
-----------------------------
* The recommendation network is built as a :class:`nx.DiGraph`
  (``RecommendationGraphService.build_graph``).
* Component analysis uses ``nx.weakly_connected_components`` - the directed
  equivalent of ``connected_components``, which raises
  ``NetworkXNotImplemented`` on a ``DiGraph``.
* Clustering coefficients are undirected-only measures, so
  ``avg_clustering`` and ``transitivity`` (global clustering) are computed on
  ``graph.to_undirected()``.
* ``reciprocity`` and ``degree`` are directed measures and run on the
  ``DiGraph`` as-is.
* ``greedy_modularity_communities``/``modularity`` accept directed graphs and
  use directed modularity (``community.modularity`` handles the
  in/out-degree terms); ``modularity`` is reported as ``None`` for an empty
  graph.
* ``nx.hits`` is a directed measure; hub/authority scores are returned
  unnormalised (the power iteration may yield small negative weights on
  graphs with zero-score sinks - the top-``n`` ranks remain meaningful).
"""

from __future__ import annotations

import io
from typing import Any

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities, modularity
from pydantic import BaseModel, ConfigDict

from SocialScienceResearch.persistence.base import Repositories
from SocialScienceResearch.services.recommendation_graph_service import (
    RecommendationGraphService,
)
from SocialScienceResearch.services.statistics_service import StatisticsService

#: Default page size applied by list endpoints (mirrors ``api/app.py``).
DEFAULT_PAGE_SIZE = 50


class _Base(BaseModel):
    """:class:`ConfigDict` ``extra="allow"`` base for response models."""

    model_config = ConfigDict(extra="allow")


class EdgeRow(_Base):
    """One serialized recommendation edge for listing / export."""

    source_video_id: str
    recommended_video_id: str
    position: int | None = None
    run_id: str | None = None
    title: str | None = None
    channel_id: str | None = None


class DegreeDistribution(_Base):
    """Percentile summary of a directed degree distribution."""

    min: float | None = None
    max: float | None = None
    mean: float | None = None
    median: float | None = None
    p25: float | None = None
    p75: float | None = None
    p90: float | None = None
    p95: float | None = None
    p99: float | None = None


class NetworkMetrics(_Base):
    """Aggregate statistics for one recommendation-network slice."""

    run_id: str | None = None
    node_count: int = 0
    edge_count: int = 0
    density: float = 0.0
    is_directed: bool = True
    reciprocity: float = 0.0
    degree_distribution: dict[str, DegreeDistribution] = {}
    avg_clustering: float = 0.0
    global_clustering: float = 0.0
    weakly_connected_components: int = 0
    largest_component_size: int = 0
    largest_component_share: float = 0.0
    community_count: int = 0
    modularity: float | None = None
    top_hubs: list[dict[str, Any]] = []
    top_authorities: list[dict[str, Any]] = []
    most_recommended: list[dict[str, Any]] = []
    most_active_sources: list[dict[str, Any]] = []


class TemporalGrowth(_Base):
    """Delta between two consecutive requested runs."""

    from_run_id: str
    to_run_id: str
    node_growth: int = 0
    edge_growth: int = 0
    density_growth: float = 0.0


class NetworkSlice(_Base):
    """NetworkSummary-like snapshot for a single run."""

    run_id: str
    node_count: int = 0
    edge_count: int = 0
    density: float = 0.0
    reciprocity: float = 0.0
    top_ranked: list[dict[str, Any]] = []


class TemporalResult(_Base):
    """Per-run slices and consecutive-run growth."""

    slices: list[NetworkSlice] = []
    growth: list[TemporalGrowth] = []


class ChannelProjection(_Base):
    """Lightweight channel-level projection (documented in the module doc).

    Recommendation edges carry a single ``channel_id`` (the channel of the
    recommended video, per ``RecommendationObservation``). ``channels`` lists
    the distinct ids observed on edges and ``edge_count`` counts the edges
    carrying a channel attribution. This is intentionally a lightweight
    projection - no inter-channel co-occurrence graph is built.
    """

    channels: list[str] = []
    edge_count: int = 0


class NetworkAnalyticsService:
    """Network-wide analytics built on ``RecommendationGraphService``."""

    def __init__(self, repos: Repositories) -> None:
        self._repos = repos
        self._graph_service = RecommendationGraphService(repos)

    # ------------------------------------------------------------------
    def metrics(self, run_id: str | None = None, top_n: int = 10) -> NetworkMetrics:
        """Compute aggregate network statistics for one slice."""
        graph = self._graph_service.build_graph(run_id)
        metrics = NetworkMetrics(
            run_id=run_id,
            node_count=graph.number_of_nodes(),
            edge_count=graph.number_of_edges(),
            is_directed=True,
        )
        if graph.number_of_edges() == 0:
            return metrics

        metrics.density = float(nx.density(graph))
        # Directed measure; ``nx.reciprocity`` is undefined on empty graphs,
        # already guarded by the edge-count check above.
        metrics.reciprocity = float(nx.reciprocity(graph))

        in_degrees = [d for _, d in graph.in_degree()]
        out_degrees = [d for _, d in graph.out_degree()]
        metrics.degree_distribution = {
            "in_degree": self._degree_distribution(in_degrees),
            "out_degree": self._degree_distribution(out_degrees),
        }

        # Clustering is undirected-only (ADR-0009): average clustering on the
        # undirected projection and transitivity for the global coefficient.
        undirected = graph.to_undirected()
        metrics.avg_clustering = float(nx.average_clustering(undirected))
        metrics.global_clustering = float(nx.transitivity(undirected))

        components = list(nx.weakly_connected_components(graph))
        metrics.weakly_connected_components = len(components)
        metrics.largest_component_size = max((len(c) for c in components), default=0)
        metrics.largest_component_share = (
            metrics.largest_component_size / metrics.node_count
        )

        communities = list(greedy_modularity_communities(graph))
        metrics.community_count = len(communities)
        metrics.modularity = (
            float(modularity(graph, communities)) if graph.number_of_edges() else None
        )

        hubs, authorities = nx.hits(graph)
        metrics.top_hubs = self._top_scores(hubs, top_n)
        metrics.top_authorities = self._top_scores(authorities, top_n)

        metrics.most_recommended = self._top_counts(
            dict(graph.in_degree()), top_n, "times_recommended"
        )
        metrics.most_active_sources = self._top_counts(
            dict(graph.out_degree()), top_n, "outgoing"
        )
        return metrics

    # ------------------------------------------------------------------
    def temporal(self, run_ids: list[str]) -> TemporalResult:
        """Per-run slices plus growth between consecutive requested runs."""
        slices: list[NetworkSlice] = []
        for run_id in run_ids:
            slices.append(self._slice(run_id))

        growth: list[TemporalGrowth] = []
        for left, right in zip(slices, slices[1:]):
            density_growth = (
                round(right.density - left.density, 6)
                if (left.node_count or right.node_count)
                else 0.0
            )
            growth.append(
                TemporalGrowth(
                    from_run_id=left.run_id,
                    to_run_id=right.run_id,
                    node_growth=right.node_count - left.node_count,
                    edge_growth=right.edge_count - left.edge_count,
                    density_growth=density_growth,
                )
            )
        return TemporalResult(slices=slices, growth=growth)

    # ------------------------------------------------------------------
    def edges(self, run_id: str | None = None) -> list[dict[str, Any]]:
        """Serialize all observed edges for a slice (export/listing).

        Rows are ordered by feed rank: grouped by source video, then by the
        ``position`` the recommendation occupied in that source's rail (so the
        edge listing and exports reflect the observed feed order).
        """
        rows: list[dict[str, Any]] = []
        for edge in self._repos.recommendations.list_recommendation_edges(
            run_id=run_id
        ):
            rows.append(
                {
                    "source_video_id": edge.source_video_id,
                    "recommended_video_id": edge.recommended_video_id,
                    "position": edge.position,
                    "run_id": edge.collection_run_id,
                    "title": edge.title,
                    "channel_id": edge.channel_id,
                }
            )
        return sorted(
            rows,
            key=lambda row: (
                row["source_video_id"],
                row["position"] is None,
                row["position"] if row["position"] is not None else 0,
                row["run_id"] or "",
                row["recommended_video_id"],
            ),
        )

    # ------------------------------------------------------------------
    def export_edges(
        self, run_id: str | None = None, format: str = "graphml"
    ) -> tuple[str, str, str]:
        """Serialize the network into a file-format string.

        Returns ``(suggested_filename, content, media_type)``. Raises
        ``ValueError`` for an unsupported ``format``.
        """
        graph = self._graph_service.build_graph(run_id)
        # GraphML/edgelist cannot serialize ``None`` edge-attrs, so sink them
        # to empty strings on a copy before writing.
        export = graph.copy()
        for _, _, data in export.edges(data=True):
            for key in ("position", "run_id", "title"):
                if data.get(key) is None:
                    data[key] = ""

        formats = {
            "graphml": ("recommendations.graphml", "application/xml"),
            "edgelist": ("recommendations.edgelist", "text/plain"),
            "gexf": ("recommendations.gexf", "application/gexf+xml"),
        }
        if format not in formats:
            raise ValueError(
                f"Unsupported export format '{format}' (expected one of: "
                + ", ".join(sorted(formats))
                + ")"
            )
        filename, media_type = formats[format]

        buffer = io.BytesIO()
        if format == "graphml":
            nx.write_graphml(export, buffer)
        elif format == "edgelist":
            nx.write_edgelist(export, buffer)
        else:
            nx.write_gexf(export, buffer)
        return filename, buffer.getvalue().decode("utf-8"), media_type

    # ------------------------------------------------------------------
    def channel_projection(
        self, run_id: str | None = None
    ) -> ChannelProjection:
        """Distinct channels observed on edges and their edge coverage.

        Lightweight projection: no co-occurrence graph is built between
        channels (see model docstring).
        """
        edges = self._repos.recommendations.list_recommendation_edges(run_id=run_id)
        channels = sorted({e.channel_id for e in edges if e.channel_id})
        edge_count = sum(1 for e in edges if e.channel_id)
        return ChannelProjection(channels=channels, edge_count=edge_count)

    # ------------------------------------------------------------------
    def _slice(self, run_id: str) -> NetworkSlice:
        """Build one per-run ``NetworkSlice`` (PageRank ``top_ranked``)."""
        graph = self._graph_service.build_graph(run_id)
        slice_model = NetworkSlice(
            run_id=run_id,
            node_count=graph.number_of_nodes(),
            edge_count=graph.number_of_edges(),
            density=float(nx.density(graph)),
        )
        if graph.number_of_edges():
            slice_model.reciprocity = float(nx.reciprocity(graph))
            top_pagerank = sorted(
                nx.pagerank(graph).items(), key=lambda item: item[1], reverse=True
            )
            slice_model.top_ranked = [
                {
                    "video_id": video,
                    "pagerank": round(rank, 6),
                }
                for video, rank in top_pagerank
            ]
        return slice_model

    @staticmethod
    def _degree_distribution(
        degrees: list[int],
    ) -> DegreeDistribution:
        """Percentile summary (linear interpolation via StatisticsService)."""
        if not degrees:
            return DegreeDistribution()
        return DegreeDistribution(
            min=float(min(degrees)),
            max=float(max(degrees)),
            mean=round(sum(degrees) / len(degrees), 6),
            median=StatisticsService.percentile(degrees, 50),
            p25=StatisticsService.percentile(degrees, 25),
            p75=StatisticsService.percentile(degrees, 75),
            p90=StatisticsService.percentile(degrees, 90),
            p95=StatisticsService.percentile(degrees, 95),
            p99=StatisticsService.percentile(degrees, 99),
        )

    @staticmethod
    def _top_scores(
        scores: dict[str, float], top_n: int
    ) -> list[dict[str, Any]]:
        """Top-``n`` name/score rows with deterministic tie-breaking."""
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return [
            {"video_id": video, "score": round(float(score), 6)}
            for video, score in ranked[:top_n]
        ]

    @staticmethod
    def _top_counts(
        counts: dict[str, int], top_n: int, value_key: str
    ) -> list[dict[str, Any]]:
        """Top-``n`` name/count rows with deterministic tie-breaking."""
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return [
            {"video_id": video, value_key: count} for video, count in ranked[:top_n]
        ]