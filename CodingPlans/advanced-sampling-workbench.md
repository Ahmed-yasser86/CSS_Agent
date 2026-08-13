# Advanced Sampling Workbench - Implementation Plan

## Executive Summary

This document outlines the comprehensive plan for implementing an advanced sampling workbench at `/samples` that provides:
1. **Maximum filtering/labeling flexibility** across all collected data
2. **Dataset combination** with lineage tracking (references to original samples)
3. **Custom label system** - researchers create any key-value labels
4. **Comment tree modal** - click any comment to see full reply hierarchy
5. **Video metadata preview** - click any video to see full metadata
6. **Project management** - group datasets into research projects

---

## Current State Analysis

### What Exists (From Exploration)

| Feature | Status | Location |
|---------|--------|----------|
| Comment Tree API | ✅ Complete | `GET /videos/{video_id}/comments/{comment_id}/tree` returns `CommentTreePayload` with recursive structure |
| Comment Models | ✅ Complete | `Comment`, `CommentObservation`, `CommentTreePayload` in `domain/models.py` |
| Enhanced Comment Tree UI | ⚠️ Exists but disconnected | `ui/src/components/features/comment-tree-enhanced.tsx` |
| AdvancedSamplingSpec | ✅ Complete | 30+ filter fields in `domain/query.py` and `services/api.ts` |
| Sampling API | ✅ Complete | `POST /sampling/advanced` in `services/sampling_service.py` |
| Sample Persistence (B5) | ✅ Complete | CRUD at `/samples` in `api/routers/samples.py` |
| Sample Library UI | ✅ Complete | `ui/src/components/features/samples/` |
| Video Metadata | ✅ Complete | Full schema in `domain/models.py`, `api/schemas.py`, `ui/src/lib/types.ts` |
| Video Workspace | ✅ Complete | `ui/src/components/features/video-workspace.tsx` at `/videos/[videoId]` |

### What's Missing

1. **Comment tree not triggered from everywhere** - Clicking a comment doesn't fetch its full tree
2. **Sampling UI is primitive** - No labeled filters, no presets, no clear UX for researchers
3. **No Dataset model** - Samples are flat, can't group into datasets
4. **No Project model** - No way to organize datasets into research projects
5. **No custom labeling system** - Missing rich metadata on samples/datasets
6. **No dataset combination with lineage** - Can't merge samples while tracking origins
7. **Video preview not available everywhere** - Only in video workspace, not in explorer/samples

---

## Data Model Design

### Extended Sample Model

```python
# domain/sample_models.py (extends existing Sample)
class Sample(BaseModel):
    sample_id: str
    entity_type: str  # 'video' | 'comment' | 'channel' | 'recommendation'
    strategy: str
    population_query_hash: str = ""
    population_size: int
    sample_size: int
    seed: int | None = None
    criteria_json: dict[str, Any] = Field(default_factory=dict)
    member_ids: list[str] = Field(default_factory=list)
    overflow: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    created_by_run_id: str | None = None
    
    # NEW: Scope tracking for reproducibility
    scope: dict[str, Any] = Field(default_factory=dict)
    # {
    #   "channel_ids": [],
    #   "video_ids": [],
    #   "author_ids": [],
    #   "date_from": "",
    #   "date_to": ""
    # }
    
    # NEW: Filters applied (subset of criteria_json)
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    
    # NEW: Full labeling system
    labels: dict[str, Any] = Field(default_factory=dict)
    # {
    #   "system": {
    #     "created_at": "",
    #     "created_by": "",
    #     "source_corpus": "",
    #     "collection_run_id": ""
    #   },
    #   "research": {
    #     "research_question": "",
    #     "methodology": "",
    #     "population": "",
    #     "sampling_frame": "",
    #     "notes": ""
    #   },
    #   "custom": {}  # user-defined key-value pairs
    # }
```

### Dataset Model (New)

```python
# domain/dataset_models.py
class Dataset(BaseModel):
    dataset_id: str
    name: str
    description: str = ""
    
    # Composition - references to samples with lineage
    sample_ids: list[str] = Field(default_factory=list)
    parent_dataset_ids: list[str] = Field(default_factory=list)
    
    # Labels (same structure as Sample)
    labels: dict[str, Any] = Field(default_factory=dict)
    
    # Aggregated stats
    total_members: int = 0
    entity_types: list[str] = Field(default_factory=list)
    source_scopes: list[str] = Field(default_factory=list)  # channel IDs or "global"
    
    # Lineage tracking
    deduplicated: bool = True
    lineage_preserved: bool = True
    
    created_at: datetime = Field(default_factory=utcnow)
    created_by: str = ""
    updated_at: datetime = Field(default_factory=utcnow)
```

