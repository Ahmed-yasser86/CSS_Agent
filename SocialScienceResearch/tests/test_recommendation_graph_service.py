"""Tests for the recommendation-network analysis service."""

from __future__ import annotations

from SocialScienceResearch.domain.enums import RecommendationStatus
from SocialScienceResearch.domain.models import RecommendationObservation
from SocialScienceResearch.services import RecommendationGraphService


def _edge(repos, source, target, *, run="run_1", position=None):
    repos.recommendations.save_recommendation(
        RecommendationObservation(
            observation_id=f"rec_{source}_{target}_{run}",
            collection_run_id=run,
            source_video_id=source,
            recommended_video_id=target,
            position=position,
            status=RecommendationStatus.OBSERVED,
        )
    )


def _seed(repos):
    # v1 recommends 3 videos; v4 is recommended by everyone (most-recommended hub).
    _edge(repos, "v1", "v2", position=0)
    _edge(repos, "v1", "v3", position=1)
    _edge(repos, "v1", "v4", position=2)
    _edge(repos, "v2", "v3", position=0)
    _edge(repos, "v2", "v4", position=1)
    _edge(repos, "v3", "v4", position=0)


def test_build_graph_edges(excel_repos) -> None:
    _seed(excel_repos)
    graph = RecommendationGraphService(excel_repos).build_graph()
    assert set(graph.nodes()) == {"v1", "v2", "v3", "v4"}
    assert graph.number_of_edges() == 6
    assert set(graph.successors("v1")) == {"v2", "v3", "v4"}


def test_build_graph_filters_by_run(excel_repos) -> None:
    _seed(excel_repos)
    _edge(excel_repos, "v9", "v1", run="run_2")
    graph = RecommendationGraphService(excel_repos).build_graph(run_id="run_1")
    assert "v9" not in graph.nodes()


def test_summary_counts_and_degrees(excel_repos) -> None:
    _seed(excel_repos)
    summary = RecommendationGraphService(excel_repos).summary()
    assert summary.node_count == 4
    assert summary.edge_count == 6
    # v4 is recommended by v1, v2 and v3 -> in-degree 3 (most recommended).
    assert summary.most_recommended[0]["video_id"] == "v4"
    assert summary.most_recommended[0]["times_recommended"] == 3
    # v1 recommends three videos -> most active source.
    assert summary.most_active_sources[0]["video_id"] == "v1"
    assert summary.most_active_sources[0]["outgoing"] == 3
    assert summary.highest_pagerank


def test_summary_empty_graph(excel_repos) -> None:
    summary = RecommendationGraphService(excel_repos).summary()
    assert summary.node_count == 0
    assert summary.edge_count == 0
    assert summary.most_recommended == []


def test_video_context_in_and_out(excel_repos) -> None:
    _seed(excel_repos)
    svc = RecommendationGraphService(excel_repos)
    context = svc.video_context("v1")
    assert context.in_degree == 0
    assert context.out_degree == 3
    assert {e["recommended_video_id"] for e in context.recommends} == {"v2", "v3", "v4"}

    middle = svc.video_context("v2")
    assert middle.in_degree == 1  # from v1
    assert middle.out_degree == 2
    assert {e["source_video_id"] for e in middle.recommended_by} == {"v1"}
    assert middle.pagerank is not None


def test_video_context_ranks_recommends_by_feed_position(excel_repos) -> None:
    # Insert out of feed order to prove the service ranks, not the repository.
    _edge(excel_repos, "v1", "last", run="run_1", position=5)
    _edge(excel_repos, "v1", "first", run="run_1", position=0)
    _edge(excel_repos, "v1", "middle", run="run_1", position=2)
    _edge(excel_repos, "v1", "no_rank", run="run_1", position=None)
    context = RecommendationGraphService(excel_repos).video_context("v1")
    ids = [e["recommended_video_id"] for e in context.recommends]
    assert ids == ["first", "middle", "last", "no_rank"]


def test_video_context_ranks_recommended_by_feed_position(excel_repos) -> None:
    # Two sources each recommend the target at different feed slots.
    _edge(excel_repos, "s_late", "target", run="run_1", position=9)
    _edge(excel_repos, "s_early", "target", run="run_1", position=0)
    context = RecommendationGraphService(excel_repos).video_context("target")
    assert [e["source_video_id"] for e in context.recommended_by] == [
        "s_early",
        "s_late",
    ]
