# Phase 2 — Research Platform Upgrade Plan

**Status:** Approved — Phases A–E complete
**Owner:** Orchestrator (opencode) + module agents
**Target:** `SocialScienceResearch/`
**Date:** 2026-08-11

---

## 0. Approved Decisions (locked)

| # | Decision | Choice |
|---|---|---|
| D1 | Context persistence | URL-encoded context now; persisted `ResearchProject` in Phase D |
| D2 | Comment collection ceiling | **Per-request, researcher-set** ceiling (`max_comments_per_video` on the collection spec); not a global cap; documented completeness limitation |
| D3 | Pagination contract | **Cursor-based** for all list endpoints (stable sort-key + opaque base64 cursor; cursor + total-count returned with rows) |
| D4 | Author analytics scope | **Include raw profiles** (`AuthorRepository` + raw author metadata in explore); privacy surface documented in ADR |
| D5 | Persistence provider | **No SQL.** Excel remains the only implemented provider; repository-factory indirection kept for replaceability in principle |
| D6 | Execution model | Orchestrator dispatches module agents per phase; S0 contract gate after every backend module; T tester gate per phase; ADR per module; report at phase boundaries |

---

## 1. Current-State Diagnosis

Endpoint-driven API (`api/app.py`), no research context, ephemeral sampling, no comparison engine, no centralized statistics engine, shallow comment analytics, unused longitudinal data (`ChannelObservation`/`VideoObservation`/`CommentObservation`), thin network analysis (summary + ego only), yt-dlp under-exploited (channel homepage, pagination, multilingual transcripts).

Verified defects (file:line):
- `JobStatus` duplicated (`domain/enums.py:147-155` dead; `services/jobs.py:39-44` live)
- `observed_at` duplicated on `TranscriptRecord` (`domain/models.py:251-252`)
- Spec-recommendation crashes: `collection_service.py:192` → `NotImplementedError` at `collection_service.py:170` (RecommendationService not wired in `api/app.py:58`)
- `/top` drops MISSING channel overrides (`api/app.py:241-242`)
- `_stratified` ignores seed (`sampling_service.py:289-300`); `_random` is seeded (`sampling_service.py:258`)
- `_can_enrich` silent skip (`collection_service.py:347-351`)
- Config pass-through missing (long-video >=300s `query_service.py:89`, seed 42, top_n duplication, max_workers=2, flush_every=1000, 5000-vs-10000 caps)
- Thread-safety gap (`WorkbookStore`)
- API hardening gaps: no response models, no pagination, CORS `*`
- Result duplication (`services/results.py:34-37` + `39-41`)
- `CommentFilter` defined but unwired (`domain/query.py:76-86`)
- `PeriodSpec` defined but unused (`domain/query.py:66-73`)
- Drift: 4 orphaned UI api fns (`ui/src/services/api.ts:169-194`), 3 orphaned hooks (`ui/src/services/queries.ts:156,193,219`); `getJobResult` is used

The foundation is sound; the problems are capability depth and workflow orientation.

## 2. Research Vision

A researcher-controlled CSS workbench with a persistent workflow:
**population → query → preview → sample → collect → explore → analyze → compare → network → dataset → export**
Methodology over endpoints, distribution over average, observed over estimated.

## 3. Capability Gap Analysis

| Capability | Today | Target | Blockers |
|---|---|---|---|
| Statistics engine | inline helpers, duplicated | central `StatisticsService` | — |
| Variable registry | implicit | dynamic per-entity catalogue | — |
| Query/filter | video-only basic | generic query builder + funnel | batch observation methods |
| Sampling | ephemeral, unseeded stratified | persisted, reproducible | `SampleRepository` + overflow storage |
| Comparison | none | cross-video/channel/period/cohort/run | `GET /channels`, `GET /videos` |
| Explorer | per-type endpoints | unified searchable explorer | `ExplorerService` + pagination |
| Comments | list only | population/participation/thread analytics | depth reconstruction, filter wiring |
| Longitudinal | unused data | observation history views | history endpoints |
| Network | summary + ego | metrics/community/projection/temporal/export | `to_undirected()`, community import |
| Datasets/projects | none | persisted datasets + research projects | new repos |
| Provenance | per-run config only | full lineage | sample criteria persistence |

## 4. Full Feature Roadmap

