```markdown
# Research API Design for YouTube Channel Analysis

## Overview
This API is designed for **research purposes**, enabling comprehensive analysis of YouTube channels from multiple dimensions: time, popularity, engagement, discussion structure, comments, audience, content, and changes across periods or channels.

The API is built around **research questions** rather than just yt-dlp functions.

---

## 1. Channel / Corpus Endpoints

Start with endpoints that define the channel corpus:

```text
GET /channel/{id}/overview
GET /channel/{id}/videos
GET /channel/{id}/videos/count
GET /channel/{id}/videos/timeline
GET /channel/{id}/videos/compare
```

### Supported Filters:
```text
date_from
date_to
video_type
duration_min
duration_max
views_min
views_max
upload_hour
upload_weekday
keywords
tags
category
```

### Example:
```text
/channel/X/videos?date_from=2020-01-01&date_to=2023-12-31
```

---

## 2. Video Sampling Endpoints

Essential for comparative research.

### Top Performing Videos:
```text
GET /channel/{id}/videos/top-views        # Highest viewed
GET /channel/{id}/videos/bottom-views     # Lowest viewed
GET /channel/{id}/videos/top-engagement   # Highest engagement
GET /channel/{id}/videos/bottom-engagement # Lowest engagement
GET /channel/{id}/videos/top-comment-rate # Highest comments/views ratio
GET /channel/{id}/videos/top-like-rate    # Highest likes/views ratio
GET /channel/{id}/videos/top-comments     # Most comments
GET /channel/{id}/videos/longest          # Longest duration
GET /channel/{id}/videos/shortest         # Shortest duration
```

### Sampling Methods:
```text
GET /channel/{id}/videos/random-sample    # Random selection
GET /channel/{id}/videos/stratified-sample # Balanced temporal sampling
```

### Stratified Sample Example:
```json
{
  "period": "2020-2023",
  "strata": "year",
  "sample_per_stratum": 20
}
```

**Result:**
```text
2020 → 20 videos
2021 → 20 videos
2022 → 20 videos
2023 → 20 videos
```

> **Note:** This is far superior to random sampling for temporal comparisons.

---

## 3. Video Metadata

Each selected video returns **complete metadata**:

```text
GET /video/{video_id}
```

### Stored Fields:
```text
video_id
title
description
channel
channel_id
upload_date
upload_timestamp
duration
views
likes
comments_count
tags
categories
language
thumbnail
chapters
live_status
availability
age_limit
```

*Additional technical metadata available as needed.*

---

## 4. Comments Endpoints

### All Comments:
```text
GET /video/{id}/comments
```

**Parameters:**
```text
date_from
date_to
sort
limit
```

### Top Percentile by Likes:
```text
GET /video/{id}/comments/top-percentile
```

**Example:**
```text
percentile=90  # Top 10%
```

**Supported Percentiles:**
```text
75, 90, 95, 99
```

### Bottom Percentile by Likes:
```text
GET /video/{id}/comments/bottom-percentile
```

**Example:**
```text
percentile=10  # Bottom 10%
```

> **Important:** Don't rely solely on this - a comment with 0 likes vs 1 like may be functionally similar. Keep the raw `like_count`.

### Latest Percentile:
```text
GET /video/{id}/comments/latest-percentile
```

**Also available:**
```text
GET /video/{id}/comments/latest
```

### Oldest Percentile:
```text
GET /video/{id}/comments/oldest-percentile
```

> **Research Value:** Compare **Early audience** vs **Later audience** behavior.

### Date Range:
```text
GET /video/{id}/comments/date-range
```

**Parameters:**
```text
from=2020-01-01
to=2023-12-31
```

### Advanced Period Comparison:
```text
GET /video/{id}/comments/periods
```

**Request:**
```json
{
  "periods": [
    ["2020-01-01", "2020-12-31"],
    ["2021-01-01", "2021-12-31"],
    ["2022-01-01", "2022-12-31"]
  ]
}
```

**Returns:** Same statistics for each period.

---

## 5. Reply Analysis

### Most-Replied Comments:
```text
GET /video/{id}/comments/top-replied
```

**Sort by:** `reply_count`

> **Insight:** Identifies comments generating the **most discussion** - often more socially significant than likes alone.

### Reply Threshold Filter:
```text
GET /video/{id}/comments/by-replies
```

**Example:**
```text
min_replies=20
```

**Returns:**
```text
Comment A → 157 replies
Comment B → 91 replies
Comment C → 43 replies
```

### Comment Thread Structure:
```json
{
  "comment": {...},
  "replies": [...],
  "reply_count": 37
}
```

> **Goal:** Each comment becomes a **conversation unit**.

### Reply Depth Analysis:
```text
GET /video/{id}/comments/deepest-threads
```

**Tracked Fields:**
```text
root_comment
parent_comment
reply_depth
```

> **Research Question:** Where do the most branched discussions occur?

---

## 6. Engagement Metrics

### Comment Engagement Score:
```text
GET /video/{id}/comments/top-engagement
```

**Formula Options:**
```text
comment_score = likes + replies
```

> **Note:** Make the metric configurable - don't enforce a single formula.

### Comment Length Analysis:
```text
GET /video/{id}/comments/longest
GET /video/{id}/comments/shortest
GET /video/{id}/comments/by-length
```

**Length Bins:**
```text
0-50
51-100
101-250
251-500
500+
```

> **Key Insight:** Comment count ≠ discussion quality.

### Comment Velocity:
```text
GET /video/{id}/comments/velocity
```

**Returns:**
```text
Hour 0 → 4,230 comments
Hour 1 → 2,190
Hour 2 → 1,102
...
Day 7 → 82
```

> **Purpose:** Measure **reaction speed** across different videos.

### Engagement Decay:
```text
GET /video/{id}/engagement-decay
```

**Returns:**
```text
Day 1  → 45%
Day 2  → 21%
Day 7  → 8%
Day 30 → 2%
```

> **Comparison:** **Viral burst** vs **Long-tail engagement**

---

## 7. Ratios and Patterns

### Engagement Ratios:
```text
GET /video/{id}/engagement-ratios
```

**Returns:**
```text
comments / views
likes / views
replies / comments
```

> **Importance:** These ratios are crucial for comparing videos with different audience sizes.

### Interaction Pattern:
```text
GET /video/{id}/interaction-pattern
```

**Outputs:**
```text
likes per 1k views
comments per 1k views
replies per 1k comments
```

---

## 8. Temporal Analysis

### Comment Timing Relative to Upload:
```text
comment_age_at_posting
```

**Example:**
```text
Comment A → posted 7 minutes after video
Comment B → posted 4 hours after video
Comment C → posted 11 days after video
```

> **Research Value:** Compare **early reaction** vs **late reaction** even across different upload years.

### Period Comparison:
```text
GET /channel/{id}/compare-periods
```

**Request:**
```json
{
  "period_a": ["2020-01-01", "2021-12-31"],
  "period_b": ["2024-01-01", "2025-12-31"]
}
```

**Returns Changes In:**
```text
video_count
median_views
mean_views
median_comments
median_likes
comment_rate
like_rate
reply_rate
comment_length
thread_depth
engagement_velocity
change_percentage
```

---

## 9. Cross-Channel Comparison

### Compare Multiple Channels:
```text
POST /channels/compare
```

**Request:**
```json
{
  "channels": ["A", "B", "C"],
  "period": ["2020-2023"]
}
```

**Metrics Compared:**
```text
publishing frequency
views
engagement
comment behavior
reply behavior
content length
audience activity
```

---

## 10. Publishing Analysis

### Time-of-Day Analysis:
```text
GET /channel/{id}/upload-time-analysis
```

**Analyzes:**
```text
hour
weekday
month
season
```

**Example Output:**
```text
Friday 20:00 → median views = X
Monday 10:00 → median views = Y
```

### Publishing Strategy:
```text
GET /channel/{id}/publishing-pattern
```

**Metrics:**
```text
videos/week
videos/month
average gap
median gap
bursts
inactive periods
```

> **Question:** Did the channel transition from daily to weekly publishing?

---

## 11. Content Evolution

### Content Analysis:
```text
GET /channel/{id}/content-evolution
```

**Uses:** Transcript, title, description

**NLP Outputs:**
```text
topics by year
keywords by year
entities by year
themes by year
```

**Example:**
```text
2020 → Topic A 45%
2021 → Topic A 30%
2022 → Topic B 50%
2023 → Topic C 62%
```

> **Correlates:** Content change with audience interaction change.

### Audience Reaction Evolution:
```text
GET /channel/{id}/audience-evolution
```

**Tracks Over Time:**
```text
comment volume
comment velocity
like distribution
reply distribution
thread depth
comment length
early-vs-late comments
```

**Future NLP Integration:**
```text
sentiment
stance
topics
emotions
```

**Framework:**
```text
Content Evolution
        ↕
