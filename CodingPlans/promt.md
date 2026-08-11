# YouTube Computational Social Science Module — Implementation Prompt
I am about to implement a **new, separate module** in my existing project:

`C:\Users\DELL\graph-rag-agent`

This module will be an important component of the project's **Computational Social Science research pipeline**.

## 1. Read the project requirements first
Before making any changes, thoroughly inspect:

### Functional requirements
`C:\Users\DELL\graph-rag-agent\CodingPlans\functionality.md`

This contains the functionality and research requirements I have already defined.

### YouTube scraping library documentation
`C:\Users\DELL\graph-rag-agent\CodingPlans\youtubeScraper.md`

This contains the documentation and capabilities of the YouTube scraping library that this module must use.

**Do not duplicate the contents of these files in your response. Treat them as the source of truth.**

Also inspect the existing repository wherever necessary to understand:

- Current architecture
- Existing modules
- Project conventions
- Dependencies
- Configuration
- Data models
- Repository patterns
- Services
- Testing infrastructure
- Logging/error handling
- Documentation conventions
Reuse existing project infrastructure whenever appropriate.

---

# 2. Understand the role of this module
This is **not simply a YouTube scraper**.

It is a research-oriented **YouTube data acquisition and computational social science analytics module**.

The goal is to collect structured, reproducible YouTube data and preserve it so that it can support increasingly sophisticated research and analysis in the future.

The system must therefore prioritize:

- Data quality
- Reproducibility
- Provenance
- Persistent storage
- Historical observations
- Deduplication
- Incremental collection
- Configurable sampling
- Analytical extensibility
- Research transparency

---

# 3. Required user workflows
The module must support two primary entry points.

## A. Channel analysis
The user provides a YouTube channel URL.

The system should be able to:

1. Identify and validate the channel.
2. Collect channel metadata.
3. Discover its videos.
4. Preserve each video's stable ID, URL, metadata, and relevant statistics.
5. Collect comments where supported.
6. Preserve comment metadata and relationships.
7. Persist all collected information.
8. Perform the available analytics.
9. Produce structured research outputs.
10. Support future repeated collection of the same channel.
The architecture should support large channels through appropriate pagination, incremental collection, retries, deduplication, and resumability.

## B. Video analysis
The user provides a YouTube video URL.

The system should:

1. Validate/resolve the video.
2. Collect and persist video metadata.
3. Preserve its canonical URL and stable ID.
4. Collect available comments and related metadata.
5. Persist the collected information.
6. Run the relevant analytics.
7. Return/save structured analytical results.
Both workflows should share the same underlying domain/data architecture rather than becoming two unrelated implementations.

---

# 4. Persistent research dataset
All important collected data must be stored in an **external persistent source**.

For the first implementation, use **Excel**.

However:

> Excel must be treated as a persistence implementation, not as an architectural dependency.
Implement a Repository Pattern or an equivalent persistence abstraction so that we can later replace Excel with:

- SQL
- PostgreSQL
- SQLite
- Another relational database
- Another structured storage provider
without rewriting the application's business logic or analytics.

The conceptual architecture should be similar to:

```
YouTube
   ↓
Acquisition
   ↓
Normalization / Validation
   ↓
Domain
   ↓
Repository Interfaces
   ↓
Excel Repository
```
Later:

```
Repository Interfaces
   ↓
SQL / PostgreSQL / Other Provider
```
Do not spread Excel-specific logic throughout the application.

---

# 5. Research data and provenance
Preserve enough information to make the resulting dataset useful for serious social-science research.

Where available, retain:

- Channel ID
- Channel URL
- Channel metadata
- Video ID
- Video URL
- Video metadata
- Publication timestamp
- Comment ID
- Comment text
- Comment timestamp
- Comment likes
- Reply information
- Parent-child relationships
- Engagement statistics
- Collection timestamp
- Collection/run ID
- Source/provenance information
- Raw source values
- Derived analytical values
Clearly distinguish:

**source observations**

from

**values calculated by our system**.

Do not overwrite raw source information with derived metrics.

---

# 6. Historical and longitudinal research
Design the system with longitudinal research in mind.

A statistic collected today must not be represented as though it were the historical value at publication.

For example:

```
Video
 ├── published_at
 │
 ├── observation_2026_08_09
 │      ├── views
 │      ├── likes
 │      └── comments
 │
 └── observation_2026_09_09
        ├── views
        ├── likes
        └── comments
```
If the scraping library cannot provide historical statistics, **do not invent or estimate them**.

Instead, structure the system so repeated collection runs can generate historical observations.

This will allow future research such as:

- longitudinal audience response
- engagement growth
- changes in content performance
- changes in comment behavior
- temporal comparisons
- cohort analysis

---

# 7. Analytics
Implement the analytics defined in `functionality.md`.

In addition, you have freedom to introduce **new research-useful analytics** when justified.

Potential areas include:

### Video-level

- Engagement rates
- Views/likes/comments relationships
- Performance distributions
- Outlier detection
- Publication-period comparisons

### Channel-level

- Upload frequency
- Publishing cadence
- Engagement distributions
- High/low-performing video identification
- Temporal trends
- Video cohort comparisons

### Comment-level

- Comment engagement distributions
- Top/bottom engagement groups
- Comment timing
- Reply structures
- Comment concentration
- Audience-response patterns

### Sampling
The system should support configurable research sampling strategies where applicable, such as:

- Top X% by likes
- Bottom X% by likes
- Most recent X%
- Earliest X%
- Random samples
- Date-range samples
- Video-specific samples
- Stratified samples
Sampling should be reproducible and configurable rather than hardcoded.

Do not add analytics merely to increase the number of features.

Every additional analytical feature should have a defensible research purpose.

---

# 8. Computational Social Science research requirements
Treat the collected dataset as a **research dataset**, not merely application data.

The system should support:

### Reproducibility
A researcher should be able to determine how a dataset/result was produced.

### Provenance
Important observations should be traceable to their source and collection run.

### Sampling transparency
Sampling criteria should be explicit and reproducible.

### Temporal validity
Do not confuse publication time with observation time.

### Data-quality awareness
Track missing, unavailable, failed, or incomplete data.

### No fabrication
If YouTube/the library does not provide a value, represent it as unavailable rather than guessing.

### Raw vs derived data
Keep source observations separate from calculated metrics.

### Research snapshots
Where appropriate, preserve collection snapshots so later analysis can distinguish different observations of the same entity.

### Ethical/research awareness
Avoid collecting information that is unnecessary for the stated research purpose.

Do not introduce unnecessary personally identifying information merely because it is technically available.

---

# 9. Architecture
Follow the existing architecture of the project after inspecting it.

Do not blindly impose a new architecture.

Where appropriate, separate:

```
Acquisition
    ↓
Normalization
    ↓
Domain
    ↓
Persistence
    ↓
Analytics
    ↓
Research Outputs
```
The YouTube library should primarily belong to the acquisition/infrastructure side.

Analytics should not depend directly on the scraper library.

Repositories should abstract persistence.

This separation must make it possible to:

- Replace the YouTube source later
- Replace Excel later
- Test analytics without YouTube
- Test repositories without live YouTube requests
- Reprocess stored data without scraping again

---

# 10. Reliability
The YouTube scraper is an external dependency and can fail.

Design appropriately for:

- Network errors
- Rate limits
- Invalid URLs
- Deleted/private videos
- Removed comments
- Missing fields
- Partial collection
- Library exceptions
- Temporary failures
Use the existing project's retry/error-handling conventions where possible.

Do not silently discard failures.

Collection failures should be observable and associated with the relevant entity/run when practical.

---

# 11. Idempotency and deduplication
Repeated execution must not blindly create duplicate records.

Use stable identifiers such as:

- `channel_id`
- `video_id`
- `comment_id`
- `collection_run_id`
The system should be able to distinguish between:

- New entity
- Existing entity
- Updated observation
- Duplicate entity
- Failed collection
Repeated collection should therefore be safe.

---

# 12. Collection runs
If consistent with the project architecture, introduce a concept such as:

`CollectionRun`

to track:

- What was collected
- From which source
- When
- How many entities were discovered
- How many succeeded
- How many failed
- Which errors occurred
- Which analytical processing was performed
This is particularly important for research reproducibility.

---

# 13. Testing
Testing is mandatory.

For **every functionality**:

```
Implement
   ↓
Test
   ↓
Fix
   ↓
Document
   ↓
Continue
```
Do not implement the entire module and test only at the end.

Tests should cover appropriate combinations of:

- Domain logic
- Data normalization
- Repository behavior
- Excel persistence
- Deduplication
- Sampling
- Analytics
- Edge cases
- Error handling
Do not make the entire test suite dependent on live YouTube requests.

Use mocks, fixtures, or fake providers for unit tests.

Add controlled integration tests where appropriate.

After each functionality:

1. Write/update tests.
2. Run them.
3. Fix failures.
4. Run relevant regression tests.
5. Document the functionality.

---

# 14. Documentation
After each major functionality, update the appropriate documentation.

Document:

- Purpose
- Inputs
- Outputs
- Data model
- Configuration
- Research relevance
- Limitations
- Known library limitations
- Error behavior
- Examples
- Testing
Do not create unnecessary duplicate documentation.

Use the project's existing documentation structure.

---

# 15. Implementation process
Follow these phases.

## Phase 1 — Discovery
Read:

`functionality.md`

and:

`youtubeScraper.md`

Then inspect the relevant source code.

Understand the project before modifying it.

---

## Phase 2 — Research/requirements analysis
Extract:

- Functional requirements
- Research requirements
- Data entities
- Relationships
- Analytics
- Persistence requirements
- Sampling requirements
- Reproducibility requirements
- Testing requirements
Identify assumptions and limitations.

---

## Phase 3 — Architecture plan
Create a concrete implementation plan showing:

- Files/modules to create
- Existing files to modify
- Domain models
- Repository interfaces
- Excel implementation
- Services
- Analytics
- Collection workflow
- Tests
- Documentation
Keep the plan aligned with the existing project architecture.

---

## Phase 4 — Implementation
Implement incrementally.

Do not create a giant monolithic scraper.

Reuse existing abstractions.

Keep responsibilities separated.

---

## Phase 5 — Test + document continuously
After every functionality:

**implement → test → fix → document**

Do not mark a functionality complete until the tests pass and the documentation is updated.

---

## Phase 6 — Final validation
At the end:

- Run the complete relevant test suite.
- Verify imports.
- Verify persistence.
- Verify deduplication.
- Verify channel workflow.
- Verify video workflow.
- Verify analytics.
- Verify sampling.
- Verify provenance.
- Verify documentation.
- Verify that existing functionality still works.

---

# 16. Use your judgment
You have considerable freedom to improve the module.

You may add functionality that you believe will significantly increase its value for Computational Social Science research.

Before adding substantial functionality, evaluate:

1. Research usefulness
2. Data availability
3. Reproducibility
4. Architectural fit
5. Testability
6. Maintenance cost
7. Ethical/data-minimization considerations
Prefer **high-value research capabilities** over unnecessary feature accumulation.

If a useful metric is impossible to obtain reliably from the available YouTube library, document that limitation instead of fabricating or inferring unsupported values.

---

# 17. Final deliverables
When the implementation is complete, provide a concise final report containing:

1. Architecture implemented
2. Functionalities implemented
3. Additional research-oriented functionalities added
4. Files created/modified
5. Repository/persistence design
6. Analytics implemented
7. Tests created and executed
8. Test results
9. Documentation created/updated
10. Known limitations
11. YouTube/library limitations
12. Research limitations
13. How to use the module
14. How Excel can later be replaced with SQL
15. Recommended future improvements

---

# 18. Important instruction
**Do not simply follow `functionality.md` mechanically.**

Use it together with:

`youtubeScraper.md`

and your understanding of the existing project to design the best implementation.

You are allowed to identify missing functionality, architectural problems, research requirements, and useful analytical capabilities that are not explicitly mentioned in the Markdown files.

However, every significant addition should have a clear justification.

---

# Start
Start by:

1. Reading `functionality.md`.
2. Reading `youtubeScraper.md`.
4. Understanding how the new module should integrate with the existing system.
5. Producing the implementation plan.
6. Then beginning implementation.
**Do not start coding before completing the discovery and planning phase.**

Once implementation begins, work incrementally:

**Implement → Test → Fix → Document → Continue.**

The final result should be a maintainable, extensible, research-grade YouTube Computational Social Science module rather than a simple scraping utility.