| ID | Feature | Priority |
|---|---|---|
| R1 | Statistics engine + variable registry + query builder + funnel | P0 |
| R2 | All BP2 defect fixes + API hardening (response models, cursor pagination, CORS) | P0 |
| R3 | `observed_at` migration + thread-safe workbook store | P0 |
| R4 | `GET /channels`, `GET /videos` global list endpoints | P0 |
| R5 | OpenAPI contract snapshot + drift gate + UI contract types | P0 |
| R6 | Shell/context-bar/jobs-tray + UI primitives + boundaries | P0 |
| R7 | Comment analytics + longitudinal + history endpoints | P1 |
| R8 | Comparison engine + workspace | P1 |
| R9 | Persisted samples + sample library | P1 |
| R10 | Explorer + provenance | P1 |
| R11 | Network metrics/community/projection/temporal/edge-list/export | P1/P2 |
| R12 | Datasets + projects + quality + exports | P2 |
| R13 | Global entity search, scatter/box/time-series charts, dark mode | P2/P3 |
| R14 | Accessibility, i18n, performance | P3 |

## 5. Researcher-Controlled Collection Architecture

- `CollectionSpec` (spec-hashed) extended: variables to collect, reply depth, transcript languages, `max_comments_per_video` (researcher-set, D2).
- **Wire `RecommendationService` into the `_services["collection"]` slot** (`api/app.py:58`) — fixes the spec-recommendation crash without new dispatch code.
- Persisted `ResearchProject` (Phase D): name, targets, spec, sampling specs, query, variable selection, notes, `config_hash` (mirrors `CollectionSpec.spec_hash`).

## 6. Dynamic Variable System

Inventory per entity:
- **channel** (`Channel` + `ChannelObservation`): title, description, handle, is_verified, avatar/banner, country, joined_date, subscriber/video/view counts (observed).
- **video** (`Video` + `VideoObservation`): channel_id, title, description, duration, upload_date/timestamp, tags, categories, language, live_status, availability, age_limit, is_short, thumbnail; view/like/comment/favorite counts; transcript_path/status/lang (derived).
- **comment** (`Comment` + `CommentObservation`): author_name/id, text, published_at, is_reply, parent/root ids, is_author; like/reply counts, is_removed.
- **recommendation** (`RecommendationObservation`): source/recommended ids, position, status, channel_id, title.

Registry metadata: name, entity, data_type, source (observed/derived/raw), availability, description, unit, limits. `GET /research/variables?entity=…`.

## 7. Smart Filtering / Query Builder

- `ResearchQuery`: entity, group tree (`AND|OR|NOT` nested), conditions `{variable, operator, value/values}`.
- Rank-based operators: `top_pct/bottom_pct`, `percentile_rank`, `quartile(1..4)`, `quantile(q)`, `median_split` — computed against the **current** population.
- Funnel preview: `POST /research/query/preview` → `{total, stages[{condition, matched, cumulative}]}`.
- Computed via latest-observation resolution (`excel_repository.py:127-131`) + Python filtering; batch `get_latest_*_observations(ids)` in `persistence/base.py` to avoid N+1.

## 8. Advanced Sampling System

- `SamplingSpec` gains `population_query` (`VideoPopulationQuery`/`CommentPopulationQuery`; `QueryService.filter_comments`).
- **Fix `_stratified`** (`sampling_service.py:289-300`): `Random(spec.seed or default)`, shuffle within strata.
- **Persisted samples** (`SampleRepository` + sheet): sample_id, entity_type, strategy, population def + hash, population_size, sample_size, seed, criteria_json, member ids (chunked/newline-joined via overflow sidecar), missing_metric_count, created_at, created_by_run_id.
- Endpoints: `POST /research/samples`, `GET /samples`, `GET /samples/{id}`, `GET /samples/{id}/members` (cursor-paginated), `DELETE /samples/{id}`, `POST /samples/compare`.
- Methodological limits documented (stratified needs per-stratum metadata; quota best-effort).

## 9. Data Explorer

- `ExplorerService`: `GET /explore/records?entity=&q=&filters=&sort=&cursor=&page_size=` — pooled scans, `q` like-search (precedent `query_service.py:64-67`), unified row projection; `raw_json` via `GET /explore/records/{type}/{id}/raw` (mirrors `/videos/{id}/raw` `app.py:216-221`).
- UI: `/explore` — entity switcher, debounced search, `PaginatedDataTable` (cursor pagination + selection + column toggle), detail drawer (Dialog side-sheet) with metadata + raw inspector + provenance; client-side CSV export. Degrade to `UnsupportedState` until R10 lands.

