"""Tests for ``NetworkAnalyticsService`` and the B6 network router.

Seeds a small deterministic recommendation network across two runs:

* ``net_r1``: a single reciprocated pair ``a <-> b``;
* ``net_r2``: ``a2->b2, a2->c2, b2->c2, c2->a2, d2->a2`` (5 edges).

The combined (``run_id=None``) graph therefore has 6 nodes and 7 edges in two
weakly-connected components.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from SocialScienceResearch.api import create_app
from SocialScienceResearch.config.settings import (
    ApiSettings,
    CollectionSettings,
    RepositorySettings,
    ScraperSettings,
    SocialScienceSettings,
)
from SocialScienceResearch.domain.enums import RecommendationStatus
from SocialScienceResearch.domain.models import RecommendationObservation
from SocialScienceResearch.persistence.excel_repository import build_excel_repositories
from SocialScienceResearch.services.network_analytics_service import (
    NetworkAnalyticsService,
)

PREFIX = "/api/v1/social-science"


def _seed_recommendations(repos) -> None:
    """Seed the deterministic 2-run network described in the module docstring."""
    edges = [
        ("r_obs_1", "net_r1", "a", "b", 0, "UC1", "T a->b"),
        ("r_obs_2", "net_r1", "b", "a", 1, "UC1", "T b->a"),
        ("r_obs_3", "net_r2", "a2", "b2", 0, "UC2", "T a2->b2"),
        ("r_obs_4", "net_r2", "a2", "c2", 1, "UC3", "T a2->c2"),
        ("r_obs_5", "net_r2", "b2", "c2", 0, "UC3", "T b2->c2"),
        ("r_obs_6", "net_r2", "c2", "a2", 2, "UC2", "T c2->a2"),
        ("r_obs_7", "net_r2", "d2", "a2", 3, "UC2", "T d2->a2"),
    ]
    for observation_id, run_id, source, target, position, channel_id, title in edges:
        repos.recommendations.save_recommendation(
            RecommendationObservation(
                observation_id=observation_id,
                collection_run_id=run_id,
                source_video_id=source,
                recommended_video_id=target,
                position=position,
                status=RecommendationStatus.OBSERVED,
                channel_id=channel_id,
                title=title,
            )
        )


@pytest.fixture
def service(excel_repos) -> NetworkAnalyticsService:
    _seed_recommendations(excel_repos)
    return NetworkAnalyticsService(excel_repos)


@pytest.fixture
def client(tmp_path):
    repo_settings = RepositorySettings(data_dir=str(tmp_path), dataset_name="net")
    repos = build_excel_repositories(repo_settings)
    _seed_recommendations(repos)
    repos.store.close()

    settings = SocialScienceSettings(
        repository=repo_settings,
        scraper=ScraperSettings(retries=1, retry_backoff=0.0, request_delay_seconds=0),
        collection=CollectionSettings(collect_comments=False),
        api=ApiSettings(prefix=PREFIX),
    )
    app = create_app(settings)
    yield TestClient(app)


# ----------------------------------------------------------------------
# Service: metrics
# ----------------------------------------------------------------------
def test_metrics_full_graph_counts_and_bounds(service) -> None:
    metrics = service.metrics()
    assert metrics.node_count == 6
    assert metrics.edge_count == 7
    assert metrics.is_directed is True
    assert 0.0 <= metrics.density <= 1.0
    assert 0.0 <= metrics.reciprocity <= 1.0
    assert metrics.weakly_connected_components == 2
    assert metrics.largest_component_size == 4
    assert metrics.largest_component_share == pytest.approx(4 / 6)


def test_metrics_reciprocity_bidirectional_pair(service) -> None:
    metrics = service.metrics(run_id="net_r1")
    assert metrics.node_count == 2
    assert metrics.edge_count == 2
    assert metrics.reciprocity == 1.0
    assert metrics.density == 1.0


def test_metrics_degree_percentiles_on_known_distribution(service) -> None:
    metrics = service.metrics(run_id="net_r2")
    assert metrics.node_count == 4
    assert metrics.edge_count == 5

    in_deg = metrics.degree_distribution["in_degree"]
    # in-degrees across net_r2 nodes: a2=2, b2=1, c2=2, d2=0 -> [0, 1, 2, 2].
    assert in_deg.min == 0
    assert in_deg.max == 2
    assert in_deg.mean == pytest.approx(1.25)
    assert in_deg.median == pytest.approx(1.5)
    assert in_deg.p25 == pytest.approx(0.75)
    assert in_deg.p75 == pytest.approx(2.0)

    out_deg = metrics.degree_distribution["out_degree"]
    # out-degrees: a2=2, b2=1, c2=1, d2=1 -> [1, 1, 1, 2].
    assert out_deg.min == 1
    assert out_deg.max == 2
    assert out_deg.median == pytest.approx(1.0)
    assert out_deg.p25 == pytest.approx(1.0)
    assert out_deg.p75 == pytest.approx(1.25)

    assert metrics.most_recommended[0]["video_id"] == "a2"
    assert metrics.most_recommended[0]["times_recommended"] == 2
    assert metrics.most_active_sources[0]["video_id"] == "a2"
    assert metrics.most_active_sources[0]["outgoing"] == 2


# ----------------------------------------------------------------------
# Service: temporal
# ----------------------------------------------------------------------
def test_temporal_returns_one_slice_per_requested_run(service) -> None:
    result = service.temporal(["net_r1", "net_r2"])
    assert [slice_model.run_id for slice_model in result.slices] == ["net_r1", "net_r2"]
    assert result.slices[0].node_count == 2
    assert result.slices[0].edge_count == 2
    assert result.slices[1].node_count == 4
    assert result.slices[1].edge_count == 5

    assert len(result.growth) == 1
    growth = result.growth[0]
    assert growth.from_run_id == "net_r1"
    assert growth.to_run_id == "net_r2"
    assert growth.node_growth == 2
    assert growth.edge_growth == 3


def test_temporal_empty_request_returns_empty(service) -> None:
    result = service.temporal([])
    assert result.slices == []
    assert result.growth == []


# ----------------------------------------------------------------------
# Service: edges / export / channels
# ----------------------------------------------------------------------
def test_edges_lists_all_edge_dicts(service) -> None:
    edges = service.edges()
    assert len(edges) == 7
    for edge in edges:
        assert set(edge) == {
            "source_video_id",
            "recommended_video_id",
            "position",
            "run_id",
            "title",
            "channel_id",
        }


def test_edges_run_filter(service) -> None:
    assert len(service.edges(run_id="net_r1")) == 2
    assert len(service.edges(run_id="net_r2")) == 5


def test_edges_ordered_by_feed_rank_per_source(service) -> None:
    """Edges are grouped by source and ranked by feed position ascending."""
    edges = service.edges()
    for source in {"a", "b", "a2", "b2", "c2", "d2"}:
        group = [e for e in edges if e["source_video_id"] == source]
        positions = [e["position"] for e in group]
        assert positions == sorted(positions), f"{source} not feed-ranked: {positions}"


def test_export_graphml_marker(service) -> None:
    filename, content, media_type = service.export_edges(format="graphml")
    assert filename == "recommendations.graphml"
    assert "<graphml" in content
    assert media_type == "application/xml"


def test_export_edgelist_marker(service) -> None:
    filename, content, _ = service.export_edges(format="edgelist")
    assert filename == "recommendations.edgelist"
    lines = [line for line in content.splitlines() if line]
    assert lines
    for line in lines:
        tokens = line.split()
        # classic edgelist rows are "u v" (optionally followed by data).
        assert len(tokens) >= 2


def test_export_gexf_marker(service) -> None:
    filename, content, media_type = service.export_edges(format="gexf")
    assert filename == "recommendations.gexf"
    assert "<gexf" in content
    assert media_type == "application/gexf+xml"


def test_export_unknown_format_raises_value_error(service) -> None:
    with pytest.raises(ValueError):
        service.export_edges(format="dot")


def test_channel_projection_lists_distinct_channels(service) -> None:
    projection = service.channel_projection()
    assert projection.channels == ["UC1", "UC2", "UC3"]
    assert projection.edge_count == 7

    projection = service.channel_projection(run_id="net_r1")
    assert projection.channels == ["UC1"]
    assert projection.edge_count == 2


# ----------------------------------------------------------------------
# Router endpoints (TestClient)
# ----------------------------------------------------------------------
def test_endpoint_metrics(client) -> None:
    resp = client.get(f"{PREFIX}/network/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["node_count"] == 6
    assert body["edge_count"] == 7
    assert body["is_directed"] is True
    assert 0.0 <= body["density"] <= 1.0


def test_endpoint_temporal(client) -> None:
    resp = client.get(f"{PREFIX}/network/temporal", params={"runs": "net_r1,net_r2"})
    assert resp.status_code == 200
    body = resp.json()
    assert [s["run_id"] for s in body["slices"]] == ["net_r1", "net_r2"]
    assert body["slices"][0]["reciprocity"] == 1.0
    assert body["growth"][0]["edge_growth"] == 3


def test_endpoint_edges_pagination_envelope(client) -> None:
    resp = client.get(f"{PREFIX}/network/edges", params={"page_size": 3})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"items", "next_cursor", "has_more", "total"}
    assert len(body["items"]) == 3
    assert body["total"] == 7
    assert body["has_more"] is True
    assert body["next_cursor"] is not None
    assert set(body["items"][0]) == {
        "source_video_id",
        "recommended_video_id",
        "position",
        "run_id",
        "title",
        "channel_id",
    }


def test_endpoint_edges_paginates_to_end(client) -> None:
    seen: list[str] = []
    cursor = None
    while True:
        params = {"page_size": 2}
        if cursor:
            params["cursor"] = cursor
        body = client.get(f"{PREFIX}/network/edges", params=params).json()
        seen += [e["source_video_id"] + "->" + e["recommended_video_id"]
                 for e in body["items"]]
        cursor = body["next_cursor"]
        if not body["has_more"]:
            break
    assert len(seen) == 7
    assert len(set(seen)) == 7


def test_endpoint_export_graphml(client) -> None:
    resp = client.get(f"{PREFIX}/network/export", params={"format": "graphml"})
    assert resp.status_code == 200
    assert "<graphml" in resp.text
    assert 'filename="recommendations.graphml"' in resp.headers["content-disposition"]
    assert "xml" in resp.headers["content-type"]


def test_endpoint_export_unknown_format_is_400(client) -> None:
    resp = client.get(f"{PREFIX}/network/export", params={"format": "dot"})
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_argument"


def test_endpoint_channels(client) -> None:
    resp = client.get(f"{PREFIX}/network/channels")
    assert resp.status_code == 200
    body = resp.json()
    assert body["channels"] == ["UC1", "UC2", "UC3"]
    assert body["edge_count"] == 7