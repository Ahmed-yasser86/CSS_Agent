# Phase 5: UX Enhancements, Dataset Scoping & Sampling Fixes

**Date:** 2026-08-12  
**Status:** In Progress

---

## 1. `extra_forbidden` on `video_criteria` / `comment_criteria`

### Root Cause
The running backend server is **stale** — it was started before our Phase 4 changes added `video_criteria` and `comment_criteria` to `CollectionSpec`. The running process does not have the updated `CollectionSpec` model.

### Evidence
- `SocialScienceResearch/domain/collection.py` **does** have `video_criteria: QueryGroup | None` and `comment_criteria: QueryGroup | None` fields.
- `openapi.json` (regenerated) includes both fields at the `CollectionSpec` schema.
- A direct Python construction with the same payload works correctly.

### Fix
**Restart the backend server:**
```bash
# If running via uvicorn (from repo root):
# 1. Kill the existing process
# 2. Restart:
uvicorn SocialScienceResearch.api:create_app --factory --reload
```
The `--reload` flag auto-restarts on file changes. Without it, a manual restart is required to pick up schema changes.

### Prevention
Consider documenting that every time `CollectionSpec` is extended, a server restart is required to pick up the new Pydantic model. This is a known limitation of loading Python modules at startup.

---

## 2. Enhance Sampling UX (Friendly Criteria Filters)

### Problem
The current `collect-target-form.tsx` uses a raw `QueryBuilder` component for `video_criteria` and `comment_criteria`. The `QueryBuilder` is a technical, nested tree editor (AND/OR/NOT groups with multiple conditions) that most researchers find confusing — it presents a JSON-like tree structure rather than the simple filter-by-variable style found on the **Explorer page**.

The Explorer page's `FilterBar` (in `record-explorer.tsx`) provides a friendlier pattern:
- Pick a **variable** from a dropdown (populated with actual column names from the current entity)
- Pick an **operator** (eq, gt, contains, in, etc.)
- Enter a **value** (text, number, or comma-separated for `in`/`not_in`)
- Click **Add** to create a chip/pill showing the condition
- Chips can be removed individually

This is immediately understandable by non-technical researchers.

### UX Goal
Replace the `QueryBuilder` in `collect-target-form.tsx` with an **explorer-style criteria editor** for both `video_criteria` and `comment_criteria`. The editor should:
1. Show an entity-specific dropdown of available variables (e.g., `view_count`, `like_count`, `duration`, `upload_date`, `title`, etc.)
2. Show a dropdown of valid operators for the selected variable's data type
3. Show a value input appropriate to the type (date picker for dates, number input for int/float, text for strings)
4. Add a chip when the user clicks "Add condition"
5. Remove chips individually (X button)
6. Produce a single-level `QueryGroup` with `operator: "AND"` containing all conditions (no nested groups for the "simple" experience)
7. Provide quick preset filters as one-click shortcuts (e.g., "Top 10% by views", "Long videos (>10min)", "Published this year", "High engagement")

**Preset ideas:**
| Preset Label | QueryGroup conditions |
|---|---|
| Top 10% by views | `view_count` `top_pct` 10 |
| Long-form videos | `duration` `gt` 600 (10+ min) |
| Shorts only | `is_short` `eq` true |
| Published this year | `upload_date` `gte` Jan 1 of current year |
| High engagement | `like_count` `gt` median (computed) |
| Comments with likes | `like_count` `gt` 0 |

### Implementation Notes
- Reuse the `VariableMeta[]` from `useResearchVariables(entity)` to populate variable dropdowns.
- The friendly filter component should produce a `QueryGroup` (AND of flat conditions) that matches what `evaluate_query` in `domain/query.py` expects.
- The component is used by both `collect-target-form.tsx` (for video/comment criteria) and should also be available in `dataset-builder.tsx` for dataset scoping filters.

