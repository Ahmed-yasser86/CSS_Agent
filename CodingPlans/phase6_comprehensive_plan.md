# Phase 6: Live Videos Fix, Channel Videos, Run Videos, Comment Stats, Folders & Export

**Date:** 2026-08-12  
**Status:** Planning

---

## Summary

This phase addresses multiple feature requests:

1. **Fix "Scrape Live Videos Only" for channel scraping** - The current `include_live_videos` option doesn't work properly
2. **Channel Videos page** - Show all videos of a specific scraped channel
3. **Run Videos page** - Show all videos scraped in a specific run
4. **Comment Statistics** - Show likes, replies per comment in table + highest replies & unique repliers
5. **Folders Tab** - Show where Excel files are stored for datasets, samples, runs
6. **Export to Device Tab** - Export selected data to Excel sheets
7. **Fix Runs Page "Provenance Ledger" Error** - Request failed (400) when loading runs list
8. **Comment Tree Navigation** - Click any comment in explorer/comments tab to view its complete reply tree

---

## 1. Fix Live Videos Scraping (Backend)

### Problem
The current `include_live_videos` implementation in `yt_dlp_adapter.py` extracts from `/live` and `/streams` tabs but:
- Doesn't use yt-dlp's native `youtubetab` extractor with `tab` argument
- May miss videos due to pagination
- Doesn't have a "live videos ONLY" mode

### Solution
Based on yt-dlp docs (youtubeScraper.md lines 1891-1894):
- Use `youtubetab` extractor with `tab` argument: `new`, `top`, `videos`, `podcasts`, `streams`, `stacks`
- Add new CollectionSpec field: `video_tabs: string[]` to specify which tabs to extract
- Options: `videos`, `shorts`, `live` (`streams`), `playlists`, `featured`
- Add `scrape_live_only: boolean` for live-only mode

### Files to Modify
- `domain/collection.py` - Add `video_tabs` and `scrape_live_only` to `CollectionSpec`
- `config/settings.py` - Add corresponding settings
- `acquisition/yt_dlp_adapter.py` - Rewrite `_extract_channel` to use `youtubetab` extractor with `tab` argument
- `ui/src/lib/types.ts` - Add new fields to `CollectionSpec`
- `ui/src/components/features/collect-target-form.tsx` - Add UI for tab selection

---

## 2. Channel Videos Tab (Already Exists, Enhance)

The channel page at `/channels/[channelId]?tab=videos` already shows videos via `VideoCorpusBrowser`. Need to:
- Ensure it shows ALL scraped videos (not just filtered)
- Add "Scraped in run" column showing which run collected each video
- Add pagination for large channels

### Files to Modify
- `ui/src/components/features/video-corpus-browser.tsx` - Add run info column, enhance display

---

## 3. Run Videos Tab (New Feature)

Create a new tab on the Run Detail page (`/runs/[runId]?tab=videos`) showing all videos collected in that run.

### Files to Create/Modify
- `ui/src/app/runs/[runId]/page.tsx` - Add tabs support
- `ui/src/components/features/run-detail.tsx` - Add tabs and video list
- NEW: `ui/src/components/features/run-videos-browser.tsx` - Video browser for run
- Backend: Add endpoint `/runs/{run_id}/videos` to list videos in a run

---

## 4. Comment Statistics Enhancement

### Current State
I already added `like_count`, `reply_count`, `is_removed` columns to the comments table. Need to verify they work and add:

### New Requirements
- **Highest number of replies** on a single comment (max reply_count)
- **Highest number of unique repliers** - count of distinct authors who replied to a comment
- Display these as metric cards in the comments section

### Files to Modify
- Backend: Add endpoint `/videos/{video_id}/comments/stats` for max replies & unique repliers
- Frontend: `ui/src/components/features/comments-browser.tsx` - Add stat cards
- Frontend: Verify comment table shows likes/replies correctly

---

## 5. Folders Tab (New Feature)

Show where Excel files are stored for:
- Main workbook (runs, channels, videos, comments, etc.)
- Datasets (exported datasets)
- Samples (exported samples)
- Transcripts directory

### Files to Create/Modify
- Backend: Add endpoint `/system/folders` returning paths
- Frontend: NEW `ui/src/components/features/folders-tab.tsx`
- Frontend: Add "Folders" tab to main navigation or settings page

---

## 6. Export to Device Tab (New Feature)

Allow exporting selected data to Excel sheets:
- Select entity type: runs, videos, comments, channels, samples, datasets
- Select specific items (checkboxes)
- Choose columns to export
- Download as .xlsx file

### Files to Create/Modify
- Backend: Add endpoint `/export` that generates Excel from selected data
- Frontend: NEW `ui/src/components/features/export-tab.tsx`
- Frontend: Add "Export" tab to main navigation

---

## 7. Fix Runs Page "Provenance Ledger" Error

### Problem
When opening the runs page (`/runs`), the "Provenance ledger" section shows "Request failed (400)" with a Retry button. This suggests the API endpoint for listing runs is returning a 400 error.

### Root Cause Investigation Needed
- Check the `GET /runs` endpoint in `api/app.py`
- Check the `useRuns` query in `ui/src/services/queries.ts`
- Check the `getRuns` API function in `ui/src/services/api.ts`
- Likely a parameter validation issue or missing required query parameter

### Files to Investigate/Modify
- `api/app.py` - `/runs` endpoint
- `ui/src/services/api.ts` - `getRuns` function
- `ui/src/services/queries.ts` - `useRuns` hook
- `ui/src/app/runs/page.tsx` - Runs page component

---

## 8. Comment Tree Navigation from Explorer/Comments Tabs

