# YouTube Computational Social Science — Frontend UX/UI Planning Prompt

You already understand the project, its requirements, the YouTube scraping library, the backend architecture, and the functionality implemented in the previous phase.

You  already implemented the backend and understand the available services, repositories, analytics, endpoints, and data flow.

Now your task is to act as a:

> **Senior UX/UI architect specializing in research software, Computational Social Science, data-intensive analytical applications, and research workflows.**

Your goal in this phase is **NOT to implement the frontend yet**.

Your goal is to create a strong, implementation-ready **UX/UI and frontend architecture plan** for the research module.

---

# 1. Product perspective

The frontend is not supposed to behave like a normal YouTube analytics dashboard.

This is a:

> **Computational Social Science Research Workbench**

The primary user is a researcher who wants to:

```text
Select research target
        ↓
Collect / inspect data
        ↓
Understand the dataset
        ↓
Explore analytical patterns
        ↓
Sample data
        ↓
Compare entities
        ↓
Explore relationships/networks
        ↓
Create research datasets
        ↓
Export / use the data in further research
```

The UX must support this research workflow rather than simply exposing backend endpoints as pages.

---

# 2. Your first task: audit the backend from a UX perspective

Since you already implemented the backend, inspect the actual functionality and endpoints you created.

Do not simply create:

```text
endpoint → page
endpoint → page
endpoint → page
```

Instead determine:

* Which endpoints belong to the same research workflow?
* Which operations should appear together?
* Which analyses are primary?
* Which analyses are secondary/drill-down operations?
* Which endpoints are better represented as tabs?
* Which should be actions?
* Which should be background operations?
* Which belong to a research workspace?
* Which should be accessible globally?
* Which results should be visualizations?
* Which results should be tables?
* Which results require both?
* Which data should be shown immediately?
* Which data should only load on demand?

Identify any backend capabilities that currently have no good UX representation.

---

# 3. Design around research entities, not endpoints

The main objects researchers interact with are things such as:

* Channel
* Video
* Comment
* Recommendation relationship
* Collection
* Research sample
* Dataset
* Network

Design the information architecture around these entities and their relationships.

For example:

```text
Channel
 ├── Videos
 │    ├── Analytics
 │    ├── Comments
 │    └── Recommendations
 │
 ├── Audience / Engagement
 ├── Temporal Analysis
 ├── Comparisons
 └── Research Samples
```

and:

```text
Video
 ├── Overview
 ├── Analytics
 ├── Comments
 ├── Temporal Behavior
 ├── Recommendations
 └── Network Context
```

These are conceptual examples.

You must determine the best structure based on the actual backend capabilities.

---

# 4. Design the main research workflows

Identify the major user journeys rather than merely listing screens.

At minimum, think through workflows such as:

### Channel research

```text
Enter channel
    ↓
Collect / open existing data
    ↓
Channel overview
    ↓
Performance analysis
    ↓
Temporal analysis
    ↓
Video exploration
    ↓
Comment/audience exploration
    ↓
Sampling
    ↓
Dataset
```

### Video research

```text
Enter video
    ↓
Video overview
    ↓
Advanced analytics
    ↓
Comment analysis
    ↓
Recommendation exploration
    ↓
Network exploration
    ↓
Sampling
    ↓
Dataset
```

### Recommendation research

```text
Select video
    ↓
Observed recommendations
    ↓
Compare recommendations
    ↓
Explore relationships
    ↓
Network
    ↓
Network analysis
    ↓
Temporal network analysis
```

### Research sampling

```text
Choose population
    ↓
Define filters
    ↓
Choose sampling strategy
    ↓
Preview sample
    ↓
Validate
    ↓
Save research sample
```

### Dataset workflow

```text
Select data
    ↓
Inspect population
    ↓
Apply filters/sample
    ↓
Review data quality
    ↓
Create dataset
    ↓
Inspect dataset
    ↓
Export
```

Refine these workflows based on the actual implementation.

---

# 5. Information architecture

Design the complete information architecture.

Determine:

* Global navigation
* Primary sections
* Secondary navigation
* Entity navigation
* Breadcrumbs
* Research workspace structure
* Analysis navigation
* Dataset navigation
* Network navigation

Avoid excessive top-level navigation.

The researcher should always understand:

> Where am I?

> What entity am I studying?

> What analysis am I viewing?

> What dataset/filter context am I using?

---

# 6. Research workspace concept

Consider whether the application should use a **research workspace model** rather than independent pages.

