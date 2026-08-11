"""Tests for the reproducible research sampling service."""

from __future__ import annotations

import pytest

from SocialScienceResearch.domain.enums import SamplingStrategy
from SocialScienceResearch.domain.models import Video, VideoObservation
from SocialScienceResearch.domain.query import SamplingSpec
from SocialScienceResearch.services import (
    SamplingService,
    UnsupportedSamplingError,
)
from SocialScienceResearch.utils.idgen import utcnow


def _add_video(repos, video_id, *, views, likes=0, comments=0, duration=100, upload_date=None):
    video = Video(
        video_id=video_id,
        url=f"https://www.youtube.com/watch?v={video_id}",
        channel_id="UCx",
        title=f"Video {video_id}",
        duration=duration,
        upload_date=upload_date,
        first_observed_run_id="run_1",
    )
    repos.videos.upsert_video(video)
    repos.videos.save_video_observation(
        VideoObservation(
            observation_id=f"obs_{video_id}",
            collection_run_id="run_1",
            video_id=video_id,
            observed_at=utcnow(),
            view_count=views,
            like_count=likes,
            comment_count=comments,
        )
    )
    return video


@pytest.fixture
def corpus(excel_repos):
    _add_video(excel_repos, "v1", views=1000, likes=100, comments=10, duration=120, upload_date=None)
    _add_video(excel_repos, "v2", views=5000, likes=500, comments=50, duration=300, upload_date=None)
    _add_video(excel_repos, "v3", views=200, likes=20, comments=2, duration=60, upload_date=None)
    # v4 has an entity row but NO observation -> views are MISSING.
    excel_repos.videos.upsert_video(
        Video(
            video_id="v4",
            url="https://www.youtube.com/watch?v=v4",
            channel_id="UCx",
            title="Video v4",
            first_observed_run_id="run_1",
        )
    )
    return excel_repos


def _spec(strategy, **kwargs) -> SamplingSpec:
    return SamplingSpec(strategy=strategy, **kwargs)


# ----------------------------------------------------------------------
def test_top_views_orders_descending(corpus) -> None:
    svc = SamplingService(corpus)
    result = svc.sample_videos("UCx", _spec(SamplingStrategy.TOP_VIEWS, size=2))
    assert result.entity_ids == ["v2", "v1"]
    assert result.sample_size == 2
    assert result.population_size == 4


def test_bottom_views_orders_ascending(corpus) -> None:
    svc = SamplingService(corpus)
    result = svc.sample_videos("UCx", _spec(SamplingStrategy.BOTTOM_VIEWS, size=2))
    assert result.entity_ids == ["v3", "v1"]


def test_top_likes(corpus) -> None:
    svc = SamplingService(corpus)
    result = svc.sample_videos("UCx", _spec(SamplingStrategy.TOP_LIKES, size=1))
    assert result.entity_ids == ["v2"]


def test_missing_metric_ranked_last_and_reported(corpus) -> None:
    svc = SamplingService(corpus)
    result = svc.sample_videos("UCx", _spec(SamplingStrategy.TOP_VIEWS))
    # v4 (no observation) is ranked last, never assigned a fabricated value.
    assert result.entity_ids[-1] == "v4"
    assert result.missing_metric_count == 1


def test_random_is_reproducible_with_seed(corpus) -> None:
    svc = SamplingService(corpus)
    first = svc.sample_videos("UCx", _spec(SamplingStrategy.RANDOM, seed=7))
    second = svc.sample_videos("UCx", _spec(SamplingStrategy.RANDOM, seed=7))
    assert first.entity_ids == second.entity_ids
    assert set(first.entity_ids) == {"v1", "v2", "v3", "v4"}


def test_percent_sampling(corpus) -> None:
    svc = SamplingService(corpus)
    result = svc.sample_videos("UCx", _spec(SamplingStrategy.TOP_VIEWS, percent=50))
    # 50% of 4 population -> top 2 by views.
    assert result.entity_ids == ["v2", "v1"]


def test_stratified_by_upload_year(corpus) -> None:
    svc = SamplingService(corpus)
    from datetime import date

    _add_video(corpus, "y2023", views=10, upload_date=date(2023, 5, 1))
    _add_video(corpus, "y2023b", views=20, upload_date=date(2023, 6, 1))
    _add_video(corpus, "y2025", views=30, upload_date=date(2025, 1, 1))
    result = svc.sample_videos(
        "UCx", _spec(SamplingStrategy.STRATIFIED, strata="year", sample_per_stratum=1)
    )
    selected = set(result.entity_ids)
    # One representative per year present, balanced.
    assert "y2023" in selected or "y2023b" in selected
    assert "y2025" in selected


def test_date_range_filters_by_upload_date(corpus) -> None:
    from datetime import date

    _add_video(corpus, "jan", views=1, upload_date=date(2024, 1, 15))
    _add_video(corpus, "mar", views=1, upload_date=date(2024, 3, 20))
    result = SamplingService(corpus).sample_videos(
        "UCx",
        _spec(
            SamplingStrategy.DATE_RANGE,
            date_from=date(2024, 1, 1),
            date_to=date(2024, 2, 1),
        ),
    )
    assert result.entity_ids == ["jan"]


def test_criteria_json_records_spec(corpus) -> None:
    result = SamplingService(corpus).sample_videos(
        "UCx", _spec(SamplingStrategy.TOP_VIEWS, size=1, seed=99)
    )
    assert result.criteria_json["strategy"] == "top_views"
    assert result.criteria_json["size"] == 1
    assert result.criteria_json["seed"] == 99
    assert result.criteria_json["population_size"] == 4
    assert result.seed == 99


# ----------------------------------------------------------------------
# Comment sampling
# ----------------------------------------------------------------------
def _add_comment(repos, comment_id, *, video_id="vid", likes=0, published_at=None):
    from SocialScienceResearch.domain.models import Comment, CommentObservation

    repos.comments.upsert_comment(
        Comment(
            comment_id=comment_id,
            video_id=video_id,
            author_name=f"Author {comment_id}",
            comment_text="text",
            published_at=published_at,
            first_observed_run_id="run_1",
        )
    )
    repos.comments.save_comment_observation(
        CommentObservation(
            observation_id=f"obs_c_{comment_id}",
            collection_run_id="run_1",
            comment_id=comment_id,
            observed_at=utcnow(),
            like_count=likes,
        )
    )


@pytest.fixture
def comment_corpus(excel_repos):
    _add_comment(excel_repos, "c1", likes=5)
    _add_comment(excel_repos, "c2", likes=50)
    _add_comment(excel_repos, "c3", likes=1)
    return excel_repos


def test_comment_top_likes(comment_corpus) -> None:
    result = SamplingService(comment_corpus).sample_comments(
        "vid", _spec(SamplingStrategy.TOP_LIKES, size=1)
    )
    assert result.entity_ids == ["c2"]


def test_comment_random_reproducible(comment_corpus) -> None:
    svc = SamplingService(comment_corpus)
    a = svc.sample_comments("vid", _spec(SamplingStrategy.RANDOM, seed=3))
    b = svc.sample_comments("vid", _spec(SamplingStrategy.RANDOM, seed=3))
    assert a.entity_ids == b.entity_ids


def test_video_strategy_rejected_for_comments(comment_corpus) -> None:
    with pytest.raises(UnsupportedSamplingError):
        SamplingService(comment_corpus).sample_comments(
            "vid", _spec(SamplingStrategy.TOP_VIEWS)
        )
