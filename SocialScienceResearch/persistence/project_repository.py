"""Excel-backed repository for persisted ResearchProjects (ADR-0002 Phase D).

A *minimal store-backed* implementation over the ``projects`` sheet (same
pattern as :mod:`persistence.dataset_repository`): it mirrors the shared
behaviour of ``_ExcelEntityRepository`` without editing
``persistence.excel_repository``. Deletes blank rows in place via
:func:`persistence.dataset_repository.blank_row`; ``get_project`` guards on the
key column so a blanked slot never re-surfaces.
"""

from __future__ import annotations

from SocialScienceResearch.domain.dataset_models import Project
from SocialScienceResearch.persistence.dataset_repository import blank_row
from SocialScienceResearch.persistence.excel_workbook import WorkbookStore
from SocialScienceResearch.persistence.serialization import (
    headers_for,
    model_to_row,
    row_to_model,
)

_PROJECT_SHEET = "projects"


class ProjectRepository:
    """Persisted ResearchProjects, sheet ``projects``."""

    def __init__(self, store: WorkbookStore) -> None:
        self._store = store
        store.ensure_sheet(_PROJECT_SHEET, headers_for(Project))

    def save_project(self, project: Project) -> None:
        """Persist (upsert) a project, idempotent by ``project_id``."""
        self._store.upsert_row(
            _PROJECT_SHEET, "project_id", headers_for(Project), model_to_row(project)
        )

    def get_project(self, project_id: str) -> Project | None:
        row = self._store.find_row(_PROJECT_SHEET, "project_id", project_id)
        if row is None or row.get("project_id") != project_id:
            return None
        return row_to_model(Project, row)  # type: ignore[return-value]

    def list_projects(self) -> list[Project]:
        return [
            row_to_model(Project, r)  # type: ignore[return-value]
            for r in self._store.read_rows(_PROJECT_SHEET, key_field="project_id")
        ]

    def update_project(self, project: Project) -> None:
        self.save_project(project)

    def delete_project(self, project_id: str) -> None:
        blank_row(self._store, _PROJECT_SHEET, "project_id", project_id)