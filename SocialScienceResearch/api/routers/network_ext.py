"""B6: Full network analytics router.

Endpoints for network-wide metrics, temporal slices, paginated edges and
graph exports (graphml/edgelist/gexf). Extends RecommendationGraphService;
backed by ``NetworkAnalyticsService`` (lazily built on ``app.state`` via
:func:`get_service`).

Routes (all under the configured API prefix):

* ``GET /network/metrics`` - aggregate network statistics;
* ``GET /network/temporal`` - per-run slices + consecutive-run growth;
* ``GET /network/edges`` - cursor-paginated edge listing;
* ``GET /network/export`` - graphml/edgelist/gexf download;
* ``GET /network/channels`` - lightweight channel projection.

Owned by the B6 module agent. Do NOT edit ``api/app.py`` from here.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from SocialScienceResearch.api.routers.common import get_service, paginated
from SocialScienceResearch.services.network_analytics_service import (
    ChannelProjection,
    EdgeRow,
    NetworkAnalyticsService,
    NetworkMetrics,
    TemporalResult,
)
from SocialScienceResearch.services.pagination import Paginated

router = APIRouter()

DEFAULT_PAGE_SIZE = 50


def _service(request: Request) -> NetworkAnalyticsService:
    return get_service(
        request,
        "network_analytics",
        lambda: NetworkAnalyticsService(request.app.state.services["repos"]),
    )


def _edge_key(edge: dict) -> tuple[str, ...]:
    return (edge["source_video_id"], edge["recommended_video_id"])


@router.get(
    "/network/metrics",
    tags=["network"],
    response_model=NetworkMetrics,
)
def network_metrics(
    request: Request,
    run_id: str | None = Query(None),
    top_n: int = Query(10, ge=1, le=500),
):
    """Aggregate statistics for the whole recommendation network (or a run)."""
    return _service(request).metrics(run_id=run_id, top_n=top_n)


@router.get(
    "/network/temporal",
    tags=["network"],
    response_model=TemporalResult,
)
def network_temporal(
    request: Request,
    runs: str = Query(
        "", description="Comma-separated run ids, e.g. runs=a,b,c"
    ),
):
    """Per-run network slices plus growth between consecutive requested runs."""
    run_ids = [r for r in (part.strip() for part in runs.split(",")) if r]
    return _service(request).temporal(run_ids)


@router.get(
    "/network/edges",
    tags=["network"],
    response_model=Paginated[EdgeRow],
)
def network_edges(
    request: Request,
    run_id: str | None = Query(None),
    cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
):
    """Cursor-paginated list of observed recommendation edges."""
    return paginated(
        _service(request).edges(run_id=run_id),
        cursor=cursor,
        page_size=page_size,
        key=_edge_key,
    )


@router.get("/network/export", tags=["network"])
def network_export(
    request: Request,
    format: str = Query("graphml"),
    run_id: str | None = Query(None),
):
    """Download the recommendation network as graphml/edgelist/gexf.

    Unknown formats raise ``ValueError`` (mapped to a 400 by the app).
    """
    filename, content, media_type = _service(request).export_edges(
        run_id=run_id, format=format
    )
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/network/channels",
    tags=["network"],
    response_model=ChannelProjection,
)
def network_channels(request: Request, run_id: str | None = Query(None)):
    """Lightweight channel projection: distinct channels seen on edges."""
    return _service(request).channel_projection(run_id=run_id)