### Problem
When clicking on a comment in the explorer tab or comments browser, users should be able to view the complete reply tree for that comment (thread view).

### Solution
- Add click handler to comment rows in `DataTable` (both explorer and comments browser)
- Navigate to `/videos/{videoId}/comments?thread={commentId}` or similar
- Use the existing `CommentTree` component to display the thread
- The thread view should show the selected comment as root with all its replies

### Files to Modify
- `ui/src/components/features/video-corpus-browser.tsx` - Add comment click handler (if comments shown)
- `ui/src/components/features/comments-browser.tsx` - Add click to view thread
- `ui/src/components/features/data-table.tsx` - Support row click actions
- `ui/src/app/videos/[videoId]/page.tsx` or comments tab - Handle thread parameter
- NEW: Thread view mode in comments browser

---

## Technical Clarification: Native yt-dlp Extraction Only

**IMPORTANT:** All YouTube scraping MUST use **only the yt-dlp Python library**. No external tools:
- ❌ NO Playwright
- ❌ NO Selenium
- ❌ NO Puppeteer
- ❌ NO browser automation
- ✅ ONLY `yt_dlp.YoutubeDL` with proper extractor arguments

The "native extraction" refers to using yt-dlp's built-in `youtubetab` extractor with the `tab` argument:
```python
opts = {
    "extractor_args": {
        "youtubetab": {
            "tab": ["videos", "shorts", "streams"]
        }
    },
    "extract_flat": "in_playlist",
    ...
}
```

This leverages yt-dlp's internal YouTube tab extraction (handling pagination, authentication, etc.) rather than manually constructing URLs for `/live`, `/streams`, `/videos` tabs.

---

## Implementation Plan (Parallel Tracks)

### Track A: Backend Core (Live Videos + Run Videos + Comment Stats + Folders + Export + Runs Fix)
1. Fix live videos scraping in `yt_dlp_adapter.py` (native yt-dlp only)
2. Add `/runs/{run_id}/videos` endpoint
3. Add `/videos/{video_id}/comments/stats` endpoint
4. Add `/system/folders` endpoint
5. Add `/export` endpoint
6. **Fix `/runs` endpoint 400 error**

### Track B: Frontend Core (Types + API + Components)
1. Update `CollectionSpec` types
2. Add new API functions in `api.ts`
3. Create `run-videos-browser.tsx`
4. Create `folders-tab.tsx`
5. Create `export-tab.tsx`
6. **Add comment thread navigation to DataTable/comments browser**

### Track C: UI Integration
1. Update collect form with tab selection
2. Add tabs to run detail page
3. Add tabs to channel page (if needed)
4. Add Folders/Export to main navigation
5. **Fix runs page error display**
6. **Add thread view mode to comments browser**

### Track D: Testing & Verification
1. Backend tests for new endpoints
2. Frontend TypeScript/build verification
3. Integration testing

---

### 1. Live Videos Fix - yt-dlp Integration

```python
# In yt_dlp_adapter.py - use youtubetab extractor with tab argument
opts = {
    "extractor_args": {
        "youtubetab": {
            "tab": ["videos", "shorts", "streams"]  # or specific tabs
        }
    },
    "extract_flat": "in_playlist",
    ...
}
```

Tabs available (from youtubeScraper.md line 1933):
- `new` - New videos
- `top` - Popular videos
- `videos` - All videos (uploads)
- `podcasts` - Podcasts
- `streams` - Live streams
- `stacks` - Stacks/playlists

### 2. New CollectionSpec Fields

```python
# domain/collection.py
class CollectionSpec(BaseModel):
    # ... existing fields ...
    video_tabs: list[str] | None = Field(default=None)  # e.g. ["videos", "shorts", "streams"]
    scrape_live_only: bool = Field(default=False)  # Only scrape live/stream videos
```

### 3. Run Videos Endpoint

```
GET /api/v1/social-science/runs/{run_id}/videos?cursor=&page_size=50
```

Returns paginated list of videos collected in that run with their metadata.

### 4. Comment Stats Endpoint

```
GET /api/v1/social-science/videos/{video_id}/comments/stats
```

Returns:
```json
{
  "max_replies": 42,
  "max_unique_repliers": 15,
  "total_replies": 1234,
  "total_unique_repliers": 567
}
```

### 5. Folders Endpoint

```
GET /api/v1/social-science/system/folders
```

Returns:
```json
{
  "workbook_path": "/path/to/youtube_research.xlsx",
  "transcripts_dir": "/path/to/transcripts",
  "datasets_dir": "/path/to/datasets",
  "samples_dir": "/path/to/samples",
  "data_dir": "/path/to/data"
}
```

### 6. Export Endpoint

```
POST /api/v1/social-science/export
{
  "entity_type": "video|comment|channel|run|sample|dataset",
  "ids": ["id1", "id2", ...],
  "columns": ["col1", "col2", ...],  // optional, default all
  "filename": "export.xlsx"  // optional
}
```

Returns: Excel file download

---

## Success Criteria

- [ ] Live videos scraping works with tab selection
- [ ] "Scrape live videos only" mode works
- [ ] Channel page shows all scraped videos with run info
- [ ] Run page has Videos tab showing run's videos
- [ ] Comment table shows likes, replies, removed status
- [ ] Comment section shows "Max Replies" and "Max Unique Repliers" stats
- [ ] Folders tab shows all data paths
- [ ] Export tab allows exporting selected data to Excel
- [ ] **Runs page loads without 400 error**
- [ ] **Click comment → view complete reply tree**
- [ ] All tests pass (backend + frontend)
- [ ] TypeScript clean, build succeeds