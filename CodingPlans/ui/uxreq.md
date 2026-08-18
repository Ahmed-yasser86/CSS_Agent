# YouTube Computational Social Science Module â€” Full Research-Grade Redesign, Gap Analysis, Planning & Implementation

## Mission

The current implementation is **far below the intended scope of this project**.

It currently behaves too much like a basic YouTube analytics application:

```text
Researcher enters URL
        â†“
System collects a predefined set of data
        â†“
System displays static metrics
```

This is **not the intended product**.

The intended system is a **research-grade Computational Social Science data collection, analysis, sampling, comparison, and research-dataset construction platform**.

The researcher must have substantial control over:

* What entities are collected
* Which variables are collected
* Which videos are included
* Which comments are included
* Which time periods are included
* Which sampling strategies are used
* Which thresholds are applied
* Which analytical operations are performed
* Which datasets are constructed
* Which entities are compared
* Which relationships are explored
* What data is exported

The frontend and backend must support this research workflow rather than forcing researchers into a fixed scraping recipe.

---

# 1. Important: do not start implementation

Do **not** immediately redesign the UI.

First perform a complete audit of the current implementation.

You already understand the project requirements and have already worked with:

`CodingPlans/functionality.md`

and:

`CodingPlans/youtubeScraper.md`

You also implemented the current backend.

Therefore, use your existing understanding, but now critically compare the **actual implementation** against the intended research system.

Do not assume that because an endpoint exists, the corresponding capability is actually complete.

Inspect the implementation and determine what is genuinely implemented versus what is only represented by an endpoint, placeholder, simplified logic, or static assumption.

---

# 2. Core product correction

The product must be understood as:

> **A configurable Computational Social Science research data collection and analytical environment for YouTube.**

It is not:

> "A dashboard that analyzes a YouTube URL."

The researcher is the primary decision-maker.

The system should provide powerful defaults, but defaults must not become fixed methodological assumptions.

The researcher must be able to define the collection experiment.

Conceptually:

```text
Researcher
    â†“
Defines research target
    â†“
Defines population
    â†“
Defines variables
    â†“
Defines temporal boundaries
    â†“
Defines inclusion/exclusion criteria
    â†“
Defines sampling strategy
    â†“
Defines collection depth
    â†“
Runs collection
    â†“
Inspects collected data
    â†“
Analyzes
    â†“
Compares
    â†“
Samples / constructs dataset
    â†“
Exports / continues research
```

---

# 3. Researcher-controlled data collection

This is one of the biggest missing capabilities.

The current system must NOT assume a fixed collection recipe.

The researcher should be able to configure the collection.

For example, depending on what the scraping library actually supports, the researcher may need to control:

### Target

* Channel
* Video
* Multiple channels
* Multiple videos
* Search/discovery result
* Recommendation neighborhood

### Video variables

Allow the researcher to select which available video metadata/statistics to collect.

Do not hardcode one fixed set if the scraper exposes additional useful variables.

### Comments

Allow control over:

* Whether comments are collected
* Comment limits
* Sampling
* Ranking criteria
* Time ranges
* Comment/reply collection
* Engagement thresholds
* Percentage-based selection

### Temporal criteria

Support researcher-defined periods such as:

```text
2020-01-01 â†’ 2023-12-31
```

rather than forcing a predefined time window.

### Quantitative criteria

Allow criteria such as:

* Top X%
* Bottom X%
* Minimum views
* Maximum views
* Minimum likes
* Minimum comments
* Engagement thresholds
* Date constraints
* Combination of conditions

### Sampling

Allow researchers to explicitly define:

* Population
* Sampling method
* Sample size
* Sampling percentage
* Stratification variables
* Random seed where relevant
* Inclusion/exclusion rules

The actual supported capabilities must be derived from the scraper and project architecture.

---

# 4. Collection configuration must be a first-class research object

Do not treat collection configuration as a handful of query parameters attached to an endpoint.

A collection should conceptually represent a **research collection experiment**.

It should preserve the researcher's choices so that the researcher can understand:

> What exactly did I ask the system to collect?

and later:

> Can I reproduce or inspect this collection?

The UX and backend should therefore support configurable collection definitions, validation, execution, progress tracking, and provenance.

Do not prescribe a database schema.

Design the domain model according to the existing architecture.

---

# 5. Complete data visibility

The current UI apparently hides too much of the collected data.

This is unacceptable for a research data collection system.

The researcher must be able to inspect the **actual collected dataset**, not only derived summary cards.

