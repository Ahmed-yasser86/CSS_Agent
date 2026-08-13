"""Dataset construction, quality and export service (B7).

A dataset is a *materialized, immutable row set* from the corpus:

* :meth:`create_dataset` snapshots the whole ``entity_type`` population;
* :meth:`create_from_project` snapshots the rows matching a persisted
  :class:`Project`'s research query, projected onto its ``variable_selection``
  (or all reported columns when none is chosen).

Rows are resolved through ``QueryService.resolve_latest_rows`` (observed
metrics resolved to their *latest* observation) and, for project datasets,
filtered by ``domain.query.evaluate_query`` over ``QueryGroup`` semantics.
Member ids are the entity's id field of each row (``video_id``/``comment_id``/
``channel_id``/``recommended_video_id``); members are persisted as chunked row
projections (see ``DatasetRepository``). With ``include_raw=True`` the per-
member ``raw_json`` payloads are snapshotted to a JSON sidecar per dataset
under ``{data_dir}/raw`` (never inside Excel, following the transcript-artifact
precedent).
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

from SocialScienceResearch.config.settings import SocialScienceSettings
from SocialScienceResearch.domain.dataset_models import (
    ColumnCoverage,
    Dataset,
    DatasetQualityReport,
)
from SocialScienceResearch.domain.query import (
    QueryContext,
    QueryGroup,
    evaluate_query,
)
from SocialScienceResearch.persistence.base import Repositories
from SocialScienceResearch.persistence.dataset_repository import DatasetRepository
from SocialScienceResearch.persistence.project_repository import ProjectRepository
from SocialScienceResearch.services.quality_service import QualityService
from SocialScienceResearch.services.query_service import QueryService
from SocialScienceResearch.utils.idgen import new_id, utcnow

#: id field of the member row per entity (mirrors what resolve_latest_rows emits).
_ID_FIELD: dict[str, str] = {
    "video": "video_id",
    "comment": "comment_id",
    "channel": "channel_id",
    "recommendation": "recommended_video_id",
    "author": "author_id",
}


class DatasetService:
    """Build, inspect, quality-check and export materialized datasets."""

    def __init__(
        self,
        repos: Repositories,
        settings: SocialScienceSettings | None = None,
    ) -> None:
        self._repos = repos
        self._settings = settings or SocialScienceSettings()
        self._datasets = DatasetRepository(repos.store)
        self._projects = ProjectRepository(repos.store)
        self._quality = QualityService(repos)
        self._query = QueryService(repos, settings)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
def create_dataset(
        self,
        name: str,
        description: str | None = None,
        entity_type: str = "video",
        include_raw: bool = False,
        run_ids: list[str] | None = None,
        channel_ids: list[str] | None = None,
        video_ids: list[str] | None = None,