Audience Reaction Evolution
        ↕
Interaction Structure
```

---

## 12. Statistical Distribution

### Distribution Metrics:
> **Critical:** Don't return just averages.

**Return:**
```text
min
P10
P25
median
P75
P90
P95
P99
max
```

> **Why:** Comment engagement is often **highly skewed**.
> - 98% comments → 0-10 likes
> - 2% comments → thousands

### Engagement Concentration:
```text
GET /video/{id}/engagement-concentration
```

**Measures:** Is engagement distributed across the audience or concentrated in few comments?

**Potential Metrics:**
- Gini coefficient
- top 1% share
- top 5% share
- top 10% share

**Example:**
```text
Top 10% comments → 73% of all comment likes
```

> **Value:** This is **socially more significant** than "average likes."

---

## 13. Participation Structure

### Reply Rate:
```text
GET /video/{id}/reply-rate
```

**Example:**
```text
10,000 root comments
2,100 have replies
```

**Calculates:**
```text
thread initiation rate
average replies/thread
median replies/thread
```

### Audience Participation:
```text
GET /video/{id}/participation
```

**If author data available:**
```text
unique commenters
repeat commenters
comments per commenter
```

> **Important Distinction:**
> - 10,000 comments from **10,000 people** vs
> - 10,000 comments from **500 people** (20 comments each)
>
> **Social difference is enormous.**

> **Caution:** Handle author identifiers and privacy with care.

---

## 14. Research Query Endpoint

### Unified Research Query:
```text
POST /research/query
```

**Example Request:**
```json
{
  "channel": "CHANNEL_ID",
  
  "videos": {
    "period": ["2020-01-01", "2023-12-31"],
    "sampling": "top_and_bottom",
    "top_n": 20,
    "bottom_n": 20
  },
  
  "comments": {
    "samples": [
      "top_10_percent_likes",
      "bottom_10_percent_likes",
      "latest_10_percent",
      "oldest_10_percent",
      "most_replied"
    ],
    "include_replies": true
  },
  
  "analytics": [
    "engagement_distribution",
    "comment_velocity",
    "reply_rate",
    "thread_depth",
    "engagement_concentration"
  ]
}
```

> **Integration:** Agents can translate natural language research questions into this format.

---

## Final Architecture

```
                 ┌────────────────────┐
                 │   CHANNEL INPUT    │
                 └─────────┬──────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      VIDEO SAMPLING               CHANNEL ANALYSIS
             │                           │
      ┌──────┼──────┐             ┌──────┼──────┐
      ▼      ▼      ▼             ▼      ▼      ▼
    Date   Views  Duration      Time   Volume  Frequency
      │
      ▼
  VIDEO METADATA
      │
      ├───────────────┐
      ▼               ▼
  TRANSCRIPT       COMMENTS
                      │
        ┌─────────────┼─────────────────┐
        ▼             ▼                 ▼
     Top 10%       Latest 10%       Lowest 10%
     Likes         Comments         Likes
        │             │                 │
        └─────────────┼─────────────────┘
                      ▼
                COMMENT THREADS
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Replies     Velocity    Timing
          │
          ▼
       NETWORK
          │
          ▼
    NLP / ANALYSIS
          │
          ▼
  ┌──────────────────────────┐
  │ TEMPORAL COMPARISON      │
  │ CHANNEL COMPARISON       │
  │ AUDIENCE EVOLUTION       │
  │ CONTENT EVOLUTION        │
  │ INTERACTION PATTERNS     │
  └──────────────────────────┘