## 10. Visualization System

- recharts 3.10: distributions with percentile `ReferenceLine`s, scatter (views vs likes), multi-series line/area (observation snapshots), box+whiskers via `ComposedChart` (no BoxPlot in 3.10), heatmap, funnel, network.
- Every chart carries population context + provenance footer; brush/select → underlying records.

## 11-15. Entity Research Workflows

- **Video:** population (dates/engagement percentile/duration/tags/channel) → preview → collect → distributions → observe history → compare.
- **Channel:** publishing patterns, cohorts, performance distribution, IQR/z outliers vs baseline, observation-history.
- **Comment:** population (likes/replies/date/depth/percentile/root-vs-reply/author) → distribution → sample → threads (depth reconstructed via parent-chain walk, bounded) → participation (unique/repeat authors, comments-per-author, Gini/top-k% concentration), reply-rate, thread-size distribution, comment-age-at-posting, velocity/decay. Wire `CommentFilter` via new `CommentRepository.list_comments_filtered`.
- **Comparison:** `POST /comparison/videos|channels|periods|cohorts|runs`; shared `VideoFilter`/`PeriodSpec` (reuse `query.py:66`) as comparable-context; `population_size` + warnings; normalization `none|per_1k|z_score`; centralize ratio math into `StatisticsService`. Requires `GET /channels` + `GET /videos`.
- **Run-snapshot diff:** change %, new/disappeared entities.

## 16-17. Network Research

- Add `observed_at` to `RecommendationObservation` (default None → backward compatible).
- Expanded service: reciprocity, degree distribution, clustering, HITS authorities, components (**`to_undirected()` first**), density, **`greedy_modularity_communities`** (from `networkx.algorithms.community`), channel projection (channel_id on both ends), temporal slices per `collection_run_id`, `GET /network/temporal?runs=a,b`, `GET /network/edges` (cursor-paginated), `GET /network/export?format=graphml|edgelist|gexf`.
- UI: `/network/full` — react-force-graph-2d (dynamic import), **wire the existing `onNodeClick`** (`network-graph.tsx:84-87`) → ego-network; community coloring, centrality node-size, temporal overlay; tables always alongside.

## 18. Longitudinal Research

- `LongitudinalService`: per-entity observation series (`GET /channels/{id}/history`, `GET /videos/{id}/history`), deltas/growth, run-snapshot diffing, observation-gap reporting.
- `published_at` vs `observed_at` separation surfaced in models/UI/coverage.

## 19. Provenance & Reproducibility

- `ProvenanceService`: lineage source → run (`config_json`/`spec_hash`) → entity (`first_observed_run_id`) → query hash → sample (criteria + seed + population hash) → dataset manifest.
- UI: `ProvenancePanel` in record drawers + methodology panels on samples/datasets.

## 20. Data Quality & Coverage

- Extend `QualityService`: missing-value matrix, per-run coverage, observation gaps, duplicate detection, dangling reply/edge ids, temporal gaps. Scoped to dataset: `GET /datasets/{id}/quality`.

## 21. External Transcript Storage

- Keep `.txt` artifacts + path refs. Add multi-language (`transcript_langs`), transcript read-back endpoint, transcript-derived variables. Fix duplicate `observed_at` (`models.py:251-252`).

## 22. Repository Architecture

- **No SQL (D5).** Factory keyed by config; Excel only implemented provider.
- New repos: `SampleRepository`, `DatasetRepository` + `dataset_members`, `ProjectRepository`, `AuthorRepository` (raw profiles, D4), `ObservationRepository`/batch methods.
- Thread-safety: serialize writes at `WorkbookStore` (single-writer lock/queue).

## 23. Frontend Information Architecture

- Context bar: URL-encoded context (`src/lib/context.ts`) + thin React context; degrades gracefully.
- Jobs tray in header (uses orphaned `useJobs` + `useCancelJob`); toasts (sonner or base-ui toast).
- Nav (≤7): Workspace · Collect · Explorer · Network · Samples · Datasets · Runs.
- New routes: `/explore`, `/compare`, `/samples`, `/datasets`, `/projects`, `/network/full`, `/videos/[id]/history`, `/channels/[id]/history`.
- Primitives: combobox (cmdk), date-range picker, Dialog-side-sheet drawer, toast, accordion, pagination, scroll-area, radio-group, slider; `error.tsx`/`global-error.tsx`/`not-found.tsx`/`loading.tsx`; dark mode (defer).
- Validation: add `zod` for builder forms.