For example:

```text
Research Workspace
│
├── Target
├── Dataset
├── Filters
├── Analysis
├── Samples
└── Results
```

Evaluate whether this model would improve continuity for long research sessions.

Do not force this architecture if another approach is better.

Explain the reasoning behind the chosen approach.

---

# 7. UX hierarchy for analytics

Do not expose all analytics equally.

Classify analytical capabilities into:

### Primary

The most important analysis a researcher should see immediately.

### Secondary

Useful analytical tools available through the workspace.

### Advanced

More specialized research operations that should remain accessible without overwhelming the main interface.

For every major entity, decide:

* What appears in the overview?
* What requires a drill-down?
* What belongs in an advanced analysis section?
* What should be visualized?
* What should be represented as a table?
* What should be both?

---

# 8. Recommendation/network UX

Treat the recommendation functionality as one of the most important research experiences.

The researcher should be able to move naturally from:

```text
Video
 ↓
Observed recommendations
 ↓
Recommendation relationships
 ↓
Network
 ↓
Network analysis
```

Plan how users switch between:

* Recommendation list
* Recommendation details
* Relationship view
* Graph/network view
* Network statistics
* Temporal network view

The network visualization should never be the only representation.

Researchers must be able to inspect the underlying records.

---

# 9. Comment/audience research UX

Plan a workflow that treats comments as research data rather than a social-media feed.

Researchers should be able to move from:

```text
Video
 ↓
Comment population
 ↓
Distribution
 ↓
Sampling
 ↓
Temporal analysis
 ↓
Replies / interaction
 ↓
Network
```

Determine how the UI should expose the advanced comment analytics already supported by the backend.

---

# 10. Sampling UX

Sampling is a research operation, not just a filter.

Design a workflow where researchers understand:

```text
Population
   ↓
Criteria
   ↓
Sampling method
   ↓
Sample size
   ↓
Preview
   ↓
Final sample
```

The interface must make the sampling methodology visible.

The researcher should never wonder:

> "Why are these records in my sample?"

---

# 11. Data provenance UX

Plan how provenance appears throughout the application.

Researchers should be able to understand:

* When data was collected
* Which collection produced it
* Whether it is raw or derived
* Whether the data is complete
* What sampling/filtering was applied
* What limitations apply

Do not hide all provenance inside a separate technical page.

Decide where contextual provenance should appear throughout the workflow.

---

# 12. Data quality UX

Design a consistent UX for:

* Missing data
* Partial collections
* Failed collections
* Duplicates
* Unsupported information
* Temporal gaps
* Incomplete recommendation observations

Determine how these states should appear in:

* Dashboards
* Tables
* Entity pages
* Dataset pages
* Analysis results

Never silently turn missing information into zero.

---

# 13. Analytical visualization strategy

For every major analytical capability, decide the most appropriate representation.

Consider:

* Line charts
* Histograms
* Distribution plots
* Scatter plots
* Rankings
* Tables
* Timelines
* Cohort views
* Network graphs
* Comparison views

Do not add charts merely because the application is analytical.

Every visualization should answer a research question.

For each major visualization, explain:

1. What question it answers.
2. What data it uses.
3. Why this visualization is appropriate.
4. What contextual information must accompany it.

---

# 14. Comparison UX

Design comparison as a first-class research capability.

Researchers may compare:

* Videos
* Channels
* Time periods
* Cohorts
* Recommendation neighborhoods
* Samples

Plan a consistent comparison experience.

Avoid making comparison simply a table with many numbers.

Where appropriate, provide:

* Normalized comparisons
* Relative performance
* Distribution comparisons
* Temporal comparisons

---

# 15. Research history and longitudinal UX

The application should support repeated observations.

Plan how researchers can distinguish:

```text
Publication date
```

from:

```text
Observation / collection date
```

Plan interfaces for:

* Historical observations
* Collection snapshots
* Temporal comparisons
* Changes in recommendations
* Changes in engagement
* Longitudinal analysis

This is particularly important for Computational Social Science research.

---

# 16. Search and discovery

Design how researchers find:

* Channels
* Videos
* Datasets
* Samples
* Collections

Consider a global search and/or command interface if it improves the workflow.

Researchers should not need to remember where a particular entity was stored.

---

# 17. Long-running operations

Some research operations may take significant time.

Plan UX for:

* Collection
* Large comment retrieval
* Recommendation collection
* Dataset creation
* Large analytical operations

Determine:

* When to use asynchronous/background behavior
* Progress indicators
* Collection status
* Partial completion
* Retry
* Failure recovery

The UX should never make a long-running research operation appear frozen.

---

# 18. Empty/loading/error states

Plan these deliberately.

For each major workflow define:

### Empty

Why is there no data and what can the researcher do?

### Loading

What is currently happening?

### Partial

What succeeded and what did not?

### Error

What went wrong and what can the researcher do?

### Unsupported

Does the underlying library simply not provide the requested information?

Avoid generic:

> Something went wrong.

---

# 19. Desktop research experience

The primary use case is serious desktop research.

Optimize for:

* Dense tables
* Multiple analytical panels
* Filtering
* Side-by-side comparisons
* Network exploration
* Long research sessions

But maintain sensible responsive behavior for smaller screens.

Do not design a mobile-first consumer interface if that compromises the research workflow.

---

# 20. Visual design direction

Define a visual language appropriate for academic/research software.

The design should communicate:

* Trust
* Precision
* Analytical depth
* Clarity
* Professionalism

Avoid:

* Consumer YouTube imitation
* Marketing-dashboard aesthetics
* Excessive animations
* Excessive gradients
* Giant KPI cards
* Decorative elements that compete with research data

The UI should feel like a serious analytical instrument.

---

# 21. Accessibility and usability

Plan for:

* Keyboard navigation
* Clear focus states
* Semantic controls
* Accessible tables
* Accessible charts where possible
* Color-independent meaning
* Readable typography
* Clear hierarchy
* Reduced visual noise

---

# 22. Frontend architecture planning

Based on the existing frontend stack, plan:

* Routes
* Page hierarchy
* Layouts
* Shared components
* Feature components
* API/service layer
* State management
* Data fetching/caching
* URL state
* Loading/error boundaries
* Network visualization architecture
* Table architecture

Do not invent technologies unnecessarily.

Use the project's existing stack unless there is a concrete reason to introduce something new.

---

# 23. API-to-UX mapping

Create a planning matrix that maps backend capabilities to UX.

For each backend capability determine:

* Where it appears
* What triggers it
* What data it returns
* Whether it is a page, tab, modal, drawer, action, chart, table, or background operation
* What loading state it requires
* What error states it requires
* Whether it belongs to a research workflow or infrastructure

The objective is to prevent the frontend from becoming a collection of disconnected endpoint screens.

---

# 24. Plan the complete frontend before implementation

Your planning output must include:

## A. Product structure

Explain the overall UX concept.

## B. Information architecture

Show the hierarchy of the application.

## C. Main user journeys

Show the important research workflows step by step.

## D. Route/page plan

List the proposed routes and explain the purpose of each.

## E. Entity workspace design

Explain how Channel, Video, Comments, Recommendations, Datasets, Samples, and Networks relate to one another.

## F. Analytics presentation plan

Map analytical capabilities to appropriate visualizations/tables/interactions.

## G. Research interaction model

Explain filtering, sampling, comparison, provenance, history, and dataset creation.

## H. Component architecture

Identify reusable components and feature-specific components.

## I. State/data architecture

Explain what should live in:

* URL state
* Server state
* Local UI state

## J. Responsive strategy

Explain how the desktop research workflow adapts to smaller screens.

## K. Accessibility strategy

Define the important accessibility requirements.

## L. Testing strategy

Define the frontend testing strategy before implementation.

---

# 25. Critical requirement: improve the product, don't merely reproduce it

You have freedom to improve the UX beyond the current backend structure.

If you identify a better way to organize existing capabilities, propose it.

If several endpoints should logically become one research workflow, group them.

If one backend capability needs a better frontend interaction, design it.

If the current backend exposes something that should not be directly exposed as a UI action, explain why.

If an important research workflow is missing from the backend, identify it as a **backend gap** rather than silently inventing frontend behavior.

The goal is not:

> "Make a UI for everything that exists."

The goal is:

> **Create the best possible research experience using the capabilities that exist, while clearly identifying what must be added to support the ideal experience.**

---

# 26. Do not implement yet

This phase is strictly for planning.

Do not start building pages or components until the UX/UI plan is complete.

First produce the plan.

The plan should be concrete enough that another engineer could implement the frontend directly from it without having to redesign the product.

After the plan, clearly separate:

### Already supported by backend

### Requires frontend implementation

### Requires backend changes

### Recommended future enhancements

Then wait for approval before beginning implementation.