For every major entity, provide a way to inspect raw/observed records.

For example:

```text
Channel
    â†“
Videos
    â†“
Video metadata
    â†“
Comments
    â†“
Replies
    â†“
Recommendation observations
    â†“
Collection metadata
```

Researchers should be able to inspect:

* Individual records
* All available fields
* Collection timestamps
* Source URLs
* Identifiers
* Relationships
* Missing values
* Collection status

The UI should not reduce a large research dataset to six KPI cards.

---

# 6. Raw data vs analytical data

Clearly separate:

### Observed/source data

Data collected from YouTube.

### Derived data

Metrics calculated by our system.

### Research artifacts

Samples, datasets, comparison results, network representations, etc.

The UI should allow researchers to inspect the underlying observations used to produce an analysis.

A chart should never become the only representation of the underlying data.

---

# 7. Video scripts/transcripts storage

Video scripts/transcripts must **not be stored directly inside Excel cells**.

The implementation should store the actual script/transcript content as external `.txt` files in an appropriate persistent directory.

The persistent research record should contain the **path/reference to the external file**, rather than duplicating the complete script inside Excel.

The design must:

* Create deterministic/unique file names.
* Avoid accidental overwriting.
* Preserve the relationship between a video and its script.
* Handle missing scripts.
* Handle failed extraction.
* Preserve provenance.
* Make the stored file accessible to the researcher where appropriate.

Do not store large script text redundantly inside Excel.

The repository abstraction must continue to allow migration from Excel to SQL or another persistence provider later.

---

# 8. Repository architecture

The persistence implementation currently uses Excel, but Excel is an initial storage provider, not the permanent architectural boundary.

The system must preserve the Repository Pattern.

Business logic, analytics, collection logic, and research workflows should not depend directly on Excel-specific implementation details.

The architecture should make it possible to replace:

```text
Excel
```

with:

```text
SQL / PostgreSQL / another provider
```

without rewriting the research/business layer.

Audit the current implementation for violations of this principle.

If services are directly coupled to Excel behavior, identify and correct them.

---

# 9. Channel research must be comprehensive

A researcher entering a channel should not simply receive a static list of videos and a few metrics.

The channel workflow should allow the researcher to define what population of videos they want.

Examples:

```text
All videos
```

or:

```text
Videos between 2020â€“2023
```

or:

```text
Top 10% by likes
```

or:

```text
Most recent 10%
```

or:

```text
Videos above a minimum engagement threshold
```

or a combination of criteria supported by the implementation.

Then the researcher should be able to analyze:

* Video population
* Publishing patterns
* Engagement distributions
* Performance distributions
* Temporal behavior
* Content cohorts
* Outliers
* Comment behavior
* Audience participation
* Recommendation relationships

---

# 10. Video research must be comprehensive

A researcher entering a video should receive a **research workspace**, not a static information page.

The workflow should allow:

```text
Video
 â”œâ”€â”€ Observed metadata
 â”œâ”€â”€ Statistics
 â”œâ”€â”€ Script/transcript
 â”œâ”€â”€ Comments
 â”œâ”€â”€ Comment distributions
 â”œâ”€â”€ Comment engagement
 â”œâ”€â”€ Temporal behavior
 â”œâ”€â”€ Recommendation context
 â”œâ”€â”€ Related videos
 â””â”€â”€ Research comparisons
```

All available collected information should be discoverable.

---

# 11. Video-to-video comparison

This is currently insufficient or missing.

Researchers must be able to compare multiple videos.

Comparison should support appropriate dimensions such as:

* Views
* Likes
* Comments
* Engagement
* Publication timing
* Comment activity
* Comment distributions
* Performance relative to channel baseline
* Temporal behavior
* Recommendation relationships
* Other available analytical variables

The comparison system must not be hardcoded to only two videos.

Design it to support a meaningful research comparison set.

---

# 12. Channel-to-channel comparison

Researchers must also be able to compare multiple channels.

Comparison should potentially include:

* Publishing behavior
* Video volume
* Engagement
* Performance distributions
* Audience participation
* Comment behavior
* Temporal patterns
* Recommendation connectivity
* Content cohorts
* Other supported research variables

Allow researchers to choose the comparison dimensions where appropriate.

Do not create a giant table containing every metric by default.

---

# 13. Flexible comparison methodology

Comparison should support researcher-defined contexts.

For example:

```text
Channel A vs Channel B
```

could mean:

```text
All videos
```

or:

```text
Videos published during the same period
```

or:

```text
Top 10% of videos
```

or:

```text
Videos satisfying the same engagement criteria
```

The UI should make the comparison population explicit.

This is essential for valid research comparisons.

---

# 14. Advanced analytics audit

Audit the current backend and frontend against the intended advanced analytics.

Identify missing or underdeveloped capabilities around:

### Channel analytics

* Engagement distributions
* Performance distributions
* Temporal engagement
* Content cohorts
* Content lifecycle
* Outliers
* Upload behavior
* Cross-period comparison

### Video analytics

* Engagement analysis
* Performance benchmarking
* Comment engagement
* Comment distributions
* Comment concentration
* Comment temporal behavior
* Discussion depth
* Video-to-video comparison

### Audience/comment analytics

* Participation
* Repeat participation where observable
* Comment concentration
* Reply structures
* Comment distributions
* Comment sampling
* Temporal participation

### Recommendation analytics

* Recommendation collection
* Recommendation inspection
* Same-channel vs cross-channel relationships
* Recommendation ranking/position where available
* Recommendation network construction data
* Network statistics
* Community analysis
* Cross-channel analysis
* Temporal network analysis

Do not assume every item is possible.

Verify each against the actual scraper capabilities and implementation.

---

# 15. Recommendation/feed research

The video workflow must include the ability to investigate the observable recommendation/feed context of a video.

The researcher should be able to:

```text
Open Video
    â†“
Collect/inspect observed recommendations
    â†“
Inspect recommended videos
    â†“
Inspect their metadata
    â†“
Explore relationships
    â†“
Construct network-ready research data
```

The system must preserve observation context and should support repeated collection over time.

The UI should make it clear that this represents **observed recommendation data**, not access to YouTube's internal recommendation algorithm.

---

# 16. Network research

The recommendation data should eventually support NetworkX-based analysis.

The frontend should therefore provide an interface for:

* Network exploration
* Node inspection
* Edge inspection
* Filtering
* Search
* Neighborhood exploration
* Channel filtering
* Temporal filtering
* Network statistics
* Community analysis
* Centrality analysis where supported
* Cross-channel network analysis

The graph should not replace the underlying data table.

Researchers must always be able to inspect the records behind the graph.

---

# 17. Research dataset builder

This is a major missing concept.

The application should allow a researcher to construct a research dataset from collected data.

Conceptually:

```text
Collected population
        â†“
Researcher-defined criteria
        â†“
Filtered population
        â†“
Sampling
        â†“
Validation
        â†“
Research dataset
```

The researcher should be able to define:

* Population
* Variables
* Time range
* Inclusion criteria
* Exclusion criteria
* Sampling criteria
* Comparison groups
* Relevant entities

The system should show a preview before dataset creation.

---

# 18. Data dictionary / variable selection

The application should provide researchers with visibility into the variables available for collection and analysis.

The researcher should be able to understand:

* Variable name
* Meaning
* Source
* Data type
* Availability
* Whether observed or derived
* Relevant limitations

Where technically feasible, researchers should be able to choose which variables they want to collect or include in a research dataset.

Do not force every research project to use the same fixed variable set.

---

# 19. Data quality and coverage

The system must provide research-oriented data-quality information.

Researchers should be able to see:

* Missing data
* Collection failures
* Partial collections
* Duplicate records
* Unsupported fields
* Temporal gaps
* Incomplete recommendations
* Coverage of the requested population
* Difference between requested and actually collected data

For example:

```text
Requested:
1,000 videos

Collected:
943 videos

Failed:
37

Unavailable:
20
```

The exact presentation should be determined during UX planning.

---

# 20. Collection execution UX

Collection may be long-running.

Design a serious collection-management workflow.

Researchers should be able to see:

* What collection is running
* What criteria were selected
* Progress
* Items discovered
* Items collected
* Failures
* Partial results
* Completion state
* Errors
* Retry/resume possibilities where supported

Do not make a long-running collection look like a normal synchronous API request.

---

# 21. Research reproducibility

Every important research operation should preserve enough context to understand what happened.

The system should support provenance around:

* Collection
* Filtering
* Sampling
* Analysis
* Dataset creation

Researchers should be able to reconstruct:

> What data produced this result?

and:

> What criteria produced this dataset?

---

# 22. Frontend problems to explicitly investigate

Audit the current frontend for problems including, but not limited to:

* Static URL-first workflow
* Fixed collection assumptions
* Limited researcher control
* Hidden collected fields
* Excessive KPI-card usage
* Poor data visualization
* Missing raw-data inspection
* Missing advanced analysis workflows
* Missing comparison workflows
* Missing sampling workflow
* Missing dataset construction
* Missing provenance
* Missing collection configuration
* Missing data-quality visibility
* Poor network exploration
* Poor temporal exploration
* Poor table functionality
* Weak filtering
* Weak search/discovery
* Disconnected pages
* Endpoint-driven rather than research-driven navigation
* Lack of research context
* Poor empty/loading/error states
* Inability to understand what data is actually being analyzed

Do not assume these are the only problems.

Find additional problems yourself.

---

# 23. Backend problems to explicitly investigate

Audit the backend for:

* Hardcoded collection variables
* Hardcoded limits
* Fixed sampling assumptions
* Missing collection configuration
* Missing variable selection
* Missing filtering primitives
* Missing comparison services
* Missing analytical services
* Analytics implemented only superficially
* Services coupled to persistence
* Excel-specific business logic
* Missing provenance
* Missing collection history
* Missing reproducibility
* Missing data-quality reporting
* Missing script external storage
* Missing persistent recommendation observations
* Missing network-ready data
* Missing error/partial collection handling
* Missing retry/resume behavior
* Missing validation
* Missing tests
* Missing documentation

Again, this is not an exhaustive list.

Inspect the actual implementation and identify all meaningful architectural and functional gaps.

---

# 24. Do not prescribe schemas prematurely

Do not invent a database schema merely to satisfy this planning exercise.

Determine the appropriate domain entities, models, relationships, repositories, and persistence mechanisms from:

* Existing architecture
* Existing implementation
* Research requirements
* Scraper capabilities

The important requirement is the **behavior and research capability**, not a predetermined table design.

---

# 25. UX redesign requirements

The new UI should be built around the researcher's workflow.

It should include appropriate experiences for:

* Research home
* Collection configuration
* Channel research
* Video research
* Raw data inspection
* Comment research
* Recommendation research
* Network exploration
* Video comparison
* Channel comparison
* Sampling
* Dataset construction
* Dataset inspection
* Collection history
* Data quality
* Provenance

These are capabilities to plan, not necessarily one page per item.

Group them into a coherent information architecture.

---

# 26. Visualization requirements

The current visualization approach is insufficient.

Design a visualization strategy that allows researchers to understand the **actual collected data**, not just summary statistics.

Consider appropriate representations for:

* Distributions
* Rankings
* Time series
* Cohorts
* Comparisons
* Correlations
* Engagement distributions
* Comment distributions
* Temporal comment activity
* Recommendation relationships
* Networks
* Channel relationships
* Data quality
* Sampling populations

For every visualization ask:

> What research question does this help answer?

Do not add decorative charts.

Tables must remain first-class research tools.

---

# 27. Researcher control vs sensible defaults

The system should provide sensible defaults for usability.

However:

> **Defaults must never become hidden methodological decisions.**

Researchers should be able to inspect and modify important collection and analysis criteria.

When defaults are used, the UI should make them visible.

---

# 28. Harvard/MIT-level research quality bar

Treat the intended users as professional computational social scientists.

Do not design this as a beginner analytics application.

The quality bar is:

* Methodological transparency
* Researcher control
* Reproducibility
* Data provenance
* Data completeness visibility
* Flexible sampling
* Rich raw-data access
* Powerful comparison
* Longitudinal analysis
* Network analysis
* Clear distinction between observation and inference
* Professional data visualization
* Scalable data workflows

The UI should feel like a serious research instrument.

Do not add superficial complexity merely to make the application look advanced.

Every capability must have a research purpose.

---

# 29. Complete redesign plan

Before implementation, produce a comprehensive plan with the following sections.

## A. Current-state audit

Explain what currently exists.

## B. Backend gap analysis

List every important missing or insufficient backend capability.

For each:

* Problem
* Why it matters scientifically
* Proposed capability
* Required implementation work
* Priority

## C. Frontend gap analysis

List every important UX/UI/functionality gap.

For each:

* Problem
* Research impact
* Proposed solution
* Priority

## D. Research workflow architecture

Define the complete researcher journey.

## E. Information architecture

Define navigation and entity/workspace relationships.

## F. Collection system redesign

Explain how researcher-controlled collection should work.

## G. Variable/criteria selection

Explain how researchers select data variables and collection criteria.

## H. Analytics architecture

Map analytical capabilities to research workflows.

## I. Comparison architecture

Design video-to-video, channel-to-channel, and relevant cross-entity comparisons.