### Files to Modify
- `ui/src/components/features/collect-target-form.tsx` — replace `QueryBuilder` with the new friendly component
- `ui/src/components/features/query-builder.tsx` — may need a new simpler variant (`SimpleCriteriaEditor` or `FilterCriteriaBar`)
- `ui/src/lib/types.ts` — ensure `QueryGroup`/`QueryCondition` support is already in place (it is)

---

## 3. "Scrape All Comments" Feature

### Problem
The **Max comments per video** field in the collection form accepts a number, but users have no way to say "I want all comments with no cap". The current behavior requires the user to know that a large number (e.g., 999999) means "all" — this is not obvious.

### Solution
Add a checkbox/toggle **"Scrape all comments (no cap)"** that appears alongside the max-comments input in the advanced panel. When checked:
- The max-comments input is disabled
- `scrape_all_comments: true` is sent in the `CollectionSpec`
- Backend interprets this as `max_comments_per_video = None` (unlimited)

### Implementation

#### Backend
1. `domain/collection.py` — add `scrape_all_comments: bool | None = None` field to `CollectionSpec`
2. `domain/collection.py` `effective()` — when `scrape_all_comments is True`, override `max_comments_per_video` to `None`
3. `services/collection_service.py` `_persist_comments` — `max_comments` from effective is already `None` if unset; the cap `if max_comments is not None and max_comments > 0: included = included[:max_comments]` naturally handles unlimited when `max_comments is None` (skips the slice)
4. `acquisition/yt_dlp_adapter.py` `_extract_video` — when `max_comments_per_video` from settings is `None`, pass `(None, None, None)` to yt-dlp's `getcomments` options (already the case when unset)

#### Frontend
1. Add state: `const [scrapeAllComments, setScrapeAllComments] = useState(false);`
2. Add checkbox in the max-comments section of the advanced panel: `"Scrape all comments (no cap)"`
3. When `scrapeAllComments` is true, disable the `maxComments` input field
4. In `buildSpec()`: add `if (scrapeAllComments) spec.scrape_all_comments = true;`
5. In `effective()`: when `scrape_all_comments` is true, `max_comments_per_video` is set to `None` (no cap)

### Files to Modify
- `SocialScienceResearch/domain/collection.py` — add field + validator + effective()
- `SocialScienceResearch/services/collection_service.py` — no logic change needed (already handles None cap)
- `SocialScienceResearch/config/settings.py` — no change needed
- `ui/src/lib/types.ts` — add `scrape_all_comments?: boolean | null` to `CollectionSpec`
- `ui/src/components/features/collect-target-form.tsx` — add the checkbox + state wiring

---

## 4. Dataset Creation: Scope by Runs, Channels, Videos with Explorer Filters

### Problem
The current `DatasetBuilder` only supports two source modes:
- **Direct (raw rows)** — snapshots the entire entity population
- **From project** — uses a persisted project's `research_query` and `variable_selection`

Users find the "From project" mode confusing (what is a project?). They want to build datasets directly by:
1. Selecting specific **runs** (collection runs)
2. Selecting specific **channels**
3. Selecting specific **videos**
4. Applying **filter criteria** (like the Explorer page) to narrow the data
5. Selecting which **variables/columns** to include

### Solution
Extend `CreateDatasetRequest` and `DatasetService.create_dataset` to support direct corpus scoping with filter criteria — no project required.

#### Backend Design

**`domain/dataset_models.py` — `CreateDatasetRequest`:**
```python
class CreateDatasetRequest(BaseModel):
    # ... existing fields ...
    # NEW: corpus scoping
    run_ids: list[str] = Field(default_factory=list)       # filter to rows seen in these runs
    channel_ids: list[str] = Field(default_factory=list)   # filter to rows from these channels
    video_ids: list[str] = Field(default_factory=list)     # filter to rows from these videos
    # NEW: filter criteria (mirrors project research_query without entity/context)
    criteria: dict[str, Any] | None = None  # QueryGroup dict (no entity prefix)
    variable_selection: list[str] = Field(default_factory=list)  # override project variable selection
```

