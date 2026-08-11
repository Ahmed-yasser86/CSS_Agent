# ADR: Phase 2 Research Platform — Decision Records

Template:
```
# ADR-00XX: Title
- Status: Proposed | Accepted | Superseded
- Date: YYYY-MM-DD
## Context
## Decision
## Consequences
```

---

# ADR-0001: No SQL Persistence (Decision D5)

- Status: Accepted
- Date: 2026-08-11

## Context
The platform persists to Excel workbooks via a repository factory (`build_repositories(provider=...)`). Phase 2 adds samples, datasets, projects, author profiles. Evaluated whether to introduce SQLite.

## Decision
**No SQL provider.** Excel remains the only implemented provider. The repository-factory indirection is kept and remains config-keyed so Excel can be replaced in principle without changing service/API layers. Large membership lists use an overflow JSON sidecar mechanism (Excel cell ~32k char limit): member ids are newline-joined/chunked.

## Consequences
- Simpler operational footprint; no schema migrations.
- All list endpoints use cursor-based pagination over stable sort keys because materialized scans are the storage model (ADR-0004).
- Sample/dataset membership must be deliberately sized or chunked; documentation notes limits.
- Single-writer discipline required at `WorkbookStore` (ADR-0009).

---

# ADR-0002: Research Context Model

- Status: Proposed (approved in principle)
- Date: 2026-08-11

## Context
The UI needs a persistent research focus (target, channel, video, query, variable selection) shared across screens without a client store.

## Decision
URL-encoded context parameters (`src/lib/context.ts`: parse/serialize + thin React context for derived state) in Phase A. A persisted `ResearchProject` (name, targets, spec, sampling specs, query, variable selection, notes, `config_hash`) is introduced in Phase D. Context degrades gracefully when no project is set.

## Consequences
- Fast iteration now; shared URL links; no new store dependency.
- Migration path to persisted projects is additive (context read from active project when present).

---

# ADR-0003: Comment Collection Ceiling — Researcher-Set (Decision D2)

- Status: Accepted
- Date: 2026-08-11

## Context
yt-dlp comment pagination is not guaranteed exhaustive. A hard global cap would silently truncate; no cap risks slow/fragile runs on popular videos.

## Decision
The ceiling is a **per-request, researcher-set** option `max_comments_per_video` on `CollectionSpec` (default: bounded by yt-dlp pagination behavior). The API accepts an explicit value per collection. Completeness is documented as a limitation; the ceiling value is recorded on the run for provenance.

## Consequences
- Researcher owns the trade-off per study.
- Provenance records the ceiling; quality reports can flag coverage versus ceiling.
- No silent global truncation.

---

# ADR-0004: Cursor-Based Pagination (Decision D3)

- Status: Accepted
- Date: 2026-08-11

## Context
All list endpoints need a consistent pagination contract. Offset/limit was considered; Excel-backed materialized scans can change length between pages.

## Decision
**Cursor-based pagination** on all list endpoints: a stable sort-key ordering tuple (primary key last) is encoded into an opaque base64 cursor. Responses are `{items, next_cursor, has_more, total}`. `total` is best-effort (full count when cheap). Missing/invalid cursors return 400 with an explanatory payload.

## Consequences
- Stable pagination across shifting data; cheap for pooled scans.
- `total` cost documented; large collections may return `total: null` when counting is expensive.
- Consistent envelope enforced by response models (ADR-0005) and the OpenAPI snapshot (R5).

---

# ADR-0005: Response-Model Strategy

- Status: Accepted
- Date: 2026-08-11

## Context
`api/app.py` has no pydantic `response_model` anywhere; the contract gate needs a stable, typed API surface.

## Decision
Every endpoint declares a pydantic `response_model`. Errors use a single envelope with machine-readable codes. The OpenAPI snapshot (checked in via `scripts/dump_openapi.py`) is the source of truth; a backend test regenerates it and fails on drift; the UI regenerates `src/lib/generated-api.ts` from it via `openapi-typescript`.

## Consequences
- Typed frontend contract; drift is caught by CI.
- Backend refactors must keep the snapshot in sync (additive changes expected).
- Orphaned API functions/hooks fail a contract test.

---

# ADR-0006: Statistics Engine Centralization

- Status: Accepted
- Date: 2026-08-11

