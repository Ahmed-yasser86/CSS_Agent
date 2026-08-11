"""Collection service: orchestrates channel and video acquisition workflows.

Responsibilities
----------------
* Create and track a :class:`CollectionRun` per workflow (provenance).
* Extract raw data through the :class:`AcquisitionProvider`.
* Normalize and persist entities + run-scoped observations (longitudinal).
* Capture every per-entity failure as a :class:`CollectionError` (no silent
  drops) and reflect it in the run's status (``success``/``partial``/``failed``).
* Accept a researcher-defined :class:`CollectionSpec` (targets, comment
  criteria, transcript collection, enrichment depth, quotas) and resolve it
  against the module defaults so the *resolved* configuration a run executed
  is always recorded in ``run.config_json``.
* Persist transcript artifacts externally and record explicit transcript
  availability (available / missing / unsupported - never fabricated).
* Idempotency: re-running is safe (upserts + observation appends).

This service depends only on the provider interface and the repository
interfaces - never on yt-dlp or Excel directly.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Protocol

from SocialScienceResearch.acquisition import (
    AcquisitionError,
    AcquisitionProvider,
    TranscriptUnsupportedError,
)
from SocialScienceResearch.acquisition.normalization import (
    normalize_channel,
    normalize_channel_observation,
    normalize_comments,
    normalize_video,
    normalize_video_observation,
)
from SocialScienceResearch.config.settings import SocialScienceSettings
from SocialScienceResearch.domain.collection import CollectionSpec
from SocialScienceResearch.domain.enums import (
    CollectionStatus,
    EntityType,
    ErrorType,
    RunType,
    TargetKind,
    TranscriptStatus,
)
from SocialScienceResearch.domain.models import (
    CollectionError,
    CollectionRun,
    TranscriptRecord,
)
from SocialScienceResearch.domain.query import QueryGroup, evaluate_query
from SocialScienceResearch.persistence.base import Repositories
from SocialScienceResearch.utils.idgen import new_id, new_run_id, utcnow
from SocialScienceResearch.utils.logger import get_logger, log_error, log_success

from .results import CollectionResult

logger = get_logger(__name__)


class ProgressReporter(Protocol):
    """Receives incremental progress from a collection run."""

    def __call__(
        self,
        *,
        stage: str,
        discovered: int = 0,
        succeeded: int = 0,
        failed: int = 0,
        message: str | None = None,
    ) -> None: ...


def _provider_version() -> str | None:
    try:
        from yt_dlp.version import __version__  # type: ignore[attr-defined]

        return __version__
    except Exception:  # noqa: BLE001
        return None


def _comment_like_count(raw: dict[str, Any]) -> int | None:
    """Best-effort like count of a raw comment payload (may be a string)."""
    value = raw.get("like_count")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _comment_ts(raw: dict[str, Any]) -> datetime | None:
    """Best-effort UTC timestamp of a raw comment payload."""
    value = raw.get("timestamp")
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=utcnow().tzinfo)
    except (TypeError, ValueError, OSError):
        return None


def _raw_int(raw: dict[str, Any], key: str) -> int | None:
    """Best-effort int of a raw dict value (may arrive as a string)."""
    value = raw.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _raw_bool(raw: dict[str, Any], key: str) -> bool | None:
    """Best-effort bool of a raw dict value (lenient about types)."""
    value = raw.get(key)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value) if value in (0, 1) else None
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return None


def _video_criteria_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Build a criteria row (keyed by variable name) from a raw video entry.

    Mirrors :meth:`QueryService._video_rows`; observed counts resolve to the
    values the *entry itself* reports (the latest we know at collection time).
    """
    video = normalize_video(raw, "")
    return {
        "channel_id": video.channel_id if video else raw.get("channel_id"),
        "title": raw.get("title"),
        "description": raw.get("description"),
        "duration": _raw_int(raw, "duration"),
        "upload_date": video.upload_date if video else None,
        "upload_timestamp": video.upload_timestamp if video else None,
        "tags": raw.get("tags") or [],
        "categories": raw.get("categories") or [],
        "language": raw.get("language"),
        "live_status": raw.get("live_status"),
        "availability": raw.get("availability"),
        "age_limit": _raw_int(raw, "age_limit"),
        "is_short": _raw_bool(raw, "is_short"),
        "thumbnail_url": raw.get("thumbnail"),
        "view_count": _raw_int(raw, "view_count"),
        "like_count": _raw_int(raw, "like_count"),
        "comment_count": _raw_int(raw, "comment_count"),
        "favorite_count": _raw_int(raw, "favorite_count"),
    }


