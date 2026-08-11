"""Tests for the FastAPI application (via TestClient, no network)."""

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
from SocialScienceResearch.domain.models import (
    Channel,
    ChannelObservation,
    CollectionRun,
    RecommendationObservation,
    Video,
    VideoObservation,
)
from SocialScienceResearch.persistence.excel_repository import build_excel_repositories
from SocialScienceResearch.utils.idgen import utcnow


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SOCIAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SOCIAL_DATASET_NAME", "api")
    repo_settings = RepositorySettings(data_dir=str(tmp_path), dataset_name="api")
    repos = build_excel_repositories(repo_settings)

    repos.runs.create_run(
        CollectionRun(
            run_id="run_api_1",
            run_type="channel",
            target_url="https://www.youtube.com/@example",
            target_channel_id="UCapi000000000000000000000",
            started_at=utcnow(),
            status="success",
        )
    )
    repos.channels.upsert_channel(
        Channel(
            channel_id="UCapi000000000000000000000",
            url="https://www.youtube.com/channel/UCapi000000000000000000000",
            title="API Channel",
            first_observed_run_id="run_api_1",
        )
    )
    repos.channels.save_channel_observation(
        ChannelObservation(
            observation_id="obs_api_ch",
            collection_run_id="run_api_1",
            channel_id="UCapi000000000000000000000",
            observed_at=utcnow(),
            subscriber_count=999,
            video_count=1,
            view_count=10000,
        )
    )
    repos.videos.upsert_video(
        Video(
            video_id="api_v1",
            url="https://www.youtube.com/watch?v=api_v1",
            channel_id="UCapi000000000000000000000",
            title="API Video",
            duration=600,
            first_observed_run_id="run_api_1",
        )
    )
    repos.videos.save_video_observation(
        VideoObservation(
            observation_id="obs_api_vid",
            collection_run_id="run_api_1",
            video_id="api_v1",
            observed_at=utcnow(),
            view_count=1000,
            like_count=100,
            comment_count=10,
        )
    )
    repos.recommendations.save_recommendation(
        RecommendationObservation(
            observation_id="rec_api_1",
            collection_run_id="run_api_1",
            source_video_id="api_v1",
            recommended_video_id="api_target",
            position=0,
            status=RecommendationStatus.OBSERVED,
        )
    )
    repos.store.close()

    settings = SocialScienceSettings(
        repository=repo_settings,
        scraper=ScraperSettings(retries=1, retry_backoff=0.0, request_delay_seconds=0),
        collection=CollectionSettings(collect_comments=False),
        api=ApiSettings(prefix="/api/v1/social-science"),
    )
    app = create_app(settings)
    yield TestClient(app)


PREFIX = "/api/v1/social-science"


def test_runs_list(client) -> None:
    resp = client.get(f"{PREFIX}/runs")
    assert resp.status_code == 200
    runs = resp.json()["items"]
    assert any(r["run_id"] == "run_api_1" for r in runs)


def test_run_not_found_404(client) -> None:
    resp = client.get(f"{PREFIX}/runs/nope")
    assert resp.status_code == 404


def test_channel_overview(client) -> None:
    resp = client.get(f"{PREFIX}/channels/UCapi000000000000000000000/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["subscribers"]["value"] == 999
    assert body["subscribers"]["availability"] == "available"


def test_channel_videos_filter(client) -> None:
    resp = client.get(
        f"{PREFIX}/channels/UCapi000000000000000000000/videos",
        params={"duration_min": 500},
    )
    assert resp.status_code == 200
    videos = resp.json()["items"]
    assert [v["video_id"] for v in videos] == ["api_v1"]

    resp = client.get(
        f"{PREFIX}/channels/UCapi000000000000000000000/videos",
        params={"duration_min": 700},
    )
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_video_engagement(client) -> None:
    resp = client.get(f"{PREFIX}/videos/api_v1/engagement")
    assert resp.status_code == 200
    body = resp.json()
    assert body["views"]["value"] == 1000
    assert body["engagement_rate"]["value"] == pytest.approx(0.11)


def test_sample_videos(client) -> None:
    resp = client.post(
        f"{PREFIX}/channels/UCapi000000000000000000000/videos/sample",
        json={"strategy": "top_views", "size": 1},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["entity_ids"] == ["api_v1"]
    assert body["criteria_json"]["strategy"] == "top_views"


def test_video_recommendations(client) -> None:
    resp = client.get(f"{PREFIX}/videos/api_v1/recommendations")
    assert resp.status_code == 200
    edges = resp.json()["items"]
    assert [e["recommended_video_id"] for e in edges] == ["api_target"]


def test_network_summary(client) -> None:
    resp = client.get(f"{PREFIX}/network/recommendations/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["node_count"] == 2
    assert body["edge_count"] == 1


def test_network_video_context(client) -> None:
    resp = client.get(f"{PREFIX}/network/recommendations/api_v1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["out_degree"] == 1
    assert body["recommends"][0]["recommended_video_id"] == "api_target"
