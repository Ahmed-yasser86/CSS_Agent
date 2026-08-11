# Phase 3 �?" Pre-scrape Filters, Channel Count Fix, Drawer Fix

**Status:** Approved �?" Planning
**Owner:** Orchestrator (opencode) + parallel module agent
**Target:** `SocialScienceResearch/`
**Date:** 2026-08-11

---

## 0. Approved Decisions (locked)

| # | Decision | Choice |
|---|---|---|
| D1 | Pre-scrape video criteria | Researcher-specified **inclusion criteria** (reusing the post-scrape `QueryGroup` tree + `evaluate_query` engine) applied at collection time to decide which discovered videos are persisted |
| D2 | Pre-scrape comment criteria | Researcher-specified **inclusion criteria** (comment variables) applied in `_persist_comments` alongside the existing min-likes/date/cap fields |
| D3 | Criteria judgment | A video/comment is kept only when the criteria **can be judged** on the data available; non-judgeable (missing variable at that stage) records are deferred (enrichment) or recorded with an explicit reason �?" **never silently dropped** |
| D4 | Channel video count | Extract the channel **Videos tab** (append `/videos`) so yt-dlp's `playlist_count` is the real video count, not the number of playlists; fall back to explicit `channel_video_count` when present |
| D5 | Drawer console error | Wrap `Drawer.Popup` in `Drawer.Viewport` per Base UI contract (restores swipe/touch-lock); no layout change for the detail drawer |
| D6 | Parallel delivery | Orchestrator implements backend + drawer fix; a module sub-agent implements the collect-form criteria UI in parallel |

---

## 1. Feature 1 �?" Pre-scrape video + comment inclusion criteria

### Business requirement

When launching a **channel** collection the researcher can, *before* scraping:

* restrict **which videos** from the channel are collected (e.g. `view_count >= 10000`, `upload_date >= 2024-01-01`, `duration between 300 and 1800`, `title contains "AI"`, `is_short == false`);
* restrict **which comments** are collected (e.g. `like_count >= 5`, `is_reply == false`, `comment_text contains "when"`, `published_at >= ...`).

The **same variable catalogue and operator set** as the post-scrape query workspace is used, so the researcher experience is identical ("before as well as after scraping", as requested).

### Data available at each stage (honesty constraint)

* **Videos (flat / Videos tab)**: `channel_id, title, description, duration, upload_date, upload_timestamp, tags, categories, language, live_status, availability, age_limit, is_short, thumbnail_url, view_count`. NOT present: `like_count, comment_count, favorite_count, transcript_*`.
* **Videos (deep-enriched)**: all of the above plus `like_count, comment_count, favorite_count`.
* **Comments (raw)**: `author_id, author_name, comment_text, published_at, is_reply, parent_comment_id, like_count, reply_count, is_removed, is_author`.

Missing values **never satisfy** a value-based condition (existing evaluator rule). Therefore:
* If a criterion references a variable the current stage cannot supply, the decision is **deferred**:
  * videos �?� to deep enrichment when `enrich_video_stats` is on;
  * otherwise recorded as an explicit skip (`reason: "video criteria requires deep enrichment"`).
* A record whose criteria *can* be judged and fails is skipped with `reason: "excluded by video/comment criteria"`.

### Backend changes

1. **`domain/collection.py`** �?" `CollectionSpec` gains:
   * `video_criteria: QueryGroup | None = None`
   * `comment_criteria: QueryGroup | None = None`
   * both echoed in `effective()` (for `config_json` provenance).
2. **`services/collection_service.py`**:
   * row builders mirroring the evaluator keys (`_video_candidate_row(video, obs)`, `_comment_candidate_row(raw)`);
   * `_collect_videos`: flat-gate on `video_criteria` (skip + reason when judgeable & fails; defer when not judgeable), and re-gate after enrichment;
   * `_persist_comments`: apply `comment_criteria` (row-based) over raw comments before the existing min-likes/date/cap filters; excluded counts preserved/reported.
3. **No API schema change** for submission �?" `POST /collect` already accepts the full `CollectionSpec` (`extra="forbid"`), now with two extra optional fields.

### Frontend changes (module sub-agent, in parallel)

1. **`ui/src/lib/types.ts`** �?" add `video_criteria?/comment_criteria?` (`QueryGroup | null`) to `CollectionSpec`.
2. **`ui/src/components/features/query-builder.tsx`** �?" optional `lockedEntity` prop to hide the entity `Select` (so the collect form can pin video/comment).
3. **`ui/src/components/features/collect-target-form.tsx`** �?" under "Researcher options", two collapsible sections:
   * **Video inclusion criteria** (`QueryBuilder` locked to `video`) �?" only relevant for channel targets;
   * **Comment inclusion criteria** (`QueryBuilder` locked to `comment`).
   * Emit the tree into the spec only when it has ≥1 condition; surface filtered/skip counts in the result summary.

## 2. Feature 2 �?" Channel video count reads playlists (show 2, not 15)

**Root cause (verified live):** the producer extracted the channel *home* tab; its `playlist_count` = number of playlists (2) and `channel_video_count` does not exist in yt-dlp 2026.07.04. `normalize_channel_observation` maps `video_count = _to_int(raw, "channel_video_count", "playlist_count")` �?" so it always stored 2.

**Verified fix:** extracting the **Videos tab** (`https://www.youtube.com/@handle/videos`) returns `playlist_count: 15`, keeps `channel_follower_count: 52500`, title/description/tags/thumbnails, and rich flat entries (`view_count, duration, timestamp, title, live_status`).

**Backend changes (`acquisition/yt_dlp_adapter.py`):**

* `_channel_videos_url(url)` �?" when the URL is a YouTube channel (`/@handle` or `/channel/UC...`), append `/videos` unless the path already ends in a known tab (`/videos, /shorts, /streams, /playlists, /featured`); non-channel URLs unchanged.
* `_extract_channel` extracts the resolved Videos-tab URL, so `playlist_count` = real video count; `normalize_channel_observation` keeps preferring `channel_video_count` (tests/fixtures still pass) then falls back to `playlist_count`.

## 3. Feature 3 �?" Drawer console error

`<Drawer.Popup> expected to be rendered within <Drawer.Viewport>` (Base UI dev-only violation). Fix `ui/src/components/ui/drawer.tsx`: inside `DrawerPortal`, wrap `DrawerPrimitive.Popup` in `DrawerPrimitive.Viewport`; the viewport is a transparent `fixed inset-0 z-50 pointer-events-none` layer, the popup keeps its current placement/classes. No consumer changes.

## 4. Verification (T gate)

* Backend: `python -m pytest tests -q` (new tests: flat video-gate, enriched re-gate, comment criteria, videos-tab URL builder, channel count); `api/openapi.json` unchanged semantics.
* Frontend: `tsc --noEmit`, `eslint`, `vitest run`, `next build` (drawer + collect form + types).
* Live smoke: collect `@mmeshref` and confirm Overview video count is the real total.

## 5. Reproducibility / ethics notes

* Criteria are recorded in `run.config_json` (via `effective()`) so every run is auditable end-to-end.
* Excluded-by-criteria records are skipped with an explicit reason (never silent), matching the platform's "observed, never estimated" rule.