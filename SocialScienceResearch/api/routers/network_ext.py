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
    ChannelGraphPayload,
    ChannelProjection,
    EdgeRow,
    NetworkAnalyticsService,
    NetworkGraph,
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


def _edge_key(edge) -> tuple[str, ...]:
    """Feed-rank pagination key: source video, position, then identity.

    Positions are zero-padded so string comparison mirrors numeric order and
    ``None`` (unknown rank) sorts after ranked edges. All keys are strings so
    cursor tokens remain comparable inside ``page_sorted``.
    
    Handles both dict and EdgeRow objects.
    """
    # Handle both dict and EdgeRow objects
    if hasattr(edge, "__dict__"):
        # EdgeRow object
        position = edge.position
        position_key = f"{position:08d}" if position is not None else "~"
        return (
            edge.source_video_id,
            position_key,
            edge.run_id or "",
            edge.recommended_video_id,
        )
    else:
        # dict
        position = edge["position"]
        position_key = f"{position:08d}" if position is not None else "~"
        return (
            edge["source_video_id"],
            position_key,
            edge["run_id"] or "",
            edge["recommended_video_id"],
        )


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
    "/network/graph",
    tags=["network"],
    response_model=NetworkGraph | ChannelGraphPayload,
)
def network_graph(
    request: Request,
    run_id: str | None = Query(None),
    channel_id: str | None = Query(None, description="Filter edges by channel_id"),
    channel_scope: str = Query(
        "source",
        description="Which edge endpoint a channel filter matches: source|target|either",
    ),
    projection: str = Query(
        "video",
        description="Graph projection: video | channel",
    ),
):
    """Enriched node/edge payload for the interactive graph UI.

    Nodes carry composite labels (``[ID] + Channel Name + Video Title +
    thumbnails/metrics``) plus degree/kind/provenance; the response includes
    run and channel facets so the filter bar never derives options from the
    rendered graph. ``projection=channel`` collapses the video network into
    a channel-level graph (channels as nodes, weighted edges between them).
    """
    if projection not in ("video", "channel"):
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="projection must be video or channel")
    if channel_scope not in ("source", "target", "either"):
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="channel_scope must be source, target or either")
    service = _service(request)
    if projection == "channel":
        return service.channel_graph(
            run_id=run_id,
            channel_id=channel_id,
            channel_scope=channel_scope,
        )
    return service.graph(
        run_id=run_id,
        channel_id=channel_id,
        channel_scope=channel_scope,
    )


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
    channel_id: str | None = Query(None, description="Filter edges by channel_id"),
    channel_scope: str = Query(
        "source",
        description="Which edge endpoint a channel filter matches: source|target|either",
    ),
    cursor: str | None = Query(None, description="Opaque cursor from the previous page"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=500),
):
    """Cursor-paginated list of observed recommendation edges.
    
    Supports filtering by `run_id` and `channel_id` (source channel by default).
    """
    if channel_scope not in ("source", "target", "either"):
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="channel_scope must be source, target or either")
    return paginated(
        _service(request).edges(
            run_id=run_id, channel_id=channel_id, channel_scope=channel_scope
        ),
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