def _comment_criteria_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Build a criteria row (keyed by variable name) from a raw comment entry.

    Mirrors :meth:`QueryService._comment_rows`. Reply count / removal state
    are not answerable at collection time and stay ``None`` (explicitly
    unknown, never fabricated); missing likes likewise leave ``like_count``
    ``None`` so ``is_null``/``not_null`` still work.
    """
    parent = raw.get("parent")
    return {
        "author_id": raw.get("author_id") or raw.get("author_channel_id"),
        "author_name": raw.get("author"),
        "comment_text": raw.get("text"),
        "published_at": _comment_ts(raw),
        "is_reply": bool(parent),
        "parent_comment_id": str(parent) if parent else None,
        "root_comment_id": None,
        "is_author": _raw_bool(raw, "author_is_uploader"),
        "like_count": _comment_like_count(raw),
        "reply_count": None,
        "is_removed": None,
    }


def _apply_criteria(
    entity: str,
    criteria: QueryGroup | None,
    raws: list[dict[str, Any]],
    row_builder: Any,
) -> tuple[list[dict[str, Any]], int]:
    """Filter ``raws`` against a researcher :class:`QueryGroup`.

    Returns ``(kept_raws, excluded)``. Rows are keyed by variable name so the
    evaluator (``evaluate_query``) is shared with the read-side query engine.
    Excluded entries are the researcher's explicit sampling decision, not
    collection errors.
    """
    if criteria is None:
        return raws, 0
    if isinstance(criteria, dict):
        criteria = QueryGroup.model_validate(criteria)
    rows = []
    for index, raw in enumerate(raws):
        row = dict(row_builder(raw))
        row["_candidate_index"] = index
        rows.append(row)
    matched = evaluate_query(entity, criteria, rows)
    kept = {row["_candidate_index"] for row in matched}
    return (
        [raws[i] for i in range(len(raws)) if i in kept],
        len(raws) - len(kept),
    )


def _as_datetime(value: Any) -> datetime | None:
    """Coerce an ISO-8601 string or datetime back to an aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=utcnow().tzinfo)
        return parsed
    return None


