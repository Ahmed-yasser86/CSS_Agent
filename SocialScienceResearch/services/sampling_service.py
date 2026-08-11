"""Reproducible research sampling of videos and comments.

Sampling is transparent: every call records the exact criteria used
(strategy, size, seed, strata) in ``criteria_json`` so samples can be audited
and reproduced. Videos whose ranking metric is unavailable (no observation,
no duration, ...) are ranked last and reported in ``missing_metric_count`` -
never fabricated or silently dropped.

Strategies implemented follow :class:`SamplingStrategy`. Comment sampling
supports only the strategies that are meaningful for comments
(``TOP_LIKES``, ``RANDOM``, ``STRATIFIED``, ``LATEST``, ``EARLIEST``,
``DATE_RANGE``); requesting a video-only strategy for comments raises
:class:`UnsupportedSamplingError` instead of guessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from random import Random
from typing import Callable, Iterable

from SocialScienceResearch.domain.enums import SamplingStrategy
from SocialScienceResearch.domain.models import Comment, Video
from SocialScienceResearch.domain.query import SamplingSpec
from SocialScienceResearch.persistence.base import Repositories
from SocialScienceResearch.services.statistics_service import StatisticsService
from SocialScienceResearch.utils.idgen import utcnow


class SamplingError(Exception):
    """Base error for sampling problems."""


class UnsupportedSamplingError(SamplingError):
    """A strategy was requested for an entity type it does not apply to."""


@dataclass
class SamplingResult:
    """Outcome of a reproducible sampling operation."""

    strategy: SamplingStrategy
    entity_type: str  # 'video' | 'comment'
    population_size: int
    sample_size: int
    entity_ids: list[str] = field(default_factory=list)
    criteria_json: dict = field(default_factory=dict)
    seed: int | None = None
    missing_metric_count: int = 0


class SamplingService:
    """Applies explicit, reproducible sampling strategies to the corpus."""

    def __init__(self, repos: Repositories, default_seed: int = 42) -> None:
        self._repos = repos
        self._default_seed = default_seed

    # ------------------------------------------------------------------
    # Videos
    # ------------------------------------------------------------------
    def sample_videos(
        self,
        channel_id: str,
        spec: SamplingSpec,
    ) -> SamplingResult:
        """Sample videos of a channel using ``spec.strategy``."""
        videos = self._repos.videos.list_videos(channel_id=channel_id)
        latest_obs = self._repos.videos.get_latest_video_observations(
            [video.video_id for video in videos]
        )
        metric_cache = {
            video.video_id: latest_obs.get(video.video_id) for video in videos
        }

        def metric(key: str) -> Callable[[Video], float | int | None]:
            def _get(video: Video):
                obs = metric_cache[video.video_id]
                if key == "views":
                    return obs.view_count if obs else None
                if key == "likes":
                    return obs.like_count if obs else None
                if key == "comments":
                    return obs.comment_count if obs else None
                if key == "engagement":
                    return self._ratio(
                        self._sum(obs, "like_count", "comment_count"),
                        obs.view_count if obs else None,
                    )
                if key == "comment_rate":
                    return self._ratio(
                        obs.comment_count if obs else None,
                        obs.view_count if obs else None,
                    )
                if key == "like_rate":
                    return self._ratio(
                        obs.like_count if obs else None,
                        obs.view_count if obs else None,
                    )
                return None

            return _get

        ranked: list[Video] | None = None
        missing = 0
        strategy = spec.strategy

        if strategy == SamplingStrategy.TOP_VIEWS:
            ranked, missing = self._rank(videos, metric("views"), reverse=True)
        elif strategy == SamplingStrategy.BOTTOM_VIEWS:
            ranked, missing = self._rank(videos, metric("views"), reverse=False)
        elif strategy == SamplingStrategy.TOP_LIKES:
            ranked, missing = self._rank(videos, metric("likes"), reverse=True)
        elif strategy == SamplingStrategy.BOTTOM_LIKES:
            ranked, missing = self._rank(videos, metric("likes"), reverse=False)
        elif strategy == SamplingStrategy.TOP_ENGAGEMENT:
            ranked, missing = self._rank(videos, metric("engagement"), reverse=True)
        elif strategy == SamplingStrategy.BOTTOM_ENGAGEMENT:
            ranked, missing = self._rank(videos, metric("engagement"), reverse=False)
        elif strategy == SamplingStrategy.TOP_COMMENTS:
            ranked, missing = self._rank(videos, metric("comments"), reverse=True)
        elif strategy == SamplingStrategy.TOP_COMMENT_RATE:
            ranked, missing = self._rank(videos, metric("comment_rate"), reverse=True)
        elif strategy == SamplingStrategy.TOP_LIKE_RATE:
            ranked, missing = self._rank(videos, metric("like_rate"), reverse=True)
        elif strategy == SamplingStrategy.LONGEST:
            ranked, missing = self._rank(
                videos, lambda v: v.duration, reverse=True
            )
        elif strategy == SamplingStrategy.SHORTEST:
            ranked, missing = self._rank(
                videos, lambda v: v.duration, reverse=False
            )
        elif strategy == SamplingStrategy.LATEST:
            ranked, missing = self._rank(
                videos, lambda v: v.upload_date, reverse=True
            )
        elif strategy == SamplingStrategy.EARLIEST:
            ranked, missing = self._rank(
                videos, lambda v: v.upload_date, reverse=False
            )
        elif strategy == SamplingStrategy.DATE_RANGE:
            ranked, missing = self._date_range(videos, spec)
        elif strategy == SamplingStrategy.RANDOM:
            ranked, missing = self._random(videos, spec)
        elif strategy == SamplingStrategy.STRATIFIED:
            ranked, missing = self._stratified(videos, spec)
        else:  # pragma: no cover - enum is closed
            raise UnsupportedSamplingError(f"Unknown strategy {strategy}")

        ids = [v.video_id for v in ranked]
        sample = self._cut(ids, spec)
        return SamplingResult(
            strategy=strategy,
            entity_type="video",
            population_size=len(videos),
            sample_size=len(sample),
            entity_ids=sample,
            criteria_json=self._criteria(spec, len(videos), missing),
            seed=spec.seed if spec.seed is not None else self._default_seed,
            missing_metric_count=missing,
        )

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------
    def sample_comments(
        self,
        video_id: str,
        spec: SamplingSpec,
    ) -> SamplingResult:
        """Sample comments of a video using a comment-applicable strategy."""
        comments = self._repos.comments.list_comments(video_id)
        strategy = spec.strategy
        if strategy not in self._COMMENT_STRATEGIES:
            raise UnsupportedSamplingError(
                f"Strategy '{strategy.value}' is not applicable to comments"
            )

        ranked: list[Comment] | None = None
        if strategy == SamplingStrategy.TOP_LIKES:
            latest_obs = self._repos.comments.get_latest_comment_observations(
                [c.comment_id for c in comments]
            )
            likes = {
                c.comment_id: (
                    latest_obs[c.comment_id].like_count
                    if latest_obs.get(c.comment_id) is not None
                    else None
                )
                for c in comments
            }
            ranked, _ = self._rank(
                comments, lambda c: likes[c.comment_id], reverse=True
            )
        elif strategy == SamplingStrategy.LATEST:
            ranked, _ = self._rank(comments, lambda c: c.published_at, reverse=True)
        elif strategy == SamplingStrategy.EARLIEST:
            ranked, _ = self._rank(comments, lambda c: c.published_at, reverse=False)
        elif strategy == SamplingStrategy.DATE_RANGE:
            ranked, _ = self._comment_date_range(comments, spec)
        elif strategy == SamplingStrategy.RANDOM:
            ranked, _ = self._random(comments, spec)
        elif strategy == SamplingStrategy.STRATIFIED:
            ranked, _ = self._stratified(comments, spec)

        ids = [c.comment_id for c in ranked or []]
        sample = self._cut(ids, spec)
        return SamplingResult(
            strategy=strategy,
            entity_type="comment",
            population_size=len(comments),
            sample_size=len(sample),
            entity_ids=sample,
            criteria_json=self._criteria(spec, len(comments), 0),
            seed=spec.seed if spec.seed is not None else self._default_seed,
        )

    # ------------------------------------------------------------------
    # Strategy internals
    # ------------------------------------------------------------------
    @staticmethod
    def _ratio(numerator: float | int | None, denominator: float | int | None):
        """None/zero-safe ratio; delegates to StatisticsService."""
        return StatisticsService.ratio(numerator, denominator)

    @staticmethod
    def _sum(obs, *fields: str) -> float | int | None:
        if obs is None:
            return None
        return StatisticsService.sum_values(*(getattr(obs, field_name) for field_name in fields))

    def _latest_obs(self, video_id: str):
        return self._repos.videos.get_latest_video_observation(video_id)

    def _latest_comment_likes(self, comment_id: str):
        obs = self._repos.comments.get_latest_comment_observation(comment_id)
        return obs.like_count if obs else None

    @staticmethod
    def _rank(
        items: list, key: Callable, *, reverse: bool
    ) -> tuple[list, int]:
        """Sort items by ``key`` with missing values ranked last.

        Returns ``(ranked_items, missing_count)``.
        """
        with_value = [it for it in items if key(it) is not None]
        without_value = [it for it in items if key(it) is None]
        with_value.sort(key=lambda it: (key(it) is None, key(it)), reverse=reverse)
        return with_value + without_value, len(without_value)

    def _cut(self, ids: list[str], spec: SamplingSpec) -> list[str]:
        """Apply ``size`` or ``percent`` to an already-ordered id list."""
        population = len(ids)
        if spec.size is not None:
            return ids[: max(0, min(spec.size, population))]
        if spec.percent is not None:
            count = round(population * spec.percent / 100.0)
            return ids[: max(0, min(count, population))]
        if spec.top_n is not None:
            return ids[: max(0, min(spec.top_n, population))]
        return ids

    def _random(self, items: list, spec: SamplingSpec) -> tuple[list, int]:
        rng = Random(spec.seed if spec.seed is not None else self._default_seed)
        return rng.sample(items, len(items)), 0

    def _date_range(self, videos: list[Video], spec: SamplingSpec) -> tuple[list, int]:
        if not spec.date_from and not spec.date_to:
            return videos, 0
        start, end = spec.date_from or date.min, spec.date_to or date.max
        kept = [
            v for v in videos if v.upload_date is not None and start <= v.upload_date <= end
        ]
        return kept, 0

    def _comment_date_range(
        self, comments: list[Comment], spec: SamplingSpec
    ) -> tuple[list, int]:
        if not spec.date_from and not spec.date_to:
            return comments, 0
        start = (
            spec.date_from
            if spec.date_from
            else date(1970, 1, 1)
        )
        end = spec.date_to or date.max
        kept = [
            c
            for c in comments
            if c.published_at is not None
            and start <= c.published_at.date() <= end
        ]
        return kept, 0

    def _stratified(self, items: list, spec: SamplingSpec) -> tuple[list, int]:
        """Balanced sampling per stratum (year/month/weekday of publication).

        Draws ``sample_per_stratum`` items *randomly within each stratum* using
        a seed-derived RNG (same seed -> same sample, different seed -> a
        different representative), mirroring :meth:`_random`.
        """
        per = spec.sample_per_stratum or 1
        rng = Random(spec.seed if spec.seed is not None else self._default_seed)
        strata: dict[str, list] = {}
        for item in items:
            key = self._stratum_key(item, spec.strata)
            if key is not None:
                strata.setdefault(key, []).append(item)
        selected: list = []
        for key in sorted(strata):
            bucket = strata[key]
            if len(bucket) <= per:
                selected.extend(bucket)
            else:
                selected.extend(rng.sample(bucket, per))
        return selected, 0

    @staticmethod
    def _stratum_key(item, strata: str | None) -> str | None:
        published = item.published_at if isinstance(item, Comment) else item.upload_date
        if published is None:
            return None
        if strata == "year":
            return str(published.year)
        if strata == "month":
            return f"{published.year}-{published.month:02d}"
        if strata == "weekday":
            return str(published.weekday())
        return str(published.year)

    @staticmethod
    def _criteria(spec: SamplingSpec, population: int, missing: int) -> dict:
        return {
            "strategy": spec.strategy.value,
            "size": spec.size,
            "percent": spec.percent,
            "top_n": spec.top_n,
            "seed": spec.seed,
            "strata": spec.strata,
            "sample_per_stratum": spec.sample_per_stratum,
            "date_from": spec.date_from.isoformat() if spec.date_from else None,
            "date_to": spec.date_to.isoformat() if spec.date_to else None,
            "population_size": population,
            "missing_metric_count": missing,
            "generated_at": utcnow().isoformat(),
        }

    _COMMENT_STRATEGIES = frozenset(
        {
            SamplingStrategy.TOP_LIKES,
            SamplingStrategy.RANDOM,
            SamplingStrategy.STRATIFIED,
            SamplingStrategy.LATEST,
            SamplingStrategy.EARLIEST,
            SamplingStrategy.DATE_RANGE,
        }
    )