### Project Model (New)

```python
# domain/project_models.py
class Project(BaseModel):
    project_id: str
    name: str
    description: str = ""
    dataset_ids: list[str] = Field(default_factory=list)
    labels: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
```

---

## Sampling Workbench UI Specification

### Overall Layout: Three-Column Design

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  ADVANCED SAMPLING WORKBENCH                                          [Run] [Save ▾]    │
├──────────────┬───────────────────────────────────────────────────────┬───────────────────┤
│              │                                                       │                    │
│  PRESETS     │  SCOPE: What data are we searching?                   │  LIVE PREVIEW      │
│              │  ┌───────────────────────────────────────────────────┐│  ──────────────── │
│  ─────────   │  │ [All Data] [By Channel] [By Author] [Custom]     ││                    │
│              │  └───────────────────────────────────────────────────┘│  Population: 12,847│
│  By Author   │                                                       │  ──────────────── │
│  By Channel  │  ┌───────────────────────────────────────────────────┐│                    │
│  By Video    │  │ SCOPE CONFIGURATION (varies by selection)         ││  Sample IDs:       │
│  Temporal    │  │                                                   ││  • comment_001     │
│  Random      │  │ [UI based on scope type]                          ││  • comment_042     │
│  Stratified  │  │                                                   ││  • comment_103     │
│              │  │                                                   ││  • ...             │
│  ─────────   │  └───────────────────────────────────────────────────┘│                    │
│              │                                                       │  [Refresh Preview] │
│  SAVED       │  ┌───────────────────────────────────────────────────┐│                    │
│  ─────────   │  │ LABELED FILTER SECTIONS              [AND ▼]      ││                    │
│  Query 1     │  │                                                   ││                    │
│  Query 2     │  │ ▼ AUTHOR FILTERS                                  ││                    │
│              │  │   Exclude video author: [✓]                        ││                    │
│              │  │   Exclude users: [input + add]                     ││                    │
│              │  │   Include authors: [input + add]                  ││                    │
│              │  │                                                   ││                    │
│              │  │ ▼ VIDEO FILTERS (if comment sampling)              ││                    │
│              │  │   Duration: [Any ▼]  Views: [Any ▼]                ││                    │
│              │  │   Upload date: [From___] - [To___]               ││                    │
│              │  │   Tags: [Add tags...]                             ││                    │
│              │  │   Category: [Any ▼]                               ││                    │
│              │  │                                                   ││                    │
│              │  │ ▼ COMMENT FILTERS                                  ││                    │
│              │  │   Likes: [Min___] - [Max___]                      ││                    │
│              │  │   Replies: [Min___] - [Max___]                    ││                    │
│              │  │   Type: ○ All ● Roots ○ Replies                   ││                    │
│              │  │   Keywords: [input] [match: Any▼]                 ││                    │
│              │  │   Exclude keywords: [input]                        ││                    │
│              │  │                                                   ││                    │
│              │  │ ▼ TEMPORAL FILTERS                                ││                    │
│              │  │   Video upload range: [From___] - [To___]        ││                    │
│              │  │   Comment date (if available): [From___] - [To]  ││                    │
│              │  │                                                   ││                    │
│              │  └───────────────────────────────────────────────────┘│                    │
│              │                                                       │                    │
│              │  ┌───────────────────────────────────────────────────┐│                    │
│              │  │ SAMPLING METHOD                                  ││                    │
│              │  │ ○ Full Population  ● Random Sample  ○ Stratified ││                    │
│              │  │                                                   ││                    │
│              │  │ Sample size: [500] comments  or  [10] %          ││                    │
│              │  │ Seed: [_________] (optional)                      ││                    │
│              │  └───────────────────────────────────────────────────┘│                    │
│              │                                                       │                    │
│              │  ┌───────────────────────────────────────────────────┐│                    │
│              │  │ RESULT ACTIONS                                   ││                    │
│              │  │                                                  ││                    │
│              │  │ Label this sample:                                ││                    │
│              │  │   Research: [dropdown ▼] [custom input]          ││                    │
│              │  │   Notes: [textarea]                               ││                    │
│              │  │                                                  ││                    │
│              │  │ ○ Save as individual sample                       ││                    │
│              │  │ ● Add to dataset: [New Dataset ▼ / Existing ▼]    ││                    │
│              │  │                                                  ││                    │
│              │  └───────────────────────────────────────────────────┘│                    │
└──────────────┴───────────────────────────────────────────────────────┴───────────────────┘
```

### Scope Types & Configuration

| Scope | Description | UI Configuration |
|-------|-------------|------------------|
| **All Data** | Global corpus | Shows total corpus counts only |
| **By Channel** | Specific channels | Multi-select channel list + "Select All" + optional video filter within channels |
| **By Author** | Specific authors | Autocomplete search + manual author ID input + author comment counts |
| **Custom/Filtered** | Combine any filters | Full filter panel with all options |

### Filter Sections (All Labeled with Help Text)

1. **Author Filters**:
   - Include specific authors (by ID or search)
   - Exclude specific authors
   - Exclude video author (toggle)
   - Author comment count range

2. **Video Filters** (for comment sampling):
   - Duration range (<60s, 1-5min, 5-20min, >20min)
   - View count range
   - Upload date range
   - Upload weekday (0-6)
   - Tags (AND match)
   - Category
   - Video type (short/long/live)

3. **Comment Filters**:
   - Like count range
   - Reply count range
   - Comment type (all/roots/replies)
   - Keywords (with Any/All match mode)
   - Exclude keywords
   - Regex pattern (optional)

4. **Temporal Filters**:
   - Video upload date range
   - Comment date range (if available)
   - Stratification by month/weekday (for stratified sampling)

### Sampling Methods

| Method | Configuration |
|--------|---------------|
| **Full Population** | No additional config - returns all matching |
| **Random Sample** | Absolute count OR percentage + optional seed |
| **Stratified Sample** | Stratification variable (channel, month, author, views quartiles, likes quartiles, weekday) + samples per stratum |

---

## Dataset Combination System

### Dataset Builder UI

```
┌────────────────────────────────────────────────────────────────────────┐
│  CREATE DATASET FROM SAMPLES                                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Name: [________________________________]                              │
│  Description: [________________________________________________]        │
│                                                                        │
│  ──────────────────────────────────────────────────────────────────── │
│                                                                        │
│  INCLUDE SAMPLES                                          [+ Add]      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ ☑ Sample: "High-engagement climate comments"    (1,247 members)  │ │
│  │ ☑ Sample: "Low-engagement political replies"    (892 members)    │ │
│  │ ☑ Sample: "Random sample channel #3"            (500 members)    │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  OPTIONS                                                                │
│  ☑ Deduplicate members (remove IDs that appear in multiple samples)  │
│  ☑ Track source sample for each member (preserve lineage)            │
│                                                                        │
│  ──────────────────────────────────────────────────────────────────── │
│                                                                        │
│  LABELS                                                                 │
│  Research Question: [dropdown ▼] [custom: ________________]          │
│  Methodology: [dropdown ▼] [custom: ________________]                │
│  Custom Labels:                                                         │
│    Key: [________] Value: [________]  [+ Add]                          │
│    • population: "YouTube comments on climate videos"                   │
│    • timeframe: "2023-2024"                                           │
│                                                                        │
│  ──────────────────────────────────────────────────────────────────── │
│                                                                        │
│  Preview: 2,639 total members (after dedup)                           │
│                                                                        │
│                              [Cancel]  [Create Dataset]                 │
└────────────────────────────────────────────────────────────────────────┘
```

### Lineage Preservation

When combining samples:
- **References maintained**: New dataset stores `sample_ids` array
- **Deduplication option**: If enabled, removes duplicate member IDs across samples
- **Lineage metadata**: Each member in resulting dataset can trace back to source sample(s)

---

## Comment Tree Integration

### Trigger Points
- Click comment in `CommentsBrowser` (video workspace)
- Click comment in `CommentTreeEnhanced`
- Click comment in any DataTable showing comments
- Click comment in Sample Library member list

### Modal Implementation
- **Component**: `CommentTreeModal` (modal overlay)
- **API**: `GET /videos/{video_id}/comments/{comment_id}/tree`
- **Features**:
  - Nested threaded view with indentation (depth × 24px)
  - Author, text, timestamp, like_count, reply_count
  - Expand/collapse branches
  - Lazy-load deep branches on expand
  - "Start new sample from this thread" action button

---

## Video Metadata Preview

### Trigger Points
- Click video in `/explore` DataTable
- Click video in `/samples` result list
- Click video in channel corpus browser
- Click video in run videos browser

### Preview Component
- **Component**: `VideoMetadataPreview` (modal overlay or slide panel)
- **Fields displayed**:
  - Basic: title, description, duration, upload_date, channel
  - Stats: views, likes, comments (from latest observation)
  - Content: tags, categories, language
  - Technical: is_short, live_status, availability, age_limit
  - Raw JSON: expandable section with full `raw_json`

---

## Project Management UI

### /samples Page Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PROJECTS & DATASETS                                              [+ New]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROJECTS                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  📁 Climate Misinformation Study                    3 datasets      │   │
│  │  📁 Political Engagement Analysis                   2 datasets      │   │
│  │  📁 Music Viral Content Research                    1 dataset       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  DATASETS (Ungrouped)                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  📊 Pro-Climate Comments          1,247 members  3 samples          │   │
│  │  📊 Climate Denial Comments         892 members   2 samples          │   │
│  │  📊 Neutral Control Group           500 members   1 sample           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  INDIVIDUAL SAMPLES                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [Sample cards - existing SampleLibrary component]                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Backend Models & APIs (Parallel)

| Task | Description | Files |
|------|-------------|-------|
| 1.1 | Extend Sample model with labels, scope, filters_applied | `domain/sample_models.py` |
| 1.2 | Create Dataset model with lineage | `domain/dataset_models.py` |
| 1.3 | Create Project model | `domain/project_models.py` |
| 1.4 | Add DatasetRepository and ProjectRepository | `persistence/` |
| 1.5 | Create API routers for datasets/projects | `api/routers/datasets.py`, `api/routers/projects.py` |
| 1.6 | Update Sample API to save labels/scope | `api/routers/samples.py` |

### Phase 2: Frontend Core Components (Parallel)

| Task | Description | Files |
|------|-------------|-------|
| 2.1 | Create SamplingWorkbench main component | `ui/src/components/features/sampling-workbench-new.tsx` |
| 2.2 | Create ScopeSelector component | `ui/src/components/features/scope-selector.tsx` |
| 2.3 | Create FilterPanel with all labeled sections | `ui/src/components/features/filter-panel.tsx` |
| 2.4 | Create SamplingMethodSelector | `ui/src/components/features/sampling-method-selector.tsx` |
| 2.5 | Create LivePreview panel | `ui/src/components/features/live-preview.tsx` |
| 2.6 | Create ResultActions panel with labeling | `ui/src/components/features/result-actions.tsx` |

### Phase 3: Dataset & Project UI (Parallel)

| Task | Description | Files |
|------|-------------|-------|
| 3.1 | Create DatasetBuilder modal | `ui/src/components/features/dataset-builder.tsx` |
| 3.2 | Create ProjectManager component | `ui/src/components/features/project-manager.tsx` |
| 3.3 | Create DatasetCard and ProjectCard | `ui/src/components/features/dataset-card.tsx` |
| 3.4 | Update /samples page with new structure | `ui/src/app/samples/page.tsx` |

### Phase 4: Comment Tree & Video Preview (Parallel)

| Task | Description | Files |
|------|-------------|-------|
| 4.1 | Create CommentTreeModal component | `ui/src/components/features/comment-tree-modal.tsx` |
| 4.2 | Create useCommentTree hook | `ui/src/hooks/useCommentTree.ts` |
| 4.3 | Integrate comment click handlers everywhere | Multiple files |
| 4.4 | Create VideoMetadataPreview component | `ui/src/components/features/video-metadata-preview.tsx` |
| 4.5 | Create useVideoPreview hook | `ui/src/hooks/useVideoPreview.ts` |
| 4.6 | Integrate video click handlers | Multiple files |

### Phase 5: Services & Types (Parallel)

| Task | Description | Files |
|------|-------------|-------|
| 5.1 | Extend API types for new models | `ui/src/lib/types.ts` |
| 5.2 | Add dataset/project API methods | `ui/src/services/api.ts` |
| 5.3 | Add React Query hooks for datasets/projects | `ui/src/services/queries.ts` |
| 5.4 | Add sample labeling helpers | `ui/src/services/sampling.ts` |

---

## API Endpoints Summary

### Samples (Existing, Extended)
```
POST   /samples              - Create sample (now accepts labels, scope)
GET    /samples              - List samples
GET    /samples/{id}         - Get sample with members
DELETE /samples/{id}         - Delete sample
POST   /samples/compare      - Compare samples
```

### Datasets (New)
```
POST   /datasets             - Create dataset from samples
GET    /datasets             - List datasets
GET    /datasets/{id}        - Get dataset with members (paginated)
GET    /datasets/{id}/members - Get dataset members
PATCH  /datasets/{id}        - Update dataset (labels, name, etc.)
DELETE /datasets/{id}        - Delete dataset
POST   /datasets/combine     - Combine multiple datasets
```

### Projects (New)
```
POST   /projects             - Create project
GET    /projects             - List projects
GET    /projects/{id}        - Get project with datasets
PATCH  /projects/{id}        - Update project
DELETE /projects/{id}        - Delete project
POST   /projects/{id}/datasets - Add dataset to project
DELETE /projects/{id}/datasets/{dataset_id} - Remove dataset
```

---

## Frontend Type Definitions

```typescript
// ui/src/lib/types.ts - additions