## Context
Rate/ratio math is duplicated (`sampling_service._ratio/_sum` `sampling_service.py:207-223` replicate analytics helpers) and statistics are inline across services.

## Decision
Introduce `StatisticsService` as the single home for descriptive statistics (percentiles, quantiles, quartiles, Gini, concentration, IQR/z-scores, rates per 1k, growth). Existing callers migrate to it; new consumers depend on it. Percentile/quantile semantics are documented and unit-tested against known distributions.

## Consequences
- Single source of truth; fewer divergence bugs.
- All statistical outputs share provenance metadata (population_size, n, method).

---

# ADR-0007: Query Semantics for Rank-Based Operators

- Status: Accepted
- Date: 2026-08-11

## Context
Rank operators (`top_pct`, `percentile_rank`, `quartile`, `quantile`, `median_split`) need unambiguous meaning against the current population.

## Decision
- `percentile(p)`: value threshold at the p-th percentile (linear interpolation, like existing `_percentile`).
- `percentile_rank(x)`: record position expressed as percentage within the population.
- `quartile(q)`: equal-sized groups by value.
- `quantile(q)`: equal-sized groups by count.
- All computed against the **current** filtered population; the evaluation population and n are returned with results.

## Consequences
- Documented semantics prevent researcher misinterpretation; reflected in the variable catalogue.
- Funnel preview shows cumulative matched counts per stage.

---

# ADR-0008: Z-Score Scope

- Status: Accepted
- Date: 2026-08-11

## Context
Z-score normalization in comparisons is ambiguous when comparing heterogeneous sets.

## Decision
Z-scores are computed over the **compared set** (the units being compared) and are explicitly documented as relative to that set. Outliers (|z|>3) are flagged but never silently dropped.

## Consequences
- Consistent interpretation; outlier reporting surfaces rather than hides.

---

# ADR-0009: NetworkX Digraph Handling + Thread-Safety

- Status: Accepted
- Date: 2026-08-11

## Context
`networkx.connected_components`/`number_connected_components` raise `NetworkXNotImplemented` on `DiGraph`; `greedy_modularity_communities` lives in `networkx.algorithms.community`. Concurrent workbook writes from the 2-worker JobManager can corrupt files.

## Decision
Network metrics call `to_undirected()` for undirected-only measures (or use `weakly_connected_components`); community detection imports from `networkx.algorithms.community`. Workbook writes are serialized at `WorkbookStore` via a single-writer lock/queue.

## Consequences
- No `NotImplementedError` at runtime; correct metric semantics documented.
- Safe concurrent collection jobs; serialized writes at research scale.

---

# ADR-0010: Author Profiles — Raw Data Included (Decision D4)

- Status: Accepted
- Date: 2026-08-11

## Context
Author analytics requires understanding participation patterns. A counts-only approach was considered to minimize PII surface.

## Decision
`AuthorRepository` stores raw author profiles (the metadata already collected with comments) and exposes them in the explorer. Aggregates (comment_count, first_seen_run, video_ids) remain the primary surface; raw profiles are available for dataset/export use. Privacy surface is documented in research ethics documentation (data minimization, no bulk export of profile data beyond what is collected).

## Consequences
- Fuller author/participation research; broader privacy surface requiring explicit documentation.
- Raw profile access is an explicit, reviewed capability rather than implicit.

---

# ADR-0011: Sample Immutability

- Status: Accepted
- Date: 2026-08-11

## Context
Samples must be reproducible for methodology and provenance.

## Decision
Persisted samples are immutable after creation: population definition + hash, criteria JSON, seed, and member list are recorded at creation. Deletion is the only mutation. Member lists may be re-fetched from the population only via the recorded definition.

## Consequences
- Reproducible research; stable sample membership.
- Storage sized at creation; overflow mechanism applies (ADR-0001).

---

# ADR-0012: Phase A Delivery — Statistics Engine, Query/Funnel Contract, Cursor Pagination

- Status: Accepted
- Date: 2026-08-11

## Context
Phase A (P0 fundamentals) shipped the foundations the Phase 1 goal requires.