```

---

## Critical Takeaways

### The 5 Most Important Additional Features:

1. **Comment Velocity** - Speed of comment arrival
2. **Comment Age Relative to Video** - Timing relative to video age
3. **Engagement Concentration/Gini** - Is interaction concentrated in a minority?
4. **Unique vs Repeat Commenters** - Is interaction broad or driven by a small group?
5. **Stratified Sampling** - Balanced temporal sampling rather than relying solely on top performers

---

## Research Questions This Enables

With this design, you can answer questions like:

> *"How did audience interaction patterns change for this channel between 2020-2022 and 2024-2026? Did the discussion structure itself change, or just its volume?"*

The necessary raw data is preserved, rather than just presenting a dashboard with numbers.
```

addtional funstionality 
# 19. Video Recommendation / Feed Analysis Endpoint

Add a dedicated endpoint/workflow for **video recommendation and feed analysis**.

This functionality is separate from ordinary video analytics.

## Objective

When a user provides a YouTube video URL, the system should:

1. Analyze the requested video using the analytics implemented by this module.
2. Collect the videos that are observable in the recommendation/feed context associated with that video, **to the extent supported by the selected YouTube scraping library**.
3. Preserve the relevant metadata and identifiers for those recommended videos.
4. Preserve the relationship between the original video and the observed recommended videos.
5. Persist this information through the repository/persistence layer.
6. Make the resulting data suitable for future **network analysis with NetworkX**.

The purpose is to allow the research system to eventually construct a directed recommendation network such as:

```text
Video A → Video B
Video A → Video C
Video A → Video D
Video B → Video C
...
```

Do **not** prescribe a specific database schema for this functionality. Determine the appropriate domain models, entities, relationships, and persistence structure after inspecting the existing architecture and the capabilities documented in `youtubeScraper.md`.

---

## Endpoint

Create an appropriate application endpoint for this workflow.

The endpoint should accept a YouTube video as its input and return:

* Analytics for the requested video.
* The observable recommended/feed videos associated with it.
* Relevant metadata for those videos.
* The observed relationship between the original video and the recommendations.
* Appropriate collection/provenance information.

Follow the project's existing API and service conventions when deciding the endpoint name, request model, response model, and implementation structure.

---

## Recommendation relationships

Treat recommendations as **observed relationships**, not as permanent properties of YouTube.

YouTube's recommendation system is dynamic, so the system should preserve the fact that a particular recommendation relationship was observed during a particular collection.

If the library provides recommendation ordering or ranking information, preserve it because it may be valuable for future research.

If the same source video is collected again later and its recommendations have changed, the system must not incorrectly overwrite the previous research observation.

Design this according to the existing project's data architecture rather than imposing a predefined schema.

---

## Network-analysis preparation

The collected recommendation data must be **network-ready**.

The design should allow a future module to construct a NetworkX graph in which:

* Videos can become nodes.
* Observed recommendations can become directed edges.
* Video metadata can become node attributes.
* Recommendation-specific information can become edge attributes.
* Observation/collection information can support temporal network analysis.

Do not tightly couple this module to NetworkX unless there is a strong architectural reason to do so.

The responsibility of this module is to produce reliable, persistent, network-ready research data.

A future module can then transform that data into NetworkX graphs and perform:

* Degree analysis
* In-degree/out-degree analysis
* Centrality analysis
* Community detection
* Clustering
* Path analysis
* Connected-component analysis
* Cross-channel network analysis
* Temporal network analysis
* Recommendation concentration analysis

---

## Computational Social Science value

Design this functionality with future research questions in mind.

For example:

* Which videos are repeatedly connected through recommendations?
* Which channels are strongly connected through the recommendation system?
* Which videos receive recommendations from many different source videos?
* Which videos act as bridges between content communities?
* Are recommendation relationships concentrated within the same channel?
* How frequently do recommendations cross channel boundaries?
* Are there identifiable recommendation communities?
* How does the observable recommendation network change over time?
* Which videos become structurally important within the network?
* Does recommendation structure differ across different content periods or channel groups?

These analyses do not necessarily need to be implemented now.

The important requirement is that the data collected by this module should preserve enough information to make these analyses possible later.

---

## Observation and research validity

Be precise about what this functionality actually measures.

The collected data represents **recommendations observable through the selected collection method at the time of collection**.

It must not be described as a complete representation of YouTube's internal recommendation algorithm.

If the scraping library exposes only a subset of recommendations, document that limitation clearly.

If recommendation information is unavailable, restricted, incomplete, or unsupported by the library:

* Do not fabricate results.
* Do not silently treat missing data as zero recommendations.
* Preserve an appropriate collection status/error.
* Document the limitation.

---

## Historical observations

The design should support repeated observation of the same video's recommendation environment.

For example, collecting the same video at different points in time may produce different recommendation sets.

The system should preserve those observations in a way that allows future research into:

* Recommendation-network evolution
* Changes in recommendation relationships
* Emerging/disappearing connections
* Temporal clustering
* Changes in channel connectivity
* Changes in network centrality

Do not overwrite historical observations simply because newer recommendations were collected.

Use the project's existing persistence and domain architecture to determine the best implementation.

---

## Configuration

Recommendation collection should be configurable where supported by the library.

Potential configuration may include things such as:

* Number of recommendations to collect
* Whether additional metadata should be collected
* Whether channel information should be collected
* Whether additional statistics should be collected
* Collection depth or scope

Do not hardcode these decisions unnecessarily.

Only expose configuration that is actually supported and useful.

---

## Testing

Add dedicated tests for this workflow.

Test the important behaviors, including:

* Valid video input
* Invalid input
* Successful video analysis
* Successful recommendation collection
* Multiple recommendations
* Recommendation ordering when available
* Duplicate handling
* Repeated collection
* Persistence
* Historical observations
* Partial failures
* Library limitations
* Network-ready output

Use mocks/fixtures for external YouTube interactions where appropriate.

Do not make the entire test suite dependent on live YouTube requests.

---

## Documentation

Document this functionality after implementation.

The documentation should explain:

* What the endpoint does
* What "recommendation" means in this system
* What information is collected
* How the data is persisted
* How observations are handled over time
* What the scraping library can and cannot provide
* Research limitations
* How the resulting data can later be transformed into NetworkX graphs

Do not hardcode a specific database schema in the documentation unless it is actually part of the implemented architecture.

---

## Architectural principle

Keep the responsibilities separated:

```text
YouTube
   ↓
Recommendation observation
   ↓
Collection / normalization
   ↓
Domain
   ↓
Repository
   ↓
Persistent research dataset
   ↓
Future NetworkX analysis
```

The current module should focus on **reliably collecting and preserving recommendation relationships**.

The future network-analysis module should be responsible for transforming those observations into graphs and performing graph/network analysis.
