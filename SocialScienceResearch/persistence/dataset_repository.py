"""Excel-backed repository for datasets and their chunked members.

A *minimal store-backed* implementation (mirroring the shared behaviour of
``_ExcelEntityRepository`` in ``persistence.excel_repository``, which is not
edited here): it goes straight to ``WorkbookStore`` and the
``persistence.serialization`` helpers.

Member lists are persisted as **chunked row projections** (ADR-0001: a single
Excel cell must stay below ~32k chars). Each ``dataset_members`` row carries a
bounded JSON array of member ``{variable: value}`` dicts under ``member_json``,
keyed by ``{dataset_id}::{chunk_index}``. Datasets whose members span more than
one chunk are flagged via ``Dataset.overflow``.

Delete is implemented by *blanking* rows in place (the store offers no delete
API): ``read_rows`` skips fully-blank rows and the ``get_*`` methods guard on
the key column, so a blanked slot can never re-surface as an entity. The one
deliberate private coupling is ``WorkbookStore._wb`` - clearing cells cannot be
expressed through the store's public API without editing ``excel_workbook.py``
(out of scope), and the store's documented single-writer, in-memory model makes
direct cell writes safe.
"""

from __future__ import annotations

import json
from typing import Any

from SocialScienceResearch.domain.dataset_models import Dataset
from SocialScienceResearch.persistence.excel_workbook import WorkbookStore
from SocialScienceResearch.persistence.serialization import (
    headers_for,
    model_to_row,
    row_to_model,
)

_DATASET_SHEET = "datasets"
_MEMBER_SHEET = "dataset_members"
_MEMBER_HEADERS = ["row_id", "dataset_id", "chunk_index", "member_json"]

#: Bounded JSON payload per member chunk (safety margin below Excel's ~32k).
_MAX_CHUNK_CHARS = 28000


def blank_row(store: WorkbookStore, sheet: str, key_field: str, key: Any) -> None:
    """Clear every cell of the row identified by ``key`` (in place).

    Uses the store's cached index to locate the row, then writes ``None`` over
    all header cells so ``read_rows`` (which skips fully-blank rows) and the
    ``get_*`` key-column guards hide it. The index entry is kept: a later upsert
    of the same key reuses the slot in place.
    """
    if key is None:
        return
    location = store._ensure_index(sheet, key_field).get(str(key))
    if location is None:
        return
    sheet_name, excel_row = location
    ws = store._wb[sheet_name]
    headers = store._headers.get(sheet, [])
    for column in range(1, len(headers) + 1):
        cell = ws.cell(row=excel_row, column=column)
        cell.value = None


class DatasetRepository:
    """Dataset headers (``datasets``) + chunked member rows (``dataset_members``)."""

    def __init__(self, store: WorkbookStore) -> None:
        self._store = store
        store.ensure_sheet(_DATASET_SHEET, headers_for(Dataset))
        store.ensure_sheet(_MEMBER_SHEET, _MEMBER_HEADERS)

    # ------------------------------------------------------------------
    # Dataset headers
    # ------------------------------------------------------------------
    def save_dataset(self, dataset: Dataset) -> None:
        """Persist (upsert) a dataset header, idempotent by ``dataset_id``."""
        self._store.upsert_row(
            _DATASET_SHEET, "dataset_id", headers_for(Dataset), model_to_row(dataset)
        )

    def get_dataset(self, dataset_id: str) -> Dataset | None:
        row = self._store.find_row(_DATASET_SHEET, "dataset_id", dataset_id)
        if row is None or row.get("dataset_id") != dataset_id:
            return None
        return row_to_model(Dataset, row)  # type: ignore[return-value]

    def list_datasets(self) -> list[Dataset]:
        return [
            row_to_model(Dataset, r)  # type: ignore[return-value]
            for r in self._store.read_rows(_DATASET_SHEET, key_field="dataset_id")
        ]

    def delete_dataset(self, dataset_id: str) -> None:
        """Blank the header row and all member chunks of a dataset."""
        blank_row(self._store, _DATASET_SHEET, "dataset_id", dataset_id)
        self._clear_dataset_members(dataset_id)

    # ------------------------------------------------------------------
    # Chunked members
    # ------------------------------------------------------------------
    def save_members(self, dataset_id: str, members: list[dict[str, Any]]) -> int:
        """Replace the dataset's members with ``members``, chunked.

        Members are row projections (dicts keyed by variable name). Existing
        chunks for the dataset are blanked first, so re-saving is idempotent
        even when the member count shrinks. Returns the number of chunks
        written (``> 1`` means ``Dataset.overflow``).
        """
        self._clear_dataset_members(dataset_id)
        chunks = self._chunk_members(members)
        for index, payload in enumerate(chunks):
            row_id = f"{dataset_id}::{index}"
            self._store.upsert_row(
                _MEMBER_SHEET,
                "row_id",
                _MEMBER_HEADERS,
                {
                    "row_id": row_id,
                    "dataset_id": dataset_id,
                    "chunk_index": index,
                    "member_json": payload,
                },
            )
        return len(chunks)

    def list_members(self, dataset_id: str) -> list[dict[str, Any]]:
        """Return every member row projection, in stored (chunk) order."""
        members: list[dict[str, Any]] = []
        for row in self._store.read_rows(_MEMBER_SHEET, key_field="row_id"):
            if row.get("dataset_id") != dataset_id:
                continue
            payload = row.get("member_json")
            if payload:
                members.extend(json.loads(payload))
        return members

    def dataset_member_count(self, dataset_id: str) -> int:
        """Number of member rows for a dataset."""
        count = 0
        for row in self._store.read_rows(_MEMBER_SHEET, key_field="row_id"):
            if row.get("dataset_id") != dataset_id:
                continue
            payload = row.get("member_json")
            if payload:
                count += len(json.loads(payload))
        return count

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @classmethod
    def _chunk_members(cls, members: list[dict[str, Any]]) -> list[str]:
        """Split member projections into bounded JSON chunks (by char budget)."""
        chunks: list[str] = []
        current: list[dict[str, Any]] = []
        size = 0
        for member in members:
            encoded = json.dumps(member, ensure_ascii=False, default=str)
            if current and size + len(encoded) + 2 > _MAX_CHUNK_CHARS:
                chunks.append(json.dumps(current, ensure_ascii=False, default=str))
                current, size = [], 0
            current.append(member)
            size += len(encoded) + 2
        if current:
            chunks.append(json.dumps(current, ensure_ascii=False, default=str))
        return chunks

    def _clear_dataset_members(self, dataset_id: str) -> None:
        members = self._store.read_rows(_MEMBER_SHEET, key_field="row_id")
        for row in members:
            if row.get("dataset_id") == dataset_id:
                blank_row(self._store, _MEMBER_SHEET, "row_id", row.get("row_id"))