## 24. Backend Architecture Changes

New services: `StatisticsService`, `QueryService` (extended), `CommentAnalyticsService`, `LongitudinalService`, `ComparisonService`, `DatasetService`, `SampleService`, `ProvenanceService`, `ExplorerService`, network expansion. New repos (above). All defect fixes. Response models mandatory. **Cursor-based pagination (D3): stable sort-key ordering tuple → opaque base64 cursor; responses include `{items, next_cursor, has_more, total}`.** CORS config. Settings pass. `observed_at` migration. Spec-recommendation wiring.

## 25. Testing Architecture

- Backend: `pytest` extended ~134 → ~230+ (stats engine incl. known-distribution Gini/quartiles; query operators + funnel; comparison normalization/context warnings; sampling reproducibility + stratified RNG; longitudinal deltas; network metrics on fixture graphs; dataset/sample/project persistence; explorer search/pagination; provenance hashing; migration/legacy-workbook test; OpenAPI snapshot test).
- Frontend: **add Vitest + RTL** (none installed today) — builder serialization, operator rendering, funnel rendering, cursor pagination/selection, raw-inspector fetch-on-demand, comparison warnings, graph node-click wiring, history formatting.
- E2E: Playwright researcher journey: population → preview → sample → explore → compare → dataset → export; error/empty/unsupported states.
- **Contract gate (S0):** `scripts/dump_openapi.py` → checked-in `api/openapi.json`; backend test regenerates and fails on drift; UI runs `openapi-typescript` → `src/lib/generated-api.ts`; `contract.test.ts` asserts types match and fails on orphaned api fns/hooks. Every endpoint needs a pydantic response_model.

## 26. Documentation

- ADRs: research-context model, stats centralization, query semantics, **cursor pagination (D3)**, response-model strategy, sample immutability, z-score scope, networkx `to_undirected`, thread-safety approach, Excel single-writer, comment pagination ceiling (**researcher-set, D2**), **author raw profiles (D4)**, **no-SQL (D5)**.
- Technical: API reference, data-model additions, migration notes, config reference. Research: variable catalogue, sampling-method definitions, percentile/quantile semantics, network metrics, yt-dlp capability register, longitudinal methodology, ethics (data minimization).

## 27. Implementation Phases

### Phase A — P0 Fundamentals (current)
- **B2** (fixes/config/cursor pagination/response models/thread-safety/observed_at migration/spec-recommendation wiring) ∥ **B1** (StatisticsService/VariableRegistry/ResearchQuery/funnel/batch observation) → **S0** (OpenAPI snapshot + contract scaffolding + legacy-workbook test) → **F1** (shell/context/jobs tray/primitives/boundaries) ∥ **F2** (query builder + funnel) → **T** gate.
- **Done:** 136+ tests green; tsc/lint green; funnel correct; contract snapshot committed; defects fixed with regression tests.

### Phase B — P1 Research-Critical
- **B8** (Explorer/Provenance/Observation batch) ∥ **B5** (samples) ∥ **B4** (comparison + `GET /channels` + `GET /videos`) ∥ **B3** (comment analytics + longitudinal + history) → **S0** → **F3** (explorer) ∥ **F5** (sampling + library) ∥ **F4** (comparison) ∥ **F7** (history views + charts) → **T**.
- **Done:** record → sample → compare loop end-to-end; histories render.

### Phase C — P1/P2 Network
- **B6** (metrics/community/projection/temporal/edges/export) → **S0** → **F6** (`/network/full`, node-click, temporal) → **T**.
- **Done:** network metrics/community/projection/temporal/edges/export endpoints (`network_ext.py`); `/network/full` UI (force-graph + temporal + node-click); S0 + backend + UI gates green.

### Phase D — P2 Datasets & Projects
- **B7** (DatasetService/Project/quality/export) → **S0** → **F8** (`/samples`/`/datasets`/`/projects` + `/data` rewrite) → **T**.
- **Done:** projects/datasets/samples/quality/export (B7, `api/routers/datasets.py` + `samples.py`); `/samples` `/datasets` `/projects` `/data` (F8); S0 gate green; backend 418 tests green; UI tsc/lint/vitest + build green.