**`services/dataset_service.py` — `create_dataset`:**
```python
def create_dataset(
    self,
    name: str,
    description: str | None = None,
    entity_type: str = "video",
    include_raw: bool = False,
    # NEW:
    run_ids: list[str] | None = None,
    channel_ids: list[str] | None = None,
    video_ids: list[str] | None = None,
    criteria: dict | None = None,    # QueryGroup dict
    variable_selection: list[str] | None = None,
) -> Dataset:
```

**Row scoping logic:**
1. Call `self._query.resolve_latest_rows(entity)` to get the full population.
2. If `run_ids` is non-empty: filter rows where `row["run_id"]` (or equivalent, e.g., `first_observed_run_id` for videos) is in `run_ids`.
   - For videos: `first_observed_run_id` field exists
   - For comments: `first_observed_run_id` field exists
   - For channels: `first_observed_run_id` field exists
3. If `channel_ids` is non-empty: filter rows by `channel_id` field.
4. If `video_ids` is non-empty: filter rows by `video_id` field.
5. If `criteria` is non-empty: parse as `QueryGroup` and apply `evaluate_query(entity, root, rows)`.
6. Apply `variable_selection` (column projection) if provided.
7. Register and return the dataset.

**Important:** Scopes can be combined. If multiple scopes are set, the result is the **intersection** (AND) of all filters (rows must match all specified scopes).

**Backward compatibility:** `project_id` path continues to work as-is. The new scoping fields are only used when `project_id` is absent.

**Dataset source_projection** should record the scope for provenance:
```python
source_projection = {
    "entity": entity,
    "scope": {
        "run_ids": run_ids,
        "channel_ids": channel_ids,
        "video_ids": video_ids,
    },
    "criteria_hash": query_digest(criteria) if criteria else None,
    "variable_selection": variable_selection,
    ...
}
```

#### Frontend Design

**`dataset-builder.tsx` — New source modes:**
| Mode | Description |
|---|---|
| Direct (raw rows) | Snapshot entire population (existing) |
| From runs | Select run IDs from a list |
| From channels | Select channel IDs from a list |
| From videos | Select video IDs (or by channel) |
| From project | Existing project-based mode |

**UI flow:**
1. Source type selector (existing "raw" / "project" toggle, extended with "runs" / "channels" / "videos")
2. When a scope type is selected, show a multi-select picker:
   - **Runs**: fetch via `getRuns()` (already exists), show run IDs + status + date
   - **Channels**: fetch via `getChannels()` (need to add API) or reuse explorer; show channel ID + title
   - **Videos**: fetch via `getChannelVideos()` (already exists) or explorer; show video ID + title
