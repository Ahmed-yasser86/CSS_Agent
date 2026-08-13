"""ProjectItem service - manages project sub-items (sample groups, dataset groups).

ProjectItems allow researchers to organize samples and datasets into logical
units within a project (e.g., "Pilot Study", "Main Analysis", "Replication").
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from SocialScienceResearch.domain.dataset_models import (
    ProjectItem,
    CreateProjectItemRequest,
    UpdateProjectItemRequest,
)
from SocialScienceResearch.persistence.base import Repositories
from SocialScienceResearch.persistence.project_item_repository import ProjectItemRepository
from SocialScienceResearch.persistence.project_repository import ProjectRepository
from SocialScienceResearch.utils.idgen import new_id, utcnow


class ProjectItemService:
    """CRUD for ProjectItems within a ResearchProject."""

    def __init__(self, repos: Repositories) -> None:
        self._items = ProjectItemRepository(repos.store)
        self._projects = ProjectRepository(repos.store)  # mirrors ProjectService

    def create_item(self, project_id: str, request: CreateProjectItemRequest) -> ProjectItem:
        """Create a new project item and associate it with a project."""
        # Verify project exists
        self._projects.get_project(project_id)
        if not self._projects.get_project(project_id):
            raise ValueError(f"Project {project_id!r} not found")

        item = ProjectItem(
            item_id=new_id("item"),
            project_id=project_id,
            name=request.name,
            description=request.description,
            item_type=request.item_type,
            sample_ids=request.sample_ids,
            dataset_ids=request.dataset_ids,
            tags=request.tags,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        self._items.save_item(item)
        return item

    def get_item(self, item_id: str) -> ProjectItem:
        """Get a project item by ID."""
        item = self._items.get_item(item_id)
        if item is None:
            raise ValueError(f"ProjectItem {item_id!r} not found")
        return item

    def list_items(self, project_id: str | None = None) -> list[ProjectItem]:
        """List all project items, optionally filtered by project."""
        return self._items.list_items(project_id)

    def list_items_by_project(self, project_id: str) -> list[ProjectItem]:
        """List all items belonging to a specific project."""
        return self._items.list_items_by_project(project_id)

    def update_item(self, item_id: str, patch: UpdateProjectItemRequest) -> ProjectItem:
        """Update a project item with the provided patch."""
        current = self.get_item(item_id)
        data = current.model_dump(exclude={"created_at", "updated_at"})

        for field in ("name", "description", "sample_ids", "dataset_ids", "tags"):
            if field in patch.model_fields_set:
                data[field] = getattr(patch, field)

        updated = ProjectItem(
            **data,
            created_at=current.created_at,
            updated_at=utcnow(),
        )
        self._items.update_item(updated)
        return updated

    def add_samples(self, item_id: str, sample_ids: list[str]) -> ProjectItem:
        """Add sample IDs to a project item."""
        current = self.get_item(item_id)
        current.sample_ids = list(set(current.sample_ids + sample_ids))
        current.updated_at = utcnow()
        self._items.update_item(current)
        return current

    def remove_samples(self, item_id: str, sample_ids: list[str]) -> ProjectItem:
        """Remove sample IDs from a project item."""
        current = self.get_item(item_id)
        current.sample_ids = [s for s in current.sample_ids if s not in sample_ids]
        current.updated_at = utcnow()
        self._items.update_item(current)
        return current

    def add_datasets(self, item_id: str, dataset_ids: list[str]) -> ProjectItem:
        """Add dataset IDs to a project item."""
        current = self.get_item(item_id)
        current.dataset_ids = list(set(current.dataset_ids + dataset_ids))
        current.updated_at = utcnow()
        self._items.update_item(current)
        return current

    def remove_datasets(self, item_id: str, dataset_ids: list[str]) -> ProjectItem:
        """Remove dataset IDs from a project item."""
        current = self.get_item(item_id)
        current.dataset_ids = [d for d in current.dataset_ids if d not in dataset_ids]
        current.updated_at = utcnow()
        self._items.update_item(current)
        return current

    def delete_item(self, item_id: str) -> None:
        """Delete a project item."""
        self.get_item(item_id)  # verify exists
        self._items.delete_item(item_id)