class CollectionService:
    """High-level orchestration of YouTube data acquisition workflows."""

    def __init__(
        self,
        provider: AcquisitionProvider,
        repos: Repositories,
        settings: SocialScienceSettings | None = None,
    ) -> None:
        self._provider = provider
        self._repos = repos
        self._settings = settings or SocialScienceSettings()

    # ------------------------------------------------------------------
    # Public workflows (single-target, legacy signatures preserved)
    # ------------------------------------------------------------------
    def collect_channel(
        self,
        channel_url: str,
        *,
        spec: CollectionSpec | None = None,
        reporter: ProgressReporter | None = None,
    ) -> CollectionResult:
        """Collect a channel: metadata, video discovery, optional enrichment."""
        spec = spec or CollectionSpec.for_channel(channel_url)
        return self._run_channel_target(spec, channel_url, reporter)

    def collect_video(
        self,
        video_url: str,
        *,
        spec: CollectionSpec | None = None,
        reporter: ProgressReporter | None = None,
    ) -> CollectionResult:
        """Collect a single video: metadata, statistics, comments, transcript."""
        spec = spec or CollectionSpec.for_video(video_url)
        return self._run_video_target(spec, video_url, reporter)

    def collect_recommendations(self, video_url: str) -> CollectionResult:
        """Collect the recommendation context of one video.

        Lives in :class:`RecommendationService`; the base class intentionally
        has no recommendation workflow.
        """
        raise NotImplementedError(
            "Recommendation runs live in RecommendationService; use that class."
        )

    def collect(
        self,
        spec: CollectionSpec,
        reporter: ProgressReporter | None = None,
    ) -> list[CollectionResult]:
        """Execute a full collection experiment across every target.

        Returns one :class:`CollectionResult` per target in spec order; the
        same resolved spec drives every target so one experiment definition is
        reproducible end-to-end.
        """
        results: list[CollectionResult] = []
        for target in spec.targets:
            if target.kind == TargetKind.CHANNEL:
                results.append(self._run_channel_target(spec, target.url, reporter))
            elif target.kind == TargetKind.VIDEO:
                results.append(self._run_video_target(spec, target.url, reporter))
            else:
                results.append(self.collect_recommendations(target.url))
        return results

    # ------------------------------------------------------------------
    # Channel workflow
    # ------------------------------------------------------------------
    def _run_channel_target(
        self,
        spec: CollectionSpec,
        channel_url: str,
        reporter: ProgressReporter | None,
    ) -> CollectionResult:
        effective = spec.effective(self._settings)
        run = self._begin_run(RunType.CHANNEL, channel_url, spec)
        errors: list[CollectionError] = []
        try:
            extract = self._provider.extract_channel(channel_url)
        except AcquisitionError as exc:
            errors.append(
                self._record_error(
                    run, EntityType.CHANNEL, None, exc.error_type, str(exc)
                )
            )
            self._finish_run(run, CollectionStatus.FAILED, errors, discovered=0)
            return self._result(run, errors)

        self._report(
            reporter,
            "channel/extract",
            discovered=len(extract.videos),
            message=f"channel metadata extracted, {len(extract.videos)} videos discovered",
        )

        channel = normalize_channel(extract.channel, run.run_id)
        if channel is None:
            errors.append(
                self._record_error(
                    run,
                    EntityType.CHANNEL,
                    None,
                    ErrorType.VALIDATION,
                    "Could not resolve a channel id from the extraction result.",
                )
            )
            self._finish_run(run, CollectionStatus.FAILED, errors, discovered=0)
            return self._result(run, errors)

        run.target_channel_id = channel.channel_id
        self._repos.channels.upsert_channel(channel)
        ch_obs = normalize_channel_observation(
            extract.channel, run.run_id, channel.channel_id
        )
        if ch_obs is not None:
            self._repos.channels.save_channel_observation(ch_obs)

        created_videos, existing_videos, comment_total, skipped = self._collect_videos(
            run, channel.channel_id, extract.videos, errors, effective, reporter
        )

        status = (
            CollectionStatus.PARTIAL if errors else CollectionStatus.SUCCESS
        )
        self._finish_run(
            run,
            status,
            errors,
            discovered=len(extract.videos),
            succeeded=created_videos + existing_videos,
            failed=len(errors),
            notes=(
                [f"{len(skipped)} video(s) skipped deep enrichment"]
                if skipped
                else None
            ),
        )
        log_success(
            f"Channel run {run.run_id}: {created_videos} new videos, "
            f"{comment_total} comments"
        )
        result = self._result(run, errors, skipped=skipped)
        result.entities_created = created_videos
        result.entities_existing = existing_videos
        result.comments_collected = comment_total
        return result

    def _collect_videos(
        self,
        run: CollectionRun,
        channel_id: str,
        raw_videos: list[dict[str, Any]],
        errors: list[CollectionError],
        effective: dict[str, Any],
        reporter: ProgressReporter | None,
    ) -> tuple[int, int, int, list[dict[str, Any]]]:
        """Persist discovered videos (and optional deep stats/comments).

        Returns ``(created, existing, comments_collected, skipped)`` where
        ``skipped`` records videos that were *not* deep-enriched (with the
        reason) so enrichment skips are observable, never silent.
        """
        created = 0
        existing = 0
        comment_total = 0
        skipped: list[dict[str, Any]] = []
        enrich = bool(effective["enrich_video_stats"])
        max_comments = effective["max_comments_per_video"]

        # Researcher video criteria + per-channel quota are applied *before*
        # persistence so the run collects exactly the researcher's sample.
        # Excluded videos are a sampling decision, never an error.
        kept_raws, criteria_excluded = _apply_criteria(
            "video", effective["video_criteria"], raw_videos, _video_criteria_row
        )
        cap = effective["max_videos_per_channel"]
        if cap is not None and cap > 0 and len(kept_raws) > cap:
            kept_raws = kept_raws[:cap]
        if criteria_excluded or (cap and len(raw_videos) - len(kept_raws) - criteria_excluded):
            self._report(
                reporter,
                "channel/videos",
                message=(
                    f"video criteria applied: {criteria_excluded} excluded, "
                    f"{len(raw_videos) - len(kept_raws) - criteria_excluded} beyond "
                    "the per-channel quota"
                ),
            )

        for index, raw in enumerate(kept_raws):
            video = normalize_video(raw, run.run_id)
            if video is None:
                continue
            if video.channel_id is None:
                video.channel_id = channel_id
            upsert = self._repos.videos.upsert_video(video)
            if upsert.created:
                created += 1
            else:
                existing += 1
            self._report(
                reporter,
                "channel/videos",
                discovered=len(raw_videos),
                succeeded=created + existing,
                failed=len(errors),
                message=f"video {video.video_id} persisted",
            )

            if enrich:
                can_enrich, reason = self._can_enrich(
                    index, created + existing, effective
                )
                if can_enrich:
                    try:
                        info = self._provider.extract_video(video.url)
                        obs = normalize_video_observation(
                            info, run.run_id, video.video_id
                        )
                        if obs is not None:
                            self._repos.videos.save_video_observation(obs)
                        if effective["collect_comments"]:
                            comment_total += self._persist_comments(
                                run,
                                info.get("comments") or [],
                                video.video_id,
                                errors,
                                effective,
                                reporter,
                            )
                        if effective["collect_transcripts"]:
                            self._collect_transcript(
                                run, video, errors, effective, reporter
                            )
                        if self._settings.scraper.request_delay_seconds:
                            time.sleep(self._settings.scraper.request_delay_seconds)
                    except AcquisitionError as exc:
                        err = self._record_error(
                            run, EntityType.VIDEO, video.video_id, exc.error_type, str(exc)
                        )
                        errors.append(err)
                else:
                    # Enrichment was requested but bounded by quota: record why
                    # this video was skipped so it is observable on the result.
                    skipped.append(
                        {"video_id": video.video_id, "reason": reason}
                    )
                    # Persist what the flat entry actually provides (may be None).
                    obs = normalize_video_observation(raw, run.run_id, video.video_id)
                    if obs is not None:
                        self._repos.videos.save_video_observation(obs)
            else:
                # Persist what the flat entry actually provides (may be None).
                obs = normalize_video_observation(raw, run.run_id, video.video_id)
                if obs is not None:
                    self._repos.videos.save_video_observation(obs)

        return created, existing, comment_total, skipped

    def _can_enrich(
        self, index: int, collected: int, effective: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """Decide whether a video may be deep-enriched.

        Returns ``(allowed, reason)``; ``reason`` is non-None exactly when the
        video is skipped, so callers can surface the decision.
        """
        cap = effective["max_videos_to_enrich"]
        if cap is None:
            return True, None
        if collected > cap:
            return (
                False,
                f"enrichment quota reached ({cap} of {cap} videos); "
                "skipped deep extraction",
            )
        return True, None

    # ------------------------------------------------------------------
    # Video workflow
    # ------------------------------------------------------------------
    def _run_video_target(
        self,
        spec: CollectionSpec,
        video_url: str,
        reporter: ProgressReporter | None,
    ) -> CollectionResult:
        effective = spec.effective(self._settings)
        run = self._begin_run(RunType.VIDEO, video_url, spec)
        errors: list[CollectionError] = []
        try:
            info = self._provider.extract_video(video_url)
        except AcquisitionError as exc:
            errors.append(
                self._record_error(
                    run, EntityType.VIDEO, None, exc.error_type, str(exc)
                )
            )
            self._finish_run(run, CollectionStatus.FAILED, errors, discovered=1)
            return self._result(run, errors)

        self._report(
            reporter,
            "video/extract",
            discovered=1,
            message="video metadata extracted",
        )

        video = normalize_video(info, run.run_id)
        if video is None:
            errors.append(
                self._record_error(
                    run,
                    EntityType.VIDEO,
                    None,
                    ErrorType.VALIDATION,
                    "Could not resolve a video id from the extraction result.",
                )
            )
            self._finish_run(run, CollectionStatus.FAILED, errors, discovered=1)
            return self._result(run, errors)

        run.target_video_id = video.video_id
        self._repos.videos.upsert_video(video)
        obs = normalize_video_observation(info, run.run_id, video.video_id)
        if obs is not None:
            self._repos.videos.save_video_observation(obs)
        self._report(
            reporter,
            "video/metadata",
            discovered=1,
            succeeded=1,
            message=f"video {video.video_id} persisted",
        )

        comment_total = 0
        if effective["collect_comments"]:
            comment_total = self._persist_comments(
                run,
                info.get("comments") or [],
                video.video_id,
                errors,
                effective,
                reporter,
            )

        if effective["collect_transcripts"]:
            self._collect_transcript(run, video, errors, effective, reporter)

        # Accounting: the video itself persisted and counts as succeeded even
        # when a downstream capability (comments / transcripts) failed.
        status = (
            CollectionStatus.SUCCESS if not errors else CollectionStatus.PARTIAL
        )
        self._finish_run(
            run,
            status,
            errors,
            discovered=1,
            succeeded=1,
            failed=len(errors),
        )
        log_success(
            f"Video run {run.run_id}: {video.video_id}, {comment_total} comments"
        )
        result = self._result(run, errors)
        result.entities_created = 1
        result.comments_collected = comment_total
        return result

    # ------------------------------------------------------------------
    # Comment persistence (researcher criteria applied)
    # ------------------------------------------------------------------
    def _persist_comments(
        self,
        run: CollectionRun,
        raw_comments: list[dict[str, Any]],
        video_id: str,
        errors: list[CollectionError],
        effective: dict[str, Any],
        reporter: ProgressReporter | None,
    ) -> int:
        """Persist comments + observations; returns the number stored.

        Applies the researcher's inclusion criteria (min likes, date window,
        cap) *before* persistence. Excluded comments are not errors - they are
        the researcher's explicit sampling decision - and are reported as such.
        """
        if not raw_comments:
            return 0

        min_likes = effective["comment_min_likes"]
        date_from = _as_datetime(effective["comment_date_from"])
        date_to = _as_datetime(effective["comment_date_to"])
        max_comments = effective["max_comments_per_video"]

        # Researcher comment criteria run first over the same raw payloads;
        # excluded comments are the researcher's sampling decision.
        included, criteria_excluded = _apply_criteria(
            "comment", effective["comment_criteria"], raw_comments, _comment_criteria_row
        )

        survivors: list[dict[str, Any]] = []
        filtered = 0
        for raw in included:
            if min_likes is not None:
                likes = _comment_like_count(raw)
                if likes is not None and likes < min_likes:
                    filtered += 1
                    continue
            if date_from is not None or date_to is not None:
                ts = _comment_ts(raw)
                if ts is not None:
                    if date_from is not None and ts < date_from:
                        filtered += 1
                        continue
                    if date_to is not None and ts > date_to:
                        filtered += 1
                        continue
            survivors.append(raw)

        if max_comments is not None and max_comments > 0:
            survivors = survivors[:max_comments]
            filtered += max(0, len(included) - len(survivors))

        excluded = criteria_excluded + filtered

        comments, observations = normalize_comments(survivors, video_id, run.run_id)
        for comment in comments:
            self._repos.comments.upsert_comment(comment)
        for observation in observations:
            self._repos.comments.save_comment_observation(observation)

        if excluded:
            logger.info(
                "video %s: %d comment(s) excluded by researcher criteria",
                video_id,
                excluded,
            )
            self._report(
                reporter,
                "comments",
                succeeded=len(comments),
                message=f"{len(comments)} comments persisted, {excluded} excluded by criteria",
            )
        return len(comments)

    # ------------------------------------------------------------------
    # Transcript persistence (explicit availability, never fabricated)
    # ------------------------------------------------------------------
    def _collect_transcript(
        self,
        run: CollectionRun,
        video,
        errors: list[CollectionError],
        effective: dict[str, Any],
        reporter: ProgressReporter | None,
    ) -> None:
        """Best-effort transcript acquisition for one video.

        Writes the caption artifact externally, records explicit status, and
        records a ``transcript_unsupported`` error when the provider cannot
        supply captions at all. Absence of captions (``MISSING``) is an
        availability outcome, not a collection failure.
        """
        lang = self._settings.scraper.transcript_lang
        try:
            extract = self._provider.extract_transcript(video.url, lang=lang)
        except TranscriptUnsupportedError as exc:
            err = self._record_error(
                run,
                EntityType.VIDEO,
                video.video_id,
                exc.error_type,
                str(exc),
                retryable=False,
            )
            errors.append(err)
            self._save_transcript_record(
                run,
                video.video_id,
                lang,
                TranscriptStatus.UNSUPPORTED,
                str(exc),
            )
            logger.warning("video %s: %s", video.video_id, str(exc))
            return
        except AcquisitionError as exc:
            err = self._record_error(
                run, EntityType.VIDEO, video.video_id, exc.error_type, str(exc)
            )
            errors.append(err)
            self._save_transcript_record(
                run,
                video.video_id,
                lang,
                TranscriptStatus.UNSUPPORTED,
                str(exc),
            )
            return

        if extract.status == TranscriptStatus.AVAILABLE:
            abs_path = self._repos.transcripts.write_artifact(
                video.video_id, extract.content
            )
            relative = str(
                abs_path.relative_to(self._settings.repository.data_dir).as_posix()
            )
            video.transcript_path = relative
            video.transcript_status = TranscriptStatus.AVAILABLE.value
            video.transcript_lang = extract.lang or lang
            self._repos.videos.upsert_video(video)
            self._save_transcript_record(
                run,
                video.video_id,
                extract.lang or lang,
                TranscriptStatus.AVAILABLE,
                path=relative,
            )
            log_success(f"video {video.video_id}: transcript saved to {relative}")
            self._report(
                reporter,
                "transcripts",
                succeeded=1,
                message=f"transcript saved to {relative}",
            )
        else:
            self._save_transcript_record(
                run,
                video.video_id,
                lang,
                extract.status,
                extract.message,
            )
            logger.info(
                "video %s: transcript %s%s",
                video.video_id,
                extract.status.value,
                f" ({extract.message})" if extract.message else "",
            )

    def _save_transcript_record(
        self,
        run: CollectionRun,
        video_id: str,
        lang: str | None,
        status: TranscriptStatus,
        message: str | None = None,
        *,
        path: str | None = None,
    ) -> None:
        record = TranscriptRecord(
            transcript_id=new_id("tx"),
            video_id=video_id,
            collection_run_id=run.run_id,
            path=path,
            lang=lang,
            status=status,
            message=message,
            observed_at=utcnow(),
        )
        self._repos.transcripts.save_transcript(record)

    # ------------------------------------------------------------------
    # Run bookkeeping
    # ------------------------------------------------------------------
    def _begin_run(
        self,
        run_type: RunType,
        target_url: str,
        spec: CollectionSpec | None = None,
    ) -> CollectionRun:
        run = CollectionRun(
            run_id=new_run_id(),
            run_type=run_type,
            target_url=target_url,
            started_at=utcnow(),
            status=CollectionStatus.RUNNING,
            provider="yt-dlp",
            provider_version=_provider_version(),
            config_json=(
                spec.effective(self._settings) if spec is not None else self._config_snapshot()
            ),
        )
        if run_type == RunType.CHANNEL:
            run.target_channel_id = None
        if run_type == RunType.VIDEO:
            run.target_video_id = None
        self._repos.runs.create_run(run)
        return run

    def _finish_run(
        self,
        run: CollectionRun,
        status: CollectionStatus,
        errors: list[CollectionError],
        *,
        discovered: int,
        succeeded: int = 0,
        failed: int = 0,
        notes: list[str] | None = None,
    ) -> None:
        run.status = status
        run.finished_at = utcnow()
        run.entities_discovered = discovered
        run.entities_succeeded = succeeded
        run.entities_failed = failed
        error_count = len(self._repos.runs.list_errors(run.run_id)) or len(errors)
        base_notes = [f"{error_count} error(s) recorded"] if error_count else []
        run.notes = base_notes + list(notes or [])
        self._repos.runs.update_run(run)

    def _record_error(
        self,
        run: CollectionRun,
        entity_type: EntityType,
        entity_id: str | None,
        error_type: ErrorType,
        message: str,
        *,
        retryable: bool | None = None,
    ) -> CollectionError:
        error = CollectionError(
            error_id=new_id("err"),
            run_id=run.run_id,
            entity_type=entity_type,
            entity_id=entity_id,
            error_type=error_type,
            message=message,
            occurred_at=utcnow(),
            retryable=bool(
                retryable
                if retryable is not None
                else error_type in (ErrorType.NETWORK, ErrorType.RATE_LIMIT)
            ),
        )
        self._repos.runs.record_error(error)
        log_error(f"run {run.run_id} | {entity_type.value}: {message}")
        return error

    def _config_snapshot(self) -> dict[str, Any]:
        collection = self._settings.collection
        return {
            "collect_comments": collection.collect_comments,
            "max_comments_per_video": collection.max_comments_per_video,
            "extract_flat": collection.extract_flat,
            "enrich_video_stats": collection.enrich_video_stats,
            "max_videos_to_enrich": collection.max_videos_to_enrich,
            "max_videos_per_channel": collection.max_videos_per_channel,
            "sampling_seed": self._settings.sampling.default_seed,
            "video_criteria": None,
            "comment_criteria": None,
        }

    def _result(
        self,
        run: CollectionRun,
        errors: list[CollectionError],
        *,
        skipped: list[dict[str, Any]] | None = None,
    ) -> CollectionResult:
        return CollectionResult(
            run_id=run.run_id,
            run_type=run.run_type,
            status=run.status,
            target_url=run.target_url,
            target_id=run.target_channel_id or run.target_video_id,
            entities_discovered=run.entities_discovered,
            entities_created=0,
            entities_existing=0,
            entities_failed=run.entities_failed,
            comments_collected=0,
            errors=errors or self._repos.runs.list_errors(run.run_id),
            skipped=skipped or [],
            started_at=run.started_at,
            finished_at=run.finished_at,
        )

    def _report(
        self,
        reporter: ProgressReporter | None,
        stage: str,
        *,
        discovered: int = 0,
        succeeded: int = 0,
        failed: int = 0,
        message: str | None = None,
    ) -> None:
        if reporter is not None:
            reporter(
                stage=stage,
                discovered=discovered,
                succeeded=succeeded,
                failed=failed,
                message=message,
            )