3. Show the **Criteria Filter Bar** (friendly editor from task #2) so users can add conditions (e.g., `view_count > 1000`, `upload_date after 2024-01-01`) — same as the Explorer filters
4. **Variable selection**: existing comma-separated text input, or better: a multi-select from the variable catalogue (populated from `useResearchVariables(entity)`)
5. **Include raw** checkbox (existing)

**API changes:**
- `GET /runs` — already exists, returns list of `CollectionRun`
- `GET /channels` — does not exist as a list endpoint. Add `GET /channels` (returns `Paginated[Channel]`). Alternatively, reuse the explorer API for listing channels: `GET /explorer/channels` (already returns columns + rows). A simple list endpoint is cleaner for the picker.
- `GET /videos?channel_id=X` — already exists via `getChannelVideos`
- For videos without channel filter: `GET /videos` (list all) — also exists

**New API endpoint for channels list:**
```python
@router.get("/channels", tags=["channels"], response_model=Paginated[Channel])
def list_channels(request: Request, cursor: str | None = None, page_size: int = Query(50)):
    # Returns all channels with basic info (channel_id, title, handle)
```

#### Files to Modify
**Backend:**
- `SocialScienceResearch/domain/dataset_models.py` — extend `CreateDatasetRequest`
- `SocialScienceResearch/services/dataset_service.py` — extend `create_dataset`
- `SocialScienceResearch/api/routers/datasets.py` — pass new fields to service
- `SocialScienceResearch/api/routers/channels.py` — add `GET /channels` list endpoint (if not already there)
- `SocialScienceResearch/api/openapi.json` — regenerate

**Frontend:**
- `ui/src/lib/dataset-types.ts` — extend `CreateDatasetInput`
- `ui/src/services/datasets.ts` — add channel list fetch
- `ui/src/components/features/datasets/dataset-builder.tsx` — add scope pickers + criteria editor
- `ui/src/components/features/datasets/dataset-library.tsx` — update dataset card to show scope info

---

## 5. Testing Requirements

| Feature | Test File | Coverage |
|---|---|---|
| `scrape_all_comments` field + effective override | `tests/test_spec_and_transcripts.py` | Add test: `test_scrape_all_comments_overrides_cap` |
| `video_criteria` / `comment_criteria` scoping in dataset | `tests/test_dataset_service.py` | Add tests for run_ids, channel_ids, video_ids filters |
| Criteria validation (invalid variable → error) | `tests/test_spec_and_transcripts.py` | Already covers via model validator |
| Frontend types compile | `ui/` TypeScript | Run `npx tsc --noEmit` |
| Backend API accepts new dataset fields | `tests/test_api_*.py` | Add integration test |
| OpenAPI snapshot up to date | `tests/test_openapi_snapshot.py` | Run `python scripts/dump_openapi.py` |

---

## 6. API Contract Summary

### CreateDatasetRequest (updated)
```json
{
  "name": "string",
  "description": "string | null",
  "entity_type": "video | comment | channel | recommendation | author | null",
  "include_raw": false,
  "project_id": "string | null",
  "run_ids": [],
  "channel_ids": [],
  "video_ids": [],
  "criteria": {
    "operator": "AND | OR | NOT",
    "conditions": [
      { "variable": "string", "operator": "eq | gt | ...", "value": any }
    ]
  },
  "variable_selection": []
}
```

### CollectionSpec (updated)
```json
{
  "targets": [...],
  "collect_comments": true,
  "max_comments_per_video": 100,
  "scrape_all_comments": true,   // <-- when true, max_comments is ignored (unlimited)
  "comment_min_likes": 0,
  "comment_date_from": "ISO date",
  "comment_date_to": "ISO date",
  "collect_transcripts": false,
  "enrich_video_stats": false,
  "max_videos_to_enrich": null,
  "max_videos_per_channel": null,
  "video_criteria": { "operator": "AND", "conditions": [...] },
  "comment_criteria": { "operator": "AND", "conditions": [...] },
  "sampling_seed": 42
}
```

---

## 7. Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| Server restart instruction not followed by user | High | Document clearly; consider adding a startup version check that warns if schema is stale |
| Dataset scoping query performance (large corpuses) | Medium | Add indexes on `first_observed_run_id`, `channel_id`, `video_id` in repositories |
| Frontend scope picker API calls are expensive | Medium | Add pagination + search; cache runs/channels/videos list |
| QueryCondition null fields (quantile_n/quartile) cause issues | Low | Already validated: backend accepts nulls |

---

## 8. Estimated Effort

| Task | Estimate |
|---|---|
| Write MD | 1 hour |
| Fix `extra_forbidden` (restart + verify) | 15 min |
| Backend: `scrape_all_comments` | 1 hour |
| Backend: dataset scoping | 2-3 hours |
| Frontend: scrape_all_comments checkbox | 1 hour |
| Frontend: friendly criteria filter component | 3-4 hours |
| Frontend: dataset builder scoping UI | 3-4 hours |
| Testing + openapi regeneration | 1 hour |
| **Total** | **13-16 hours** |