interface SampleLabels {
  system: {
    created_at: string;
    created_by: string;
    source_corpus: string;
    collection_run_id?: string;
  };
  research: {
    research_question?: string;
    methodology?: string;
    population?: string;
    sampling_frame?: string;
    notes?: string;
  };
  custom: Record<string, string>;
}

interface Sample {
  // ... existing fields
  scope: {
    channel_ids: string[];
    video_ids: string[];
    author_ids: string[];
    date_from?: string;
    date_to?: string;
  };
  filters_applied: Record<string, any>;
  labels: SampleLabels;
}

interface Dataset {
  dataset_id: string;
  name: string;
  description: string;
  sample_ids: string[];
  parent_dataset_ids: string[];
  labels: SampleLabels;
  total_members: number;
  entity_types: ("video" | "comment")[];
  source_scopes: string[];
  deduplicated: boolean;
  lineage_preserved: boolean;
  created_at: string;
  created_by: string;
  updated_at: string;
}

interface Project {
  project_id: string;
  name: string;
  description: string;
  dataset_ids: string[];
  labels: Record<string, string>;
  created_at: string;
  updated_at: string;
}
```

---

## Preset Templates

| Preset | Scope | Filters Applied | Sampling Method |
|--------|-------|-----------------|-----------------|
| **By Author(s)** | By Author | Include specified authors | Full Population |
| **By Channel** | By Channel | All videos in selected channels | Full Population |
| **By Video Criteria** | Custom | Video filters only | Full Population |
| **Random Sample** | All Data | None | Random (10%) |
| **Stratified by Month** | All Data | None | Stratified (month, 50/stratum) |
| **High Engagement** | All Data | Likes > 100, Replies > 5 | Random (500) |
| **Root Comments Only** | All Data | Type = Roots | Full Population |
| **Temporal Window** | All Data | Video upload: last 30 days | Full Population |

---

## Parallel Development Strategy

Each phase runs with **multiple sub-agents working concurrently** on independent files. No sequential dependencies within a phase.

**Launch pattern**: All tasks in a phase launched simultaneously via Task tool with appropriate subagent_type.

**Verification**: After each phase, run lint/typecheck and verify integration.

---

## Acceptance Criteria

1. **Sampling Workbench**: Researcher can define any combination of filters, see live preview, run sample, save with full labels
2. **Dataset Combination**: Multiple samples can be combined into dataset with deduplication and lineage tracking
3. **Project Organization**: Datasets can be grouped into projects with custom labels
4. **Comment Tree**: Click any comment anywhere → modal with full nested thread
5. **Video Preview**: Click any video anywhere → modal with full metadata
6. **All Labels**: Custom key-value labels work on samples, datasets, projects
7. **Reproducibility**: Every sample stores full scope, filters, seed, criteria for exact recreation

---

## File Structure Changes

```
SocialScienceResearch/
├── domain/
│   ├── sample_models.py (extended)
│   ├── dataset_models.py (new)
│   ├── project_models.py (new)
├── persistence/
│   ├── excel_repository.py (extended with dataset/project sheets)
│   ├── sample_repository.py (extended)
│   ├── dataset_repository.py (new)
│   ├── project_repository.py (new)
├── api/
│   ├── routers/
│   │   ├── samples.py (extended)
│   │   ├── datasets.py (new)
│   │   ├── projects.py (new)
├── ui/src/
│   ├── app/
│   │   ├── samples/page.tsx (rebuilt)
│   ├── components/features/
│   │   ├── sampling-workbench-new.tsx
│   │   ├── scope-selector.tsx
│   │   ├── filter-panel.tsx
│   │   ├── sampling-method-selector.tsx
│   │   ├── live-preview.tsx
│   │   ├── result-actions.tsx
│   │   ├── dataset-builder.tsx
│   │   ├── project-manager.tsx
│   │   ├── dataset-card.tsx
│   │   ├── comment-tree-modal.tsx
│   │   ├── video-metadata-preview.tsx
│   ├── hooks/
│   │   ├── useCommentTree.ts
│   │   ├── useVideoPreview.ts
│   ├── services/
│   │   ├── api.ts (extended)
│   │   ├── queries.ts (extended)
│   ├── lib/
│   │   ├── types.ts (extended)
```