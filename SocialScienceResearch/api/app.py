"""FastAPI application for the SocialScienceResearch module.

Mounts the research API under the configured prefix (default
``/api/v1/social-science``). Endpoints map onto the service layer
(collection, sampling, analytics, recommendation network) and depend only on
the service interfaces.

The application is created via :func:`create_app`, which wires services to a
single persistence store so collection and analytics read the same data.

API hardening (B2)
------------------
* every endpoint declares a pydantic ``response_model`` (``api.schemas``);
* list endpoints use opaque cursor pagination (``services.pagination``);
* domain errors map to a single machine-readable error envelope;
* CORS origins, OpenAPI metadata and docs visibility come from settings.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from SocialScienceResearch.config.settings import SocialScienceSettings
from SocialScienceResearch.domain.collection import CollectionSpec
from SocialScienceResearch.domain.enums import RunType
from SocialScienceResearch.domain.query import (
    OPERATOR_DESCRIPTIONS,
    ResearchQueryRequest,
    SamplingSpec,
    VideoFilter,
    evaluate_query,
    preview_query,
)
from SocialScienceResearch.persistence.excel_repository import build_excel_repositories
from SocialScienceResearch.services import (
    AnalyticsService,
    CoverageReport,
    JobManager,
    QualityService,
    QueryService,
    RecommendationGraphService,
    RecommendationService,
    SamplingService,
)
from SocialScienceResearch.services.pagination import (
    CursorError,
    Paginated,
    page_sorted,
)
from SocialScienceResearch.services.sampling_service import SamplingError
from SocialScienceResearch.services.variable_registry import VariableRegistry

from .schemas import (
    ChannelCountPayload,
    ChannelOverviewPayload,
    ChannelPayload,
    CollectionErrorPayload,
    CollectionResultPayload,
    CollectionResultsPayload,
    CommentPayload,
    DatasetSummaryPayload,
    ErrorPayload,
    JobCancelPayload,
    JobFailurePayload,
    JobPayload,
    JobResultPayload,
    JobSubmitPayload,
    NetworkSummaryPayload,
    OperatorInfoPayload,
    PercentilesPayload,
    QueryPreviewResponse,
    QueryResolveResponse,
    RawVideoPayload,
    RecommendationPayload,
    RunPayload,
    SamplingResultPayload,
    ThreadPayload,
    TopVideosPayload,
    VariableMetaPayload,
    VelocityPoint,
    VideoEngagementPayload,
    VideoNetworkContextPayload,
    VideoObservationPayload,
    VideoPayload,
)

#: Default page size for cursor-paginated list endpoints.
DEFAULT_PAGE_SIZE = 50


class CollectRequest(BaseModel):
    url: str


def _services(
    settings: SocialScienceSettings, *, provider=None
) -> dict[str, Any]:
    repos = build_excel_repositories(settings.repository)
    if provider is None:
        from SocialScienceResearch.acquisition import YtDlpAcquisitionProvider

        provider = YtDlpAcquisitionProvider(
            settings=settings.scraper, collection=settings.collection
        )
    return {
        "repos": repos,
        # ``RecommendationService`` extends ``CollectionService``; using it for
        # the ``"collection"`` key wires the spec-driven recommendation target
        # (previously raised NotImplementedError from the base class).
        "collection": RecommendationService(provider, repos, settings=settings),
        "recommendations": RecommendationService(provider, repos, settings=settings),
        "analytics": AnalyticsService(repos),
        "query": QueryService(repos, settings),
        "sampling": SamplingService(repos, settings.sampling.default_seed),
        "network": RecommendationGraphService(repos),
        "quality": QualityService(repos),
        "jobs": JobManager(max_workers=settings.jobs.max_workers),
    }


def _run_key(run) -> tuple[str, ...]:
    return (run.started_at.isoformat(), run.run_id)


def _job_key(job) -> tuple[str, ...]:
    return (job.created_at.isoformat(), job.job_id)


def _video_key(video) -> tuple[str, ...]:
    return (video.video_id,)


def _channel_key(channel) -> tuple[str, ...]:
    return (channel.channel_id,)


def _obs_key(obs) -> tuple[str, ...]:
    return (obs.observed_at.isoformat(), obs.observation_id)


def _comment_key(comment) -> tuple[str, ...]:
    return (comment.comment_id,)


def _edge_key(edge) -> tuple[str, ...]:
    return (edge.recommended_video_id, edge.observation_id)


def _paginate(
    entities: list, *, cursor: str | None, page_size: int, key
) -> Paginated[Any]:
    """Slice a materialized entity list into a ``Paginated`` envelope.

    ``total`` is always populated because the repositories return in-memory
    lists (research scale), making the count free.
    """
    full = sorted(entities, key=key)
    page = page_sorted(
        full, cursor=cursor, page_size=page_size, key_func=key, total=len(full)
    )
    return Paginated(
        items=[e.model_dump() for e in page.items],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
        total=page.total,
    )


def create_app(
    settings: SocialScienceSettings | None = None, *, provider=None
) -> FastAPI:
    settings = settings or SocialScienceSettings()
    services = _services(settings, provider=provider)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        services["repos"].store.close()
        services["jobs"].shutdown()

    app = FastAPI(
        title=settings.api.title,
        version=settings.api.version,
        description=settings.api.description,
        docs_url="/docs" if settings.api.docs_enabled else None,
        redoc_url="/redoc" if settings.api.docs_enabled else None,
        lifespan=lifespan,
    )
    app.state.services = services
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Error envelope: domain errors map to machine-readable codes.
    # ------------------------------------------------------------------
    @app.exception_handler(HTTPException)
    def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorPayload(
                code=f"http_{exc.status_code}", message=str(exc.detail)
            ).model_dump(),
        )

    @app.exception_handler(SamplingError)
    def _sampling_exception_handler(request: Request, exc: SamplingError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorPayload(code="sampling_error", message=str(exc)).model_dump(),
        )

    @app.exception_handler(CursorError)
    def _cursor_exception_handler(request: Request, exc: CursorError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorPayload(code="invalid_cursor", message=str(exc)).model_dump(),
        )

    @app.exception_handler(ValueError)
    def _value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorPayload(code="invalid_argument", message=str(exc)).model_dump(),
        )

    prefix = settings.api.prefix
    repos = services["repos"]

    # ------------------------------------------------------------------
    # Phase B-D routers (split modules so they build in parallel).
    # Included BEFORE the direct routes below so literal paths such as
    # ``/runs/delta`` are never shadowed by ``/runs/{run_id}``.
    # ------------------------------------------------------------------
    from .routers import (
        comments,
        comparison,
        datasets,
        explorer,
        network_ext,
        samples,
        search,
    )

    app.include_router(comments.router, prefix=prefix)
    app.include_router(comparison.router, prefix=prefix)
    app.include_router(datasets.router, prefix=prefix)
    app.include_router(explorer.router, prefix=prefix)
    app.include_router(network_ext.router, prefix=prefix)
    app.include_router(samples.router, prefix=prefix)
    app.include_router(search.router, prefix=prefix)

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------
    @app.post(
        f"{prefix}/collect/channel",
        tags=["collection"],
        response_model=CollectionResultPayload,
    )
    def collect_channel(body: CollectRequest):
        return _collection_payload(services["collection"].collect_channel(body.url))

    @app.post(
        f"{prefix}/collect/video",
        tags=["collection"],
        response_model=CollectionResultPayload,
    )
    def collect_video(body: CollectRequest):
        return _collection_payload(services["collection"].collect_video(body.url))

    @app.post(
        f"{prefix}/collect/recommendations",
        tags=["collection"],
        response_model=CollectionResultPayload,
    )
    def collect_recommendations(body: CollectRequest):
        return _collection_payload(
            services["recommendations"].collect_recommendations(body.url)
        )

    # ------------------------------------------------------------------
    # Spec-driven collection (async jobs with progress + cancellation)
    # ------------------------------------------------------------------
    @app.post(f"{prefix}/collect", tags=["collection"], response_model=JobSubmitPayload)
    def collect_spec(spec: CollectionSpec):
        """Submit a spec-driven collection experiment; returns a job id.

        Runs in the background (worker thread) so the client can poll progress
        via ``GET /jobs/{job_id}`` and cancel via ``POST /jobs/{job_id}/cancel``.
        """

        def _worker(reporter):
            return services["collection"].collect(spec, reporter=reporter)

        job = services["jobs"].submit(_worker, kind="collect")
        return {"job_id": job.job_id}

    @app.get(f"{prefix}/jobs", tags=["jobs"], response_model=Paginated[JobPayload])
    def list_jobs(
        cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
        page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
    ):
        jobs = sorted(services["jobs"].list(), key=_job_key)
        page = page_sorted(
            jobs, cursor=cursor, page_size=page_size, key_func=_job_key, total=len(jobs)
        )
        return Paginated(
            items=[j.to_dict() for j in page.items],
            next_cursor=page.next_cursor,
            has_more=page.has_more,
            total=page.total,
        )

    @app.get(f"{prefix}/jobs/{{job_id}}", tags=["jobs"], response_model=JobPayload)
    def get_job(job_id: str):
        job = services["jobs"].get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return job.to_dict()

    @app.post(
        f"{prefix}/jobs/{{job_id}}/cancel",
        tags=["jobs"],
        response_model=JobCancelPayload,
    )
    def cancel_job(job_id: str):
        if not services["jobs"].cancel(job_id):
            raise HTTPException(
                status_code=409,
                detail=f"Job {job_id} cannot be cancelled (finished or missing)",
            )
        return {"job_id": job_id, "cancelled": True}

    @app.get(
        f"{prefix}/jobs/{{job_id}}/result",
        tags=["jobs"],
        response_model=JobResultPayload,
    )
    def job_result(job_id: str):
        job = services["jobs"].get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        if job.status.value in ("pending", "running"):
            raise HTTPException(status_code=409, detail="Job is still running")
        if job.error:
            return {"error": job.error}
        return _collect_payload_many(job.result)

    # ------------------------------------------------------------------
    # Runs (provenance)
    # ------------------------------------------------------------------
    @app.get(f"{prefix}/runs", tags=["runs"], response_model=Paginated[RunPayload])
    def list_runs(
        run_type: RunType | None = None,
        cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
        page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
    ):
        runs = repos.runs.list_runs(run_type=run_type)
        return _paginate(runs, cursor=cursor, page_size=page_size, key=_run_key)

    @app.get(f"{prefix}/runs/{{run_id}}", tags=["runs"], response_model=RunPayload)
    def get_run(run_id: str):
        run = repos.runs.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        return _run_payload(run)

    @app.get(
        f"{prefix}/runs/{{run_id}}/errors",
        tags=["runs"],
        response_model=list[CollectionErrorPayload],
    )
    def run_errors(run_id: str):
        return [e.model_dump() for e in repos.runs.list_errors(run_id)]

    # ------------------------------------------------------------------
    # Corpus / channel
    # ------------------------------------------------------------------
    @app.get(
        f"{prefix}/channels",
        tags=["corpus"],
        response_model=Paginated[ChannelPayload],
    )
    def list_channels(
        q: str | None = Query(None, description="Case-insensitive text search over title/handle/description"),
        cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
        page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
    ):
        """All channels (global picker for comparison/explorer views)."""
        channels = repos.channels.list_channels()
        if q:
            needle = q.lower()
            channels = [
                channel
                for channel in channels
                if needle in (channel.title or "").lower()
                or needle in (channel.handle or "").lower()
                or needle in (channel.description or "").lower()
            ]
        return _paginate(channels, cursor=cursor, page_size=page_size, key=_channel_key)

    @app.get(
        f"{prefix}/channels/{{channel_id}}/overview",
        tags=["corpus"],
        response_model=ChannelOverviewPayload,
    )
    def channel_overview(channel_id: str):
        overview = services["analytics"].channel_overview(channel_id)
        return {
            "channel_id": overview.channel_id,
            "observed_at": overview.observed_at,
            "subscribers": _value_payload(overview.subscriber_count),
            "videos": _value_payload(overview.video_count),
            "views": _value_payload(overview.view_count),
        }

    @app.get(
        f"{prefix}/channels/{{channel_id}}/videos",
        tags=["corpus"],
        response_model=Paginated[VideoPayload],
    )
    def channel_videos(
        channel_id: str,
        date_from: date | None = Query(None),
        date_to: date | None = Query(None),
        video_type: str | None = Query(None),
        duration_min: int | None = Query(None),
        duration_max: int | None = Query(None),
        views_min: int | None = Query(None),
        views_max: int | None = Query(None),
        upload_hour: int | None = Query(None),
        upload_weekday: int | None = Query(None),
        keywords: list[str] | None = Query(None),
        tags: list[str] | None = Query(None),
        category: str | None = Query(None),
        cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
        page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
    ):
        # NOTE: the VideoFilter fields are declared as explicit query params
        # (instead of FastAPI's model-as-query-param) because FastAPI cannot
        # mix a query parameter model with the pagination params below.
        filter = VideoFilter(
            date_from=date_from,
            date_to=date_to,
            video_type=video_type,
            duration_min=duration_min,
            duration_max=duration_max,
            views_min=views_min,
            views_max=views_max,
            upload_hour=upload_hour,
            upload_weekday=upload_weekday,
            keywords=keywords or [],
            tags=tags or [],
            category=category,
        )
        videos = services["query"].filter_videos(channel_id, filter)
        return _paginate(videos, cursor=cursor, page_size=page_size, key=_video_key)

    @app.get(
        f"{prefix}/channels/{{channel_id}}/videos/count",
        tags=["corpus"],
        response_model=ChannelCountPayload,
    )
    def channel_video_count(channel_id: str):
        return {
            "channel_id": channel_id,
            "count": len(repos.videos.list_videos(channel_id)),
        }

    @app.get(f"{prefix}/videos", tags=["corpus"], response_model=Paginated[VideoPayload])
    def list_videos(
        q: str | None = Query(None, description="Case-insensitive text search over title/description"),
        cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
        page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
    ):
        """All videos (global picker for comparison/explorer views)."""
        videos = repos.videos.list_videos()
        if q:
            needle = q.lower()
            videos = [
                video
                for video in videos
                if needle in (video.title or "").lower()
                or needle in (video.description or "").lower()
            ]
        return _paginate(videos, cursor=cursor, page_size=page_size, key=_video_key)

    @app.get(f"{prefix}/videos/{{video_id}}", tags=["corpus"], response_model=VideoPayload)
    def get_video(video_id: str):
        video = repos.videos.get_video(video_id)
        if video is None:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
        return video.model_dump()

    @app.get(
        f"{prefix}/videos/{{video_id}}/observations",
        tags=["corpus"],
        response_model=Paginated[VideoObservationPayload],
    )
    def video_observations(
        video_id: str,
        cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
        page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
    ):
        observations = repos.videos.list_video_observations(video_id)
        return _paginate(
            observations, cursor=cursor, page_size=page_size, key=_obs_key
        )

    @app.get(
        f"{prefix}/videos/{{video_id}}/raw",
        tags=["corpus"],
        response_model=RawVideoPayload,
    )
    def video_raw(video_id: str):
        video = repos.videos.get_video(video_id)
        if video is None:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
        return {"video_id": video_id, "raw_json": video.raw_json}

    @app.get(
        f"{prefix}/channels/{{channel_id}}/videos/top",
        tags=["corpus"],
        response_model=TopVideosPayload,
    )
    def channel_top_videos(
        channel_id: str,
        metric: str = Query("views"),
        n: int = Query(settings.analytics.top_n, ge=1, le=500),
    ):
        """Top videos by the latest observed engagement metric.

        Videos whose metric is MISSING are kept and annotated with
        ``availability: "missing"`` (ranked last) rather than dropped, so the
        channel-level leaderboard never silently loses videos.
        """
        field_map = {
            "views": "view_count",
            "likes": "like_count",
            "comments": "comment_count",
        }
        metric = metric.lower()
        field = field_map.get(metric, metric)
        rows: list[dict[str, Any]] = []
        for video in repos.videos.list_videos(channel_id):
            latest = repos.videos.get_latest_video_observation(video.video_id)
            value = getattr(latest, field, None) if latest is not None else None
            rows.append(
                {
                    "video_id": video.video_id,
                    "title": video.title,
                    metric: value,
                    "observed_at": latest.observed_at if latest else None,
                    "availability": "available" if value is not None else "missing",
                }
            )
        rows.sort(
            key=lambda r: (r[metric] is None, r[metric] if r[metric] is not None else 0),
            reverse=True,
        )
        return {"channel_id": channel_id, "metric": metric, "top": rows[:n]}

    # ------------------------------------------------------------------
    # Sampling
    # ------------------------------------------------------------------
    @app.post(
        f"{prefix}/channels/{{channel_id}}/videos/sample",
        tags=["sampling"],
        response_model=SamplingResultPayload,
    )
    def sample_videos(channel_id: str, spec: SamplingSpec):
        return _sampling_payload(services["sampling"].sample_videos(channel_id, spec))

    @app.post(
        f"{prefix}/videos/{{video_id}}/comments/sample",
        tags=["sampling"],
        response_model=SamplingResultPayload,
    )
    def sample_comments(video_id: str, spec: SamplingSpec):
        return _sampling_payload(services["sampling"].sample_comments(video_id, spec))

    # ------------------------------------------------------------------
    # Video analytics
    # ------------------------------------------------------------------
    @app.get(
        f"{prefix}/videos/{{video_id}}/engagement",
        tags=["analytics"],
        response_model=VideoEngagementPayload,
    )
    def video_engagement(video_id: str):
        eng = services["analytics"].video_engagement(video_id)
        return {
            "video_id": eng.video_id,
            "observed_at": eng.observed_at,
            "views": _value_payload(eng.views),
            "likes": _value_payload(eng.likes),
            "comments": _value_payload(eng.comments),
            "engagement_rate": _value_payload(eng.engagement_rate),
            "like_rate": _value_payload(eng.like_rate),
            "comment_rate": _value_payload(eng.comment_rate),
        }

    @app.get(
        f"{prefix}/videos/{{video_id}}/comments/percentiles",
        tags=["analytics"],
        response_model=PercentilesPayload,
    )
    def comment_percentiles(video_id: str):
        result = services["analytics"].comment_like_percentiles(video_id)
        return {
            "video_id": result.video_id,
            "availability": result.availability.value,
            "observed_like_counts": result.like_counts,
            "bands": result.bands,
        }

    @app.get(
        f"{prefix}/videos/{{video_id}}/comments/velocity",
        tags=["analytics"],
        response_model=list[VelocityPoint],
    )
    def comment_velocity(video_id: str, bucket: str = "day"):
        return services["analytics"].comment_velocity(video_id, bucket=bucket)

    @app.get(
        f"{prefix}/videos/{{video_id}}/comments",
        tags=["analytics"],
        response_model=Paginated[CommentPayload],
    )
    def video_comments(
        video_id: str,
        cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
        page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
    ):
        comments = repos.comments.list_comments(video_id)
        return _paginate(
            comments, cursor=cursor, page_size=page_size, key=_comment_key
        )

    @app.get(
        f"{prefix}/videos/{{video_id}}/comments/threads",
        tags=["analytics"],
        response_model=Paginated[ThreadPayload],
    )
    def video_comment_threads(
        video_id: str,
        cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
        page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
    ):
        """Root comments with their replies, preserving parent-child order."""
        pairs = [
            (root, repos.comments.list_replies(root.comment_id))
            for root in repos.comments.list_root_comments(video_id)
        ]
        full = sorted(pairs, key=lambda pair: pair[0].comment_id)
        page = page_sorted(
            full,
            cursor=cursor,
            page_size=page_size,
            key_func=lambda pair: (pair[0].comment_id,),
            total=len(full),
        )
        return Paginated(
            items=[
                {
                    "comment": root.model_dump(),
                    "replies": [r.model_dump() for r in replies],
                }
                for root, replies in page.items
            ],
            next_cursor=page.next_cursor,
            has_more=page.has_more,
            total=page.total,
        )

    # ------------------------------------------------------------------
    # Recommendation network
    # ------------------------------------------------------------------
    @app.get(
        f"{prefix}/videos/{{video_id}}/recommendations",
        tags=["network"],
        response_model=Paginated[RecommendationPayload],
    )
    def video_recommendations(
        video_id: str,
        cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
        page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
    ):
        edges = repos.recommendations.list_recommendations_for_source(video_id)
        return _paginate(edges, cursor=cursor, page_size=page_size, key=_edge_key)

    @app.get(
        f"{prefix}/network/recommendations/summary",
        tags=["network"],
        response_model=NetworkSummaryPayload,
    )
    def network_summary(
        run_id: str | None = None,
        top_n: int = Query(settings.analytics.top_n, ge=1, le=500),
    ):
        return services["network"].summary(run_id=run_id, top_n=top_n).__dict__

    @app.get(
        f"{prefix}/network/recommendations/{{video_id}}",
        tags=["network"],
        response_model=VideoNetworkContextPayload,
    )
    def network_video_context(video_id: str, run_id: str | None = None):
        return services["network"].video_context(video_id, run_id=run_id).__dict__

    # ------------------------------------------------------------------
    # Quality / coverage
    # ------------------------------------------------------------------
    @app.get(
        f"{prefix}/coverage",
        tags=["quality"],
        response_model=CoverageReport,
    )
    def coverage():
        return services["quality"].coverage()

    @app.get(
        f"{prefix}/dataset/summary",
        tags=["quality"],
        response_model=DatasetSummaryPayload,
    )
    def dataset_summary():
        return services["quality"].dataset_summary()

    # ------------------------------------------------------------------
    # Research queries (B1): variable catalogue, operators and the funnel
    # ------------------------------------------------------------------
    @app.get(
        f"{prefix}/research/variables",
        tags=["research"],
        response_model=list[VariableMetaPayload],
    )
    def research_variables(entity: str | None = Query(None)):
        """Registered research variables for an entity (all when omitted)."""
        if entity is None:
            return [v.model_dump() for v in VariableRegistry.all_variables()]
        return [v.model_dump() for v in VariableRegistry.get_variables(entity)]

    @app.get(
        f"{prefix}/research/operators",
        tags=["research"],
        response_model=list[OperatorInfoPayload],
    )
    def research_operators():
        """Operators understood by the research-query evaluator."""
        return [
            {"name": operator.value, "description": description}
            for operator, description in OPERATOR_DESCRIPTIONS.items()
        ]

    @app.post(
        f"{prefix}/research/query/preview",
        tags=["research"],
        response_model=QueryPreviewResponse,
    )
    def research_query_preview(body: ResearchQueryRequest):
        """Evaluate a research query and report the ordered funnel stages.

        ``stages`` flatten the condition tree: each stage's ``cumulative`` is
        the count matching the conditions-so-far (AND-ed prefix) and
        ``matched`` is the incremental drop. OR/NOT groups appear once.
        """
        rows = services["query"].resolve_latest_rows(
            body.entity, context=body.query_context
        )
        preview = preview_query(body.entity, body.root, rows)
        return {
            "total": preview.total,
            "stages": [stage.model_dump() for stage in preview.stages],
            "population_size": preview.population_size,
            "n": preview.n,
        }

    @app.post(
        f"{prefix}/research/query/resolve",
        tags=["research"],
        response_model=QueryResolveResponse,
    )
    def research_query_resolve(body: ResearchQueryRequest):
        """Count-only resolution of a research query (no rows returned)."""
        rows = services["query"].resolve_latest_rows(
            body.entity, context=body.query_context
        )
        matched = evaluate_query(body.entity, body.root, rows)
        return {"total": len(matched), "population_size": len(rows)}

    return app


def _collection_payload(result) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "run_type": result.run_type.value,
        "status": result.status.value,
        "target_url": result.target_url,
        "target_id": result.target_id,
        "entities_discovered": result.entities_discovered,
        "entities_created": result.entities_created,
        "entities_existing": result.entities_existing,
        "entities_failed": result.entities_failed,
        "comments_collected": result.comments_collected,
        "errors": [e.model_dump() for e in result.errors],
        "skipped": result.skipped,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
    }


def _collect_payload_many(results) -> dict[str, Any]:
    """Serialize one or many collection results into a uniform payload."""
    if isinstance(results, list):
        return {
            "target_count": len(results),
            "results": [_collection_payload(r) for r in results],
        }
    return _collection_payload(results)


def _run_payload(run) -> dict[str, Any]:
    return run.model_dump()


def _value_payload(value) -> dict[str, Any]:
    return {
        "value": value.value,
        "availability": value.availability.value,
    }


def _sampling_payload(result) -> dict[str, Any]:
    return {
        "strategy": result.strategy.value,
        "entity_type": result.entity_type,
        "population_size": result.population_size,
        "sample_size": result.sample_size,
        "entity_ids": result.entity_ids,
        "criteria_json": result.criteria_json,
        "seed": result.seed,
        "missing_metric_count": result.missing_metric_count,
    }


#: Module-level app so ``from SocialScienceResearch.api.app import app`` works
#: (used by the S0 import gate). Constructed with default settings; the
#: workbook store is opened in-memory and only written on an explicit save.
app = create_app()