## Decision
- `StatisticsService` (`services/statistics_service.py`) is the single home for descriptive statistics; `analytics_service` and `sampling_service` now delegate to it (ADR-0006 implemented).
- `VariableRegistry` (`services/variable_registry.py`) provides the entity×variable catalogue that drives the query builder and future sampling/explorer UIs.
- `ResearchQuery`/evaluator/funnel in `domain/query.py`: 19 operators incl. rank ops computed against the current population (ADR-0007). Endpoints `GET /research/variables`, `GET /research/operators`, `POST /research/query/preview`, `POST /research/query/resolve`.
- Cursor pagination (ADR-0004) implemented in `services/pagination.py` and applied to all list endpoints.
- Contract gate (ADR-0005) shipped: checked-in `api/openapi.json` + drift test (`tests/test_openapi_snapshot.py`), `ui/src/lib/generated-api.ts` via `openapi-typescript`, orphan scanner (`ui/scripts/find-orphans.mjs`) + `ui/src/lib/contract.test.ts`. Known orphans: 4 api fns + 2 hooks.
- Frontend: research context model (ADR-0002), shell/context-bar/jobs tray, primitives (drawer/toast/combobox/date-range/pagination/accordion/scroll-area/radio-group/slider), error boundaries, query builder + funnel on `/query` (server-page pattern reading searchParams; rank-operator widgets; URL round-trip).

## Consequences
- 279 backend tests green (188 baseline + 91 new); UI tsc/lint clean and `/query` builds; contract + drift gate green.
- The full-research stack on the query/population path is now typed end-to-end and drift-protected; Phase B can build explorer/samples/comparison against it.

---

# ADR-0013: Router-Split Module Isolation

- Status: Accepted
- Date: 2026-08-11

## Context
Phase B-D adds six independent backend workstreams (comment analytics/longitudinal, comparison, samples, explorer/provenance, network full, datasets/projects). All would otherwise edit the shared `api/app.py` dispatcher, causing merge conflicts in parallel builds.

## Decision
Each module owns its own router module under `api/routers/*.py` plus its own service/domain/repository/test files. `create_app` includes all routers once (before the legacy direct routes, so literal paths like `/runs/delta` are never shadowed by `/runs/{run_id}`). Routers access shared state via `request.app.state.services` and lazily build their own services through `api.routers.common.get_service`.

## Consequences
- Fully parallel backend development on disjoint file sets; verified end-to-end (390 backend tests).
- Response models live next to their endpoints; OpenAPI snapshot is regenerated after each wave.
- New module agents never edit `api/app.py`.

---

# ADR-0014: Comment Analytics + Longitudinal (B3)

- Status: Accepted
- Date: 2026-08-11

## Context
Comment participation and longitudinal channel/video histories require centralization and must re-wire the previously-unwired `CommentFilter`.

## Decision
`CommentAnalyticsService` (participation Gini via StatisticsService, thread-size/age-at-posting/velocity-decay with bounded parent-chain walks, no fabrication when upload timestamps are missing) and `LongitudinalService` (oldest-first observation histories with per-step growth %, run deltas with new/disappeared entities, observation-gap reporting). Wiring goes through `QueryService.filter_comments`/`resolve_latest_rows` and `StatisticsService` for all math.

## Consequences
- Distribution-over-average researcher surface with explicit gap reporting.
- Literal `/runs/delta` requires router precedence (ADR-0013).

---

# ADR-0015: Comparison Engine + Z-Score Scope (B4)

- Status: Accepted
- Date: 2026-08-11

## Context
Comparisons (videos/channels/periods/cohorts/runs) need explicit normalization: none, per-1k, z-score.

## Decision
`ComparisonService` centralizes normalization in `StatisticsService` (rate/growth/mean/median/outliers). Z-scores are computed over the *compared set only* (ADR-0008); `None` values count toward `population_size`, never dropped; |z|>3 outliers are flagged.

## Consequences
- Consistent normalization semantics documented; robust to missing metrics.
- Endpoints: `POST /comparison/{videos|channels|periods|cohorts|runs}`.

---

# ADR-0016: Persisted Samples + Immutability (B5)

- Status: Accepted
- Date: 2026-08-11

## Context
Samples must be reproducible and auditable; Excel cell ~32k char limit constrains large member lists (ADR-0001).