### Phase E — P2/P3 Polish
- Chromatic polish, global entity search, accessibility, performance, dark mode, `AuthorRepository` refinement → **T** + full suite + E2E + docs.
- **Done:** E1 author profiles (`AuthorRepository` + `authors` sheet + `/explore` author entity) · E2 global search (`GET /search` + `q` on `/channels` `/videos` + command-palette groups) · E3 dark mode (pre-hydration script + CSS-variable charts) · E4 accessibility (label/htmlFor, metrics `role=group`/`aria-labelledby`, focus-ring policy) · E5 performance (windowed `PaginatedDataTable`, sticky header, explorer page size 25) · E6 chromatic sweep (shared state/table primitives, headers, toolbars) · docs + ADR-0020..0025. Gates green: backend 418 pytest, `tsc`/`eslint`/`vitest`/`next build`, OpenAPI snapshot. **E7 Playwright E2E deferred** (ADR-0025): harness authored then dropped; browsers not installable in the environment and the `@playwright/mcp` server is VS Code-scoped only.

#### E1 — Author Profiles (D4, backend)
- `AuthorProfile`/`Author` domain model; `AuthorRepository` + `authors` Excel sheet (raw profile JSON + aggregates); register in `Repositories` container (`persistence/base.py`).
- `/explore` gains `author` entity (resolve + raw profile fields); provenance covers author records.
- **S0** contract gate after this module.

#### E2 — Global Entity Search (backend + frontend)
- `GET /search?q=&entity=&cursor=&page_size=` cross-entity (channels, videos, comments, authors, recommendations) with rank-by-relevance, unified result projection.
- Add `q` (like-search) to `GET /channels` + `GET /videos`.
- Frontend: `api.ts` fn + `queries.ts` hook; `CommandPalette` gains an entity-result group (debounced, grouped by entity, `state.tsx` loading/empty states).
- **S0** contract gate.

#### E3 — Dark Mode (frontend)
- Theme provider/toggle + pre-hydration script in `layout.tsx`; persist preference.
- Replace hardcoded hex colors in `charts.tsx`, `velocity-chart.tsx`, `longitudinal-chart.tsx`, `temporal-overlay.tsx`, `network-graph.tsx` with CSS variables.

#### E4 — Accessibility (frontend)
- Label/`htmlFor` pairing for explorer search + filter controls; metrics-group `role="group"`/`aria-labelledby`; focus-ring policy check (`ErrorState` retry, thin outline risk).

#### E5 — Performance (frontend)
- Virtualize `PaginatedDataTable` rows (windowed rendering) and/or smaller default page size.

#### E6 — Chromatic/Visual Polish (frontend)
- Consistent state spacing, table header behavior, empty/loading alignment sweep across `/explore`, `/compare`, `/samples`, `/network/full`, `/datasets`, `/projects`.

#### E7 — E2E + Docs
- Playwright researcher journey: population → preview → sample → explore → compare → dataset → export; error/empty/unsupported states.
- Technical + research docs, final ADRs, plan status → complete.

## 28. Priority Register

- **P0:** Stats engine, variable registry, query + funnel, all B2 fixes, cursor pagination/response models, thread-safe store, observed_at migration, `GET /channels` + `GET /videos`, contract gate + scaffolding, shell/context/jobs tray, query builder + funnel UI, paginated tables, test/docs foundations.
- **P1:** Comment analytics, longitudinal + history, comparison + workspace, sample persistence + library, explorer + provenance, network full metrics + full-graph UI, datasets + projects + exports, edge-list endpoint.
- **P2:** Community/cross-channel/temporal network + NetworkX export, comment pagination loop + deep author data, global entity search, dark mode, scatter/box/time-series charts.
- **P3:** Accessibility, i18n, performance/virtualization, additional sampling methods (quota/cohort/balanced).

## 29. Execution Workflow

```
Orchestrator
 ├─ dispatches module agents per phase (backend ∥ frontend where dependency-free)
 ├─ runs S0 contract gate after every backend module
 ├─ runs T tester gate (pytest + tsc/eslint/vitest + integration + Playwright journey)
 │    └─ bounded failing checks → module agent refines → re-gate
 ├─ writes ADR per completed module
 └─ updates plan + reports at each phase boundary
```
