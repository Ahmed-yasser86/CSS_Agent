"""B3: Comment analytics + longitudinal/history router.

Endpoints for comment participation/replies/velocity decay analytics
(``CommentAnalyticsService``) and longitudinal channel/video histories, run
deltas and observation gaps (``LongitudinalService``). Comment selection goes
through ``QueryService`` (wiring the previously-unwired ``CommentFilter``).

Routes are declared as relative paths; the app includes this router under
``settings.api.prefix`` (e.g. ``/api/v1/social-science``). List endpoints use
opaque cursor pagination and return the ``{items, next_cursor, has_more,
total}`` envelope.

Owned by the B3 module agent. Do NOT edit ``api/app.py`` from here.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from SocialScienceResearch.api.routers.common import get_service, paginated
from SocialScienceResearch.services.comment_analytics_service import (
    CommentAnalyticsService,
    ParticipationAnalytics,
    ReplyMetrics,
    VelocityDecay,
)
from SocialScienceResearch.services.longitudinal_service import (
    ChannelHistoryPoint,
    LongitudinalService,
    RunDeltaReport,
    VideoHistoryPoint,
)
from SocialScienceResearch.services.pagination import Paginated

router = APIRouter()

#: Default page size for cursor-paginated list endpoints (matches api/app.py).
DEFAULT_PAGE_SIZE = 50


def _comment_analytics(request: Request) -> CommentAnalyticsService:
    return get_service(
        request,
        "comment_analytics",
        lambda: CommentAnalyticsService(request.app.state.services["repos"]),
    )


def _longitudinal(request: Request) -> LongitudinalService:
    return get_service(
        request,
        "longitudinal",
        lambda: LongitudinalService(request.app.state.services["repos"]),
    )


def _history_key(point) -> tuple[str, ...]:
    return (point.observed_at.isoformat(), point.observation_id)


# ----------------------------------------------------------------------
# Comment analytics
# ----------------------------------------------------------------------
@router.get(
    "/videos/{video_id}/comments/analytics/participation",
    tags=["analytics"],
    response_model=ParticipationAnalytics,
)
def participation_analytics(video_id: str, request: Request):
    """Unique vs repeat author participation for a video's comments."""
    return _comment_analytics(request).participation(video_id)


@router.get(
    "/videos/{video_id}/comments/analytics/replies",
    tags=["analytics"],
    response_model=ReplyMetrics,
)
def reply_analytics(video_id: str, request: Request):
    """Reply rate and thread-size distribution for a video's comments."""
    return _comment_analytics(request).reply_metrics(video_id)


@router.get(
    "/videos/{video_id}/comments/analytics/velocity",
    tags=["analytics"],
    response_model=VelocityDecay,
)
def velocity_decay_analytics(
    video_id: str, request: Request, bucket: str = Query("day")
):
    """Comment counts per hour/day bucket plus upload-relative decay shares."""
    return _comment_analytics(request).velocity_decay(video_id, bucket=bucket)


# ----------------------------------------------------------------------
# Longitudinal histories
# ----------------------------------------------------------------------
@router.get(
    "/channels/{channel_id}/history",
    tags=["corpus"],
    response_model=Paginated[ChannelHistoryPoint],
)
def channel_history(
    channel_id: str,
    request: Request,
    cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
):
    """All channel observations, oldest first, with per-step growth %."""
    points = _longitudinal(request).channel_history(channel_id)
    return paginated(points, cursor=cursor, page_size=page_size, key=_history_key)


@router.get(
    "/videos/{video_id}/history",
    tags=["corpus"],
    response_model=Paginated[VideoHistoryPoint],
)
def video_history(
    video_id: str,
    request: Request,
    cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
):
    """All video observations, oldest first, with per-step growth %."""
    points = _longitudinal(request).video_history(video_id)
    return paginated(points, cursor=cursor, page_size=page_size, key=_history_key)


# ----------------------------------------------------------------------
# Run deltas (longitudinal)
# ----------------------------------------------------------------------
@router.get("/runs/delta", tags=["runs"], response_model=RunDeltaReport)
def run_delta(request: Request, from_run: str = Query(...), to_run: str = Query(...)):
    """Diff two run snapshots: per-metric change + growth, new/disappeared."""
    return _longitudinal(request).run_deltas(from_run, to_run)


@router.get("/runs/{run_id}/deltas", tags=["runs"], response_model=RunDeltaReport)
def single_run_deltas(run_id: str, request: Request):
    """Diff one run against the previous run of the same type."""
    return _longitudinal(request).run_entity_deltas(run_id)