## Decision
`SampleRepository` persists immutable `Sample` rows (population hash, criteria_json, seed, members). Large member lists are newline-joined and chunked into `sample_members` sidecar rows (`{sample_id}::{chunk_index}`); overflow is flagged. Deletion is the only mutation (tombstone row). `SampleService.compare_samples` computes pairwise Jaccard overlap + criteria diffs.

## Consequences
- Reproducible research; stable membership; chunking tested with 50k ids.
- Endpoints: `POST/GET /samples`, `GET/DELETE /samples/{id}`, `GET /samples/{id}/members`, `POST /samples/compare`.

---

# ADR-0017: Explorer + Provenance (B8)

- Status: Accepted
- Date: 2026-08-11

## Context
Researchers need a browsable, filterable view of any entity population plus the full provenance chain of each entity.

## Decision
`ExplorerService.explore` reuses `QueryService.resolve_latest_rows` (never re-implements row resolution), validates filter variables against `VariableRegistry`, and lifts simple filters into `QueryGroup` conditions evaluated by `domain/query.evaluate_query` (identical rank semantics). `ProvenanceService` returns first-observed run, run summaries, bounded observation history, provider/config. Lists are cursor-paginated.

## Consequences
- Explorer filter semantics == research-query semantics by construction.
- Endpoints: `GET /explore/records`, `GET /explore/records/{entity}/{id}/raw`, `GET /explore/provenance/{entity}/{id}`.

---

# ADR-0018: Full Network + Temporal + Exports (B6)

- Status: Accepted
- Date: 2026-08-11

## Context
Network-wide metrics, temporal run slices and graph exports are needed for network research.

## Decision
`NetworkAnalyticsService` builds on `RecommendationGraphService.build_graph` (unchanged). DiGraph semantics follow ADR-0009: `weakly_connected_components`, clustering/transitivity on `to_undirected()`, communities via `networkx.algorithms.community.gexf` sinks `None` edge attrs to `""`. HITS/PageRank directed; reciprocity guarded for empty graphs. Degree percentiles through `StatisticsService.percentile`.

## Consequences
- Correct NetworkX semantics documented; deterministic tie-breaks.
- Endpoints: `GET /network/metrics`, `/network/temporal`, `/network/edges`, `/network/export?format=graphml|edgelist|gexf`, `/network/channels`.

---

# ADR-0019: Datasets, Projects, Quality + Exports (B7)

- Status: Accepted
- Date: 2026-08-11

## Context
Researchers need persisted projects (ADR-0002 Phase D) and datasets built from query/sample projections, with quality reports and exports.

## Decision
`ProjectRepository` (sheet `projects`) persists `ResearchProject` (targets, collection spec, sampling specs, research query, variable selection, notes, `config_hash`). `DatasetRepository` persists dataset metadata + chunked `dataset_members` sidecar and optional raw-json sidecar files. `DatasetService.create_from_project` resolves rows via query evaluation + variable selection; quality reports a per-column missing-value matrix; exports are CSV/JSON via StreamingResponse. Fix: `blank_row` now clears cells by setting `.value = None` (openpyxl `cell(value=None)` does not clear).

## Consequences
- Projects are first-class; datasets reproducible from query config hashes; chunking tested with 50k ids.
- Endpoints: projects CRUD; datasets CRUD + `/members`, `/quality`, `/export?format=csv|json`.

---

# ADR-0020: Global Entity Search (E2)

- Status: Accepted
- Date: 2026-08-11

## Context
Researchers must find a specific channel, video, comment, author or recommendation without knowing its id or browsing per-entity screens.

## Decision
A single `GET /search?q=&entity=&cursor=&page_size=` endpoint searches across the five explorer entities with a rank-by-relevance projection (exact id/title/handle first, then text-substring matches, capped per entity). `GET /channels` and `GET /videos` gained the same `q` like-search so the `CommandPalette` and list endpoints share one retrieval path. Results use the standard cursor envelope (ADR-0004).

## Consequences
- One typed search surface drives the command palette and any future global search UI.
- Relevance is deterministic (documented ordering), never ML-ranked.

---

# ADR-0021: Dark Mode — CSS-Variable Theming + Pre-hydration (E3)

- Status: Accepted
- Date: 2026-08-11

## Context
The app ships hardcoded hex colors in recharts/graph components and needs a theme that matches `prefers-color-scheme` without a flash on load.

## Decision
Dark mode is class-based (`.dark` on `documentElement`, Tailwind v4 `@custom-variant dark`). A tiny inline pre-hydration script in `layout.tsx` reads `localStorage["theme"]` and falls back to `prefers-color-scheme: dark`, applying the class before first paint. Hardcoded chart hex colors were replaced with CSS variables (`--muted-foreground`, `--border`, etc.) that already flip with the theme.

## Consequences
- No flash of the wrong theme; preference persists across reloads.
- Chart/variable references stay theme-correct in both modes by construction.

---

# ADR-0022: Accessibility — Label Pairing, Group Semantics, Focus Rings (E4)

- Status: Accepted
- Date: 2026-08-11

## Context
The explorer form controls, metric tile groups and focus affordances were not fully reachable/describable by assistive technology.

## Decision
- Every form control in the explorer pairs an explicit `<Label htmlFor>` with its control id (search, entity, filter variable/operator/value).
- Metric tile groups (channel stats, video engagement + rates, network metrics) are wrapped in `role="group"`/`aria-labelledby` with sr-only section headings.
- Focus-ring policy: every raw `<button>`/button-styled `<a>` declares an `outline-none` + `focus-visible:ring` treatment; the `ErrorState` retry and `global-error` reset were brought into line.

## Consequences
- Keyboard and screen-reader journeys are consistent; visual focus is never removed silently.

---

# ADR-0023: Explorer Table Windowed Rendering + Page Size (E5)

- Status: Accepted
- Date: 2026-08-11

## Context
The `/explore` table rendered the whole page of rows at once (50 default) and headers scrolled out of view, causing jank on large pages.

## Decision
`PaginatedDataTable` renders a scroll container (`max-h-[65vh] overflow-y-auto`) with a sticky header and windowed tbody: uniform 36px row estimate, overscan window around the visible range, `aria-hidden` spacer rows above/below, scroll-reset on page/entity change. The `Table` ui primitive gained optional `wrapperRef`/`onWrapperScroll`/`wrapperClassName` (backwards-compatible). The explorer default page size dropped 50 → 25 to shrink payloads; `page_size` still accepts up to 500, and windowing keeps any page smooth.

## Consequences
- Constant DOM cost regardless of page size; sticky headers improve scanability.
- Row heights are estimated; a future variable-height row would need measured heights.

---

# ADR-0024: Visual Consistency Sweep (E6)

- Status: Accepted
- Date: 2026-08-11

## Context
A chromatic sweep across `/explore /compare /samples /network/full /datasets /projects` found hand-rolled loading/empty UI, raw `<table>`s with divergent headers, and micro-spacing drift.

## Decision
Standardize on the shared primitives: `LoadingState`/`EmptyState` for all loading/empty surfaces (network metrics, comparison compute, sample members, temporal runs), the shared `Table` primitives with bordered wrappers for all tabular output (degree-distribution, per-run slices), the page-header icon+subtitle pattern on `/network` + `/network/full`, always-visible toolbars with states rendered below (datasets), and unified label/icon/gap/margin tokens (text-xs filter labels, size-3.5 chip icons, gap-4 grids, mb-3 card headings). The explorer gained a real `LoadingState` instead of flashing "No records match" on first load.

## Consequences
- One visual language across the six screens; empty/loading/error behavior is predictable.

---

# ADR-0025: Phase E Delivery Status (E7)

- Status: Accepted
- Date: 2026-08-11

## Context
Phase E is the final polish wave; the plan required a Playwright researcher-journey E2E before declaring the phase complete.

## Decision
All E1–E6 work is shipped and gated (backend pytest, `tsc`, `eslint`, `vitest`, `next build`, OpenAPI snapshot). The Playwright E2E harness (config + researcher-journey spec) was authored but **dropped by the researcher before execution**: browser binaries (~700 MB) were not installable in the environment and the interactive `@playwright/mcp` server lives only in the VS Code config, not opencode. The dropped harness and browsers were fully removed. Journey coverage continues via the Vitest component tests, the 418-test backend suite, and documented manual QA steps; the plan status is set to **complete** with E7 marked as deferred.

## Consequences
- Phase E is complete with the E2E automation recorded as a known deferred follow-up; the testing story remains green on the existing gates.