## J. Sampling architecture

Design researcher-controlled sampling and dataset construction.

## K. Recommendation/network architecture

Design the recommendation exploration and future NetworkX workflow.

## L. Raw-data inspection architecture

Design how researchers inspect the complete collected data.

## M. Visualization strategy

Map research questions to appropriate visualizations and tables.

## N. Provenance and reproducibility

Define how the system communicates research provenance.

## O. Data quality

Define how collection quality and coverage are communicated.

## P. Script/transcript storage

Define the external TXT-file storage workflow and Excel path/reference handling.

## Q. Repository architecture

Verify Excel remains replaceable by SQL or another provider.

## R. Frontend architecture

Define routes, components, state, data fetching, and visualization architecture.

## S. Testing strategy

Define backend and frontend tests.

---

# 30. Testing is mandatory

Testing is part of the implementation, not an optional final step.

For every implemented capability:

```text
Implement
   â†“
Unit test
   â†“
Integration test
   â†“
Fix
   â†“
Document
```

Where appropriate, include end-to-end tests.

### Backend testing should cover

* Collection configuration
* Variable selection
* Filtering
* Sampling
* Channel collection
* Video collection
* Comments
* Recommendations
* Comparisons
* Analytics
* Persistence
* Script storage
* Repository abstraction
* Data quality
* Partial failures
* Retry/resume
* Provenance

### Frontend testing should cover

* Research workflows
* Collection configuration
* Filtering
* Sampling
* Comparison
* Data tables
* Visualization
* Recommendation exploration
* Network interaction
* Dataset creation
* Loading states
* Empty states
* Partial states
* Error states
* Responsive behavior
* Accessibility

Do not consider a feature complete until it has appropriate tests.

---

# 31. Documentation is mandatory

Every major capability must have appropriate documentation.

Document:

* What it does
* Why it exists
* How it is configured
* What data it produces
* What limitations apply
* How it should be used for research
* How it is tested

Do not create documentation that merely repeats code.

The documentation should help another researcher/engineer understand the methodological and technical behavior of the system.

---

# 32. Implementation order

Do not implement the frontend first while the backend has major capability gaps.

Use this order:

```text
1. Full audit
       â†“
2. Gap analysis
       â†“
3. Research architecture
       â†“
4. Backend capability corrections
       â†“
5. Backend tests
       â†“
6. Backend documentation
       â†“
7. Frontend UX architecture
       â†“
8. Frontend implementation
       â†“
9. Frontend tests
       â†“
10. Integration testing
       â†“
11. Final research workflow validation
       â†“
12. Documentation
```

If a frontend requirement exposes a backend gap, stop and address the backend capability rather than building a fake frontend abstraction around it.

---

# 33. Priority system

Classify identified work as:

### P0 â€” Fundamental

Without this, the system does not satisfy the research objective.

### P1 â€” Research-critical

Required for serious research workflows.

### P2 â€” Advanced

Important sophisticated capabilities.

### P3 â€” Enhancement

Useful but not fundamental.

Do not prioritize based on how visually impressive a feature is.

Prioritize based on research value and architectural importance.

---

# 34. Final requirement

Do not try to defend the current implementation.

Assume that the current implementation may contain substantial conceptual mistakes.

Be critical.

Your job is to determine:

> **What would this system actually need to become a serious Computational Social Science research platform?**

Then compare that target against the current implementation.

Identify the gaps honestly.

Do not hide missing functionality simply because an endpoint with a similar name already exists.

A route called:

`/videos/analyze`

does not mean "video research" is complete.

A route called:

`/recommendations/analyze`

does not mean "recommendation research" is complete.

Evaluate the actual capability behind each feature.

---

# 35. Deliverable before coding

Your first response should be the **complete audit and implementation plan only**.

It should contain:

1. Executive assessment of the current system
2. Backend gap analysis
3. Frontend gap analysis
4. Missing research capabilities
5. Researcher-controlled collection design
6. Data-variable/criteria design
7. Comparison design
8. Sampling design
9. Raw-data inspection design
10. Script/transcript storage correction
11. Recommendation/network research design
12. Visualization strategy
13. Information architecture
14. UX workflows
15. Backend implementation phases
16. Frontend implementation phases
17. Testing strategy
18. Documentation strategy
19. Priority classification
20. Definition of done

**Do not start implementation until this plan is complete and internally consistent.**

The plan must be detailed enough to serve as the blueprint for rebuilding the module into a genuine research-grade Computational Social Science platform.

