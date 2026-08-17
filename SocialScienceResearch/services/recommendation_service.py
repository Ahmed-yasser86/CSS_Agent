"""Recommendation observation workflow.

Collects the recommendations observable around a source video *to the extent
the selected library supports it*, persists them as observed relationships
(never as permanent properties), and records an explicit
``RECOMMENDATION_UNSUPPORTED`` error when the library cannot provide them.

yt-dlp does not expose recommendations reliably, so by default this workflow
correctly yields an unsupported status rather than fabricating edges.

Network-tab entry points
------------------------
* ``collect_recommendations`` - single-video scrape (click-to-scrape from a
  graph node). Accepts an optional ``video_id`` (reuses the persisted source
  video instead of re-fetching it) and ``parent_run_id`` (the run whose node
  started the scrape).
* ``collect_recommendations_for_videos`` - bulk depth-1 scrape for a set of
  source videos (re-scrape a run / a channel from the network tab). One
  ``RunType.RECOMMENDATION`` run per video so temporal slices stay
  meaningful; network work runs concurrently under ONE shared rate limiter.

Every run records ``parent_run_id`` and a ``config_json["trigger"]`` marker
for provenance, and its observed edges are auto-persisted as a run-scoped
dataset with lineage (``Dataset.source_projection["lineage"]``).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

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

from .collection_service import CollectionService, ProgressReporter, _RateLimiter
from .results import CollectionResult

logger = get_logger(__name__)


def _watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


class RecommendationService(CollectionService):
    """Extends the collection service with recommendation observation runs."""

    # ------------------------------------------------------------------
    def collect_recommendations(
        self,
        video_url: str | None = None,
        *,
        video_id: str | None = None,
        parent_run_id: str | None = None,
        dedupe_run_ids: list[str] | None = None,
        layer_index: int | None = None,
        max_recommendations_per_video: int | None = None,
        reporter: ProgressReporter | None = None,
    ) -> CollectionResult:
        """Collect the source video plus its observable recommendations.

        Backwards compatible: ``video_url`` alone works (legacy callers). When
        ``video_id`` is supplied and the video is already persisted, the source
        video is reused instead of re-fetched; otherwise it is extracted and
        persisted. ``parent_run_id`` records the run that triggered this scrape
        and ``dedupe_run_ids`` skips edges already observed by those runs.
        ``layer_index`` stamps the run (and its edges) with a crawl layer, or
        ``None`` for layer-agnostic scrapes. ``max_recommendations_per_video``
        keeps only the top-N observed edges (by feed position) for this run.
        """
        if not video_url and video_id:
            existing = self._repos.videos.get_video(video_id)
            video_url = existing.url if existing else _watch_url(video_id)
        if not video_url:
            raise ValueError("video_url or video_id is required")

        run = self._begin_recommendation_run(
            video_url, parent_run_id, "node_click", layer_index=layer_index
        )
        errors: list = []

        # 1. Resolve the source video (its id anchors edges).
        video = self._repos.videos.get_video(video_id) if video_id else None
        if video is None:
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
                self._record_error(
                    run,
                    EntityType.VIDEO,
                    None,
                    ErrorType.VALIDATION,
                    "Could not resolve a video id for the recommendation source.",
                )
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
            self._repos.runs.update_run(run)

        self._report(reporter, "recommendation/start", message=f"Starting recommendation scrape for {video_url}")

        # 2. Attempt recommendation observation.
        payload: dict[str, Any] = {
            "video_id": video.video_id,
            "video": video,
            "raw": None,
            "error": None,
            "unsupported": None,
            "missing": False,
        }
        try:
            payload["raw"] = self._provider.extract_recommendations(
                video.url or video_url
            )
        except RecommendationUnsupportedError as exc:
            payload["unsupported"] = exc
        except AcquisitionError as exc:
            payload["error"] = exc
        return self._complete_video_result(
            run,
            payload,
            channel_id=None,
            dedupe_run_ids=dedupe_run_ids,
            layer_index=layer_index,
            max_recommendations_per_video=max_recommendations_per_video,
            reporter=reporter,
        )

    # ------------------------------------------------------------------
    def collect_recommendations_for_videos(
        self,
        video_ids: list[str],
        *,
        parent_run_id: str | None = None,
        channel_id: str | None = None,
        dedupe_run_ids: list[str] | None = None,
        layer_index: int | None = None,
        concurrency: int | None = None,
        max_recommendations_per_video: int | None = None,
        reporter: ProgressReporter | None = None,
    ) -> list[CollectionResult]:
        """Bulk depth-1 recommendation scrape for a set of source videos.

        Creates one :class:`RunType.RECOMMENDATION` run per video (lineage via
        ``parent_run_id``), network work running concurrently under ONE shared
        rate limiter. Returns one result per source video, ordered by input.
        A single video's failure never aborts its siblings. ``layer_index``
        stamps each run (and its edges) with a crawl layer, or ``None`` for
        layer-agnostic scrapes. ``max_recommendations_per_video`` keeps only
        the top-N observed edges per source feed.
        """
        if not video_ids:
            return []
        concurrency = max(1, concurrency or self._settings.scraper.enrichment_concurrency)
        throttle = _RateLimiter(self._settings.scraper.request_delay_seconds)

        self._report(
            reporter,
            "recommendation/batch/start",
            discovered=len(video_ids),
            message=f"Scraping recommendations for {len(video_ids)} video(s)",
        )

        results: list[CollectionResult] = []
        with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="rec") as pool:
            futures = {
                pool.submit(
                    self._scrape_video_task,
                    video_id,
                    parent_run_id,
                    dedupe_run_ids,
                    throttle,
                ): video_id
                for video_id in video_ids
            }
            for future in as_completed(futures):
                payload = future.result()
                video_id = payload["video_id"]
                run = self._begin_recommendation_run(
                    _watch_url(video_id),
                    parent_run_id,
                    "run_bulk",
                    layer_index=layer_index,
                )
                run.target_video_id = video_id
                self._repos.runs.update_run(run)
                results.append(
                    self._complete_video_result(
                        run,
                        payload,
                        channel_id=channel_id,
                        dedupe_run_ids=dedupe_run_ids,
                        layer_index=layer_index,
                        max_recommendations_per_video=max_recommendations_per_video,
                        reporter=reporter,
                    )
                )

        results.sort(
            key=lambda r: video_ids.index(r.target_id)
            if r.target_id in video_ids
            else len(video_ids)
        )
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _scrape_video_task(
        self,
        video_id: str,
        parent_run_id: str | None,
        dedupe_run_ids: list[str] | None,
        throttle: _RateLimiter,
    ) -> dict[str, Any]:
        """Worker-thread network phase for one video.

        Only the slow network calls run here (rate-limited). Persistence and
        run bookkeeping happen on the caller thread via
        :meth:`_complete_video_result`.

        The source video does NOT need a persisted ``Video`` row: a video may
        exist only as a graph node (e.g. a recommended target that was never
        deep-enriched). When missing, the raw info is resolved and returned in
        ``source_info`` so the caller can persist it; recommendations are
        scraped by watch URL regardless. A failed source resolution never
        aborts the recommendation scrape.
        """
        video = self._repos.videos.get_video(video_id)
        payload: dict[str, Any] = {
            "video_id": video_id,
            "video": video,
            "source_info": None,
            "raw": None,
            "error": None,
            "unsupported": None,
            "missing": video is None,
        }
        if video is None:
            try:
                throttle.wait()
                payload["source_info"] = self._provider.extract_video(
                    _watch_url(video_id)
                )
                payload["missing"] = False
            except AcquisitionError:
                pass
        try:
            throttle.wait()
            payload["raw"] = self._provider.extract_recommendations(
                video.url if video else _watch_url(video_id)
            )
            payload["missing"] = False
        except RecommendationUnsupportedError as exc:
            payload["unsupported"] = exc
        except AcquisitionError as exc:
            payload["error"] = exc
        return payload

    def _complete_video_result(
        self,
        run,
        payload: dict[str, Any],
        *,
        channel_id: str | None,
        dedupe_run_ids: list[str] | None,
        layer_index: int | None = None,
        max_recommendations_per_video: int | None = None,
        reporter: ProgressReporter | None,
    ) -> CollectionResult:
        """Persist one video's recommendation outcome + run + dataset.

        Shared by single-video (click-to-scrape) and bulk paths. ``run`` is
        already begun with its ``target_video_id`` and lineage set.
        ``layer_index`` stamps each saved edge with the producing crawl layer.
        ``max_recommendations_per_video`` truncates the observed feed to the
        top-N edges (by position) before persistence.
        """
        errors: list = []
        video_id = payload["video_id"]

        # The source video existed only as a graph node (never deep-enriched).
        # Best-effort: persist it now that we have its raw info, so edges
        # anchor to a real Video row and the graph gains proper metadata. A
        # persistence failure never fails the run (edges anchor by id anyway).
        source_info = payload.get("source_info")
        if source_info is not None and payload["video"] is None:
            try:
                normalized = normalize_video(source_info, run.run_id)
                if normalized is not None:
                    self._repos.videos.upsert_video(normalized)
                    obs = normalize_video_observation(
                        source_info, run.run_id, normalized.video_id
                    )
                    if obs is not None:
                        self._repos.videos.save_video_observation(obs)
                    payload["video"] = normalized
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to persist source video %s for run %s: %s",
                    video_id,
                    run.run_id,
                    exc,
                )

        if payload["missing"]:
            err = self._record_error(
                run,
                EntityType.RECOMMENDATION,
                video_id,
                ErrorType.VALIDATION,
                "Source video is not persisted; cannot scrape recommendations.",
            )
            errors.append(err)
            self._finish_run(
                run, CollectionStatus.FAILED, errors,
                discovered=1, succeeded=0, entities_existing=0, comments_collected=0, failed=1
            )
            result = self._result(run, errors)
            result.entities_created = 0
            return result

        if payload["unsupported"] is not None:
            exc = payload["unsupported"]
            err = self._record_error(
                run,
                EntityType.RECOMMENDATION,
                video_id,
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
            result.entities_created = 0
            return result

        if payload["error"] is not None:
            exc = payload["error"]
            err = self._record_error(
                run,
                EntityType.RECOMMENDATION,
                video_id,
                exc.error_type,
                str(exc),
            )
            errors.append(err)
            self._finish_run(
                run, CollectionStatus.PARTIAL, errors,
                discovered=1, succeeded=0, entities_existing=0, comments_collected=0, failed=1
            )
            result = self._result(run, errors)
            result.entities_created = 0
            return result

        self._report(
            reporter,
            "recommendation/extracting",
            message="Extracting recommendations...",
        )
        edges = normalize_recommendations(
            video_id, payload["raw"], run.run_id
        )
        for edge in edges:
            edge.layer_index = layer_index
        if max_recommendations_per_video is not None:
            edges = sorted(
                edges,
                key=lambda e: e.position if e.position is not None else float("inf"),
            )
            if len(edges) > max_recommendations_per_video:
                self._report(
                    reporter,
                    "recommendation/top_n",
                    discovered=len(edges),
                    message=(
                        f"Keeping top {max_recommendations_per_video} of "
                        f"{len(edges)} recommendation(s) for {video_id}"
                    ),
                )
                edges = edges[:max_recommendations_per_video]
        if dedupe_run_ids:
            existing = self._existing_pairs(dedupe_run_ids)
            kept = [
                e
                for e in edges
                if (e.source_video_id, e.recommended_video_id) not in existing
            ]
            if len(kept) != len(edges):
                self._report(
                    reporter,
                    "recommendation/dedup",
                    succeeded=len(kept),
                    message=(
                        f"skipped {len(edges) - len(kept)} edge(s) already "
                        "observed in an earlier run"
                    ),
                )
            edges = kept

        self._report(
            reporter,
            "recommendation/edges_found",
            discovered=len(edges),
            message=f"Found {len(edges)} recommendations",
        )
        saved = []
        for edge in edges:
            result = self._repos.recommendations.save_recommendation(edge)
            if result.created:
                saved.append(edge)

        dataset_id = self._persist_run_dataset(
            run,
            saved,
            channel_id=channel_id,
            layer_index=layer_index,
            reporter=reporter,
        )

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
        result.entities_created = len(saved)
        result.dataset_id = dataset_id
        self._report(
            reporter,
            "recommendation/complete",
            succeeded=len(saved),
            message=f"Recommendation scrape complete: {len(saved)} edge(s) saved",
        )
        logger.info(
            "recommendation run %s: %d edge(s) for source %s",
            run.run_id,
            len(saved),
            video_id,
        )
        return result

    def _begin_recommendation_run(
        self,
        target_url: str,
        parent_run_id: str | None,
        source_kind: str,
        layer_index: int | None = None,
    ):
        """Begin a recommendation run with provenance (parent + trigger).

        ``layer_index`` stamps the run with a crawl layer and records it in the
        trigger's ``depth``; ``None`` (legacy callers) keeps ``depth=1``.
        """
        run = self._begin_run(RunType.RECOMMENDATION, target_url)
        run.parent_run_id = parent_run_id
        run.layer_index = layer_index
        run.config_json["trigger"] = {
            "kind": source_kind,
            "parent_run_id": parent_run_id,
            "depth": layer_index if layer_index is not None else 1,
        }
        self._repos.runs.update_run(run)
        return run

    def _existing_pairs(self, run_ids: list[str]) -> set[tuple[str, str]]:
        """(source, target) pairs already observed in the given runs."""
        pairs: set[tuple[str, str]] = set()
        for run_id in run_ids:
            for edge in self._repos.recommendations.list_recommendation_edges(
                run_id=run_id
            ):
                pairs.add((edge.source_video_id, edge.recommended_video_id))
        return pairs

    def _persist_run_dataset(
        self,
        run,
        edges: list,
        *,
        channel_id: str | None,
        layer_index: int | None = None,
        reporter: ProgressReporter | None,
    ) -> str | None:
        """Auto-persist the run's observed edges as a scoped dataset.

        The dataset is scoped to this recommendation run (``run_ids`` is now
        honored for recommendation rows) and records machine-queryable lineage
        (trigger run, parent run, source kind). When ``layer_index`` is set the
        name and lineage carry the crawl layer. A persistence failure is logged
        and never fails the collection run.
        """
        if not edges:
            return None
        try:
            from SocialScienceResearch.services.dataset_service import DatasetService

            dataset_service = DatasetService(self._repos)
            trigger_run_id = run.parent_run_id or run.run_id
            source_kind = (run.config_json.get("trigger") or {}).get("kind", "single")
            if layer_index is not None:
                name = (
                    f"Recommendation Layer {layer_index} - source {trigger_run_id}"
                )
                description = (
                    f"Auto-persisted layer {layer_index} recommendation edges for "
                    f"run {run.run_id} of {run.target_video_id or 'video'}; "
                    f"triggered by {trigger_run_id} ({source_kind}); "
                    f"{len(edges)} edge(s)."
                )
                lineage = {
                    "trigger_run_id": trigger_run_id,
                    "parent_run_id": run.parent_run_id,
                    "source_kind": source_kind,
                    "layer_index": layer_index,
                    "depth": layer_index,
                }
            else:
                name = (
                    f"Recommendation Run {run.run_id} - {run.target_video_id or 'video'} "
                    f"[source {trigger_run_id}]"
                )
                description = (
                    f"Auto-persisted dataset for recommendation run {run.run_id} "
                    f"of {run.target_video_id or 'video'}; triggered by "
                    f"{trigger_run_id} ({source_kind}); {len(edges)} edge(s)."
                )
                lineage = {
                    "trigger_run_id": trigger_run_id,
                    "parent_run_id": run.parent_run_id,
                    "source_kind": source_kind,
                    "depth": 1,
                }
            dataset = dataset_service.create_dataset(
                name=name,
                description=description,
                entity_type="recommendation",
                include_raw=False,
                run_ids=[run.run_id],
                channel_ids=[channel_id] if channel_id else None,
                video_ids=[run.target_video_id] if run.target_video_id else None,
                member_ids=[e.recommended_video_id for e in edges],
                criteria=None,
                variable_selection=None,
                lineage=lineage,
            )
            self._report(
                reporter,
                "recommendation/dataset_persisted",
                message="Persisted recommendation results as a dataset",
            )
            return dataset.dataset_id
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to auto-persist recommendation run %s as dataset: %s",
                run.run_id,
                exc,
            )
            return None