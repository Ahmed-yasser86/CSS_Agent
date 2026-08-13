"""Recommendation observation workflow.

Collects the recommendations observable around a source video *to the extent
the selected library supports it*, persists them as observed relationships
(never as permanent properties), and records an explicit
``RECOMMENDATION_UNSUPPORTED`` error when the library cannot provide them.

yt-dlp does not expose recommendations reliably, so by default this workflow
correctly yields an unsupported status rather than fabricating edges.
"""

from __future__ import annotations

from SocialScienceResearch.acquisition import (
    AcquisitionError,
    AcquisitionProvider,
    RecommendationUnsupportedError,
)
from SocialScienceResearch.acquisition.normalization import (
    normalize_recommendations,
    normalize_video,
    normalize_video_observation,
)
from SocialScienceResearch.domain.enums import (
    CollectionStatus,
    EntityType,
    ErrorType,
    RunType,
)
from SocialScienceResearch.utils.logger import get_logger

from .collection_service import CollectionService
from .results import CollectionResult

logger = get_logger(__name__)


class RecommendationService(CollectionService):
    """Extends the collection service with recommendation observation runs."""

    def collect_recommendations(self, video_url: str) -> CollectionResult:
        """Collect the source video plus its observable recommendations."""
        run = self._begin_run(RunType.RECOMMENDATION, video_url)
        errors: list = []

        # 1. Resolve and persist the source video first (its id anchors edges).
        try:
            info = self._provider.extract_video(video_url)
        except AcquisitionError as exc:
            self._record_error(run, EntityType.VIDEO, None, exc.error_type, str(exc))
            self._finish_run(
                run, CollectionStatus.FAILED, errors,
                discovered=1, succeeded=0, entities_existing=0, comments_collected=0, failed=1
            )
            return self._result(run, errors)

        video = normalize_video(info, run.run_id)
        if video is None:
            err = self._record_error(
                run,
                EntityType.VIDEO,
                None,
                ErrorType.VALIDATION,
                "Could not resolve a video id for the recommendation source.",
            )
            errors.append(err)
            self._finish_run(
                run, CollectionStatus.FAILED, errors,
                discovered=1, succeeded=0, entities_existing=0, comments_collected=0, failed=1
            )
            return self._result(run, errors)

        self._repos.videos.upsert_video(video)
        obs = normalize_video_observation(info, run.run_id, video.video_id)
        if obs is not None:
            self._repos.videos.save_video_observation(obs)
        run.target_video_id = video.video_id

        # 2. Attempt recommendation observation.
        try:
            raw_recommendations = self._provider.extract_recommendations(video_url)
        except RecommendationUnsupportedError as exc:
            err = self._record_error(
                run,
                EntityType.RECOMMENDATION,
                video.video_id,
                exc.error_type,
                str(exc),
                retryable=False,
            )
            errors.append(err)
            self._finish_run(
                run, CollectionStatus.PARTIAL, errors,
                discovered=1, succeeded=0, entities_existing=0, comments_collected=0, failed=1
            )
            result = self._result(run, errors)
            result.entities_created = 1
            return result
        except AcquisitionError as exc:
            err = self._record_error(
                run, EntityType.RECOMMENDATION, video.video_id, exc.error_type, str(exc)
            )
            errors.append(err)
            self._finish_run(
                run, CollectionStatus.PARTIAL, errors,
                discovered=1, succeeded=0, entities_existing=0, comments_collected=0, failed=1
            )
            result = self._result(run, errors)
            result.entities_created = 1
            return result

        edges = normalize_recommendations(video.video_id, raw_recommendations, run.run_id)
        created = 0
        for edge in edges:
            result = self._repos.recommendations.save_recommendation(edge)
            created += int(result.created)

        status = CollectionStatus.PARTIAL if errors else CollectionStatus.SUCCESS
        self._finish_run(
            run,
            status,
            errors,
            discovered=len(edges) + 1,
            succeeded=len(edges),
            entities_existing=0,
            comments_collected=0,
            failed=len(errors),
        )
        result = self._result(run, errors)
        result.entities_created = created
        result.comments_collected = 0
        logger.info(
            "recommendation run %s: %d edge(s) for source %s",
            run.run_id,
            len(edges),
            video.video_id,
        )
        return result
