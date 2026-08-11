"""Computational social science metrics for YouTube data.

All metrics distinguish source observations from derived calculations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from domain.models import Comment, Video, VideoObservation


@dataclass
class DistributionResult:
    """Statistical distribution summary."""

    min_val: float
    p10: float
    p25: float
    median: float
    p75: float
    p90: float
    p95: float
    p99: float
    max_val: float
    mean: float
    std: float
    count: int


class EngagementMetrics:
    """Engagement-related metrics."""

    @staticmethod
    def like_rate(likes: Optional[int], views: Optional[int]) -> Optional[float]:
        if likes is None or views is None or views == 0:
            return None
        return likes / views

    @staticmethod
    def comment_rate(comments: Optional[int], views: Optional[int]) -> Optional[float]:
        if comments is None or views is None or views == 0:
            return None
        return comments / views

    @staticmethod
    def reply_rate(root_comments: int, comments_with_replies: int) -> Optional[float]:
        if root_comments == 0:
            return None
        return comments_with_replies / root_comments

    @staticmethod
    def engagement_score(
        likes: Optional[int],
        comments: Optional[int],
        replies: Optional[int],
        views: Optional[int],
        weights: Optional[Dict[str, float]] = None,
    ) -> Optional[float]:
        if views is None or views == 0:
            return None
        w = weights or {"likes": 1.0, "comments": 2.0, "replies": 3.0}
        score = 0.0
        if likes is not None:
            score += likes * w.get("likes", 1.0)
        if comments is not None:
            score += comments * w.get("comments", 2.0)
        if replies is not None:
            score += replies * w.get("replies", 3.0)
        return score / views

    @staticmethod
    def interaction_pattern(
        likes: Optional[int], comments: Optional[int], replies: Optional[int], views: Optional[int]
    ) -> Dict[str, Optional[float]]:
        if views is None or views == 0:
            return {"likes_per_1k": None, "comments_per_1k": None, "replies_per_1k_comments": None}
        return {
            "likes_per_1k": (likes or 0) / views * 1000 if likes is not None else None,
            "comments_per_1k": (comments or 0) / views * 1000 if comments is not None else None,
            "replies_per_1k_comments": (replies or 0) / (comments or 1) * 1000
            if replies is not None and comments
            else None,
        }

    @staticmethod
    def engagement_concentration(comment_likes: List[int]) -> Dict[str, float]:
        """Calculate engagement concentration (Gini-like metrics).

        Returns top 1%, 5%, 10% share of total likes.
        """
        if not comment_likes:
            return {"gini": 0.0, "top_1_pct_share": 0.0, "top_5_pct_share": 0.0, "top_10_pct_share": 0.0}
        sorted_likes = sorted(comment_likes, reverse=True)
        total = sum(sorted_likes)
        if total == 0:
            return {"gini": 0.0, "top_1_pct_share": 0.0, "top_5_pct_share": 0.0, "top_10_pct_share": 0.0}
        n = len(sorted_likes)
        results: Dict[str, float] = {}
        for pct in [1, 5, 10]:
            k = max(1, int(n * pct / 100))
            share = sum(sorted_likes[:k]) / total
            results[f"top_{pct}_pct_share"] = share
        # Simple Gini approximation
        cumsum = 0.0
        for i, val in enumerate(sorted_likes):
            cumsum += (i + 1) * val
        gini = (2 * cumsum) / (n * total) - (n + 1) / n
        results["gini"] = max(0.0, gini)
        return results


class TemporalMetrics:
    """Temporal analysis metrics."""

    @staticmethod
    def comment_velocity(comments: List[Comment], video_upload: datetime, bins_hours: List[int] = None) -> Dict[int, int]:
        """Count comments per time bin after upload."""
        if bins_hours is None:
            bins_hours = [1, 2, 6, 12, 24, 48, 72, 168]
        velocity: Dict[int, int] = {h: 0 for h in bins_hours}
        for c in comments:
            if c.posted_at and video_upload:
                age_hours = (c.posted_at - video_upload).total_seconds() / 3600
                for h in bins_hours:
                    if age_hours <= h:
                        velocity[h] += 1
        return velocity

    @staticmethod
    def comment_age_distribution(comments: List[Comment], video_upload: datetime) -> List[int]:
        """Return comment ages in seconds relative to video upload."""
        ages: List[int] = []
        for c in comments:
            if c.posted_at and video_upload:
                age = int((c.posted_at - video_upload).total_seconds())
                ages.append(age)
        return ages

    @staticmethod
    def publishing_pattern(videos: List[Video]) -> Dict[str, Any]:
        """Analyze publishing frequency and patterns."""
        if not videos:
            return {}
        dates = sorted([v.upload_date for v in videos if v.upload_date])
        if len(dates) < 2:
            return {"video_count": len(dates), "average_gap_days": None, "median_gap_days": None}
        gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        return {
            "video_count": len(dates),
            "average_gap_days": sum(gaps) / len(gaps),
            "median_gap_days": sorted(gaps)[len(gaps) // 2],
            "min_gap_days": min(gaps),
            "max_gap_days": max(gaps),
        }

    @staticmethod
    def upload_time_analysis(videos: List[Video]) -> Dict[str, Dict[int, int]]:
        """Analyze upload times by hour and weekday."""
        hours: Dict[int, int] = {h: 0 for h in range(24)}
        weekdays: Dict[int, int] = {d: 0 for d in range(7)}
        for v in videos:
            if v.upload_date:
                hours[v.upload_date.hour] += 1
                weekdays[v.upload_date.weekday()] += 1
        return {"hours": hours, "weekdays": weekdays}


class DistributionMetrics:
    """Statistical distribution calculations."""

    @staticmethod
    def percentile(values: List[float], p: float) -> float:
        if not values:
            return 0.0
        s = sorted(values)
        k = (len(s) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return s[int(k)]
        return s[f] * (c - k) + s[c] * (k - f)

    @staticmethod
    def distribution(values: List[float]) -> DistributionResult:
        if not values:
            return DistributionResult(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        s = sorted(values)
        n = len(s)
        mean = sum(s) / n
        variance = sum((x - mean) ** 2 for x in s) / n
        return DistributionResult(
            min_val=min(s),
            p10=DistributionMetrics.percentile(s, 10),
            p25=DistributionMetrics.percentile(s, 25),
            median=DistributionMetrics.percentile(s, 50),
            p75=DistributionMetrics.percentile(s, 75),
            p90=DistributionMetrics.percentile(s, 90),
            p95=DistributionMetrics.percentile(s, 95),
            p99=DistributionMetrics.percentile(s, 99),
            max_val=max(s),
            mean=mean,
            std=math.sqrt(variance),
            count=n,
        )

    @staticmethod
    def engagement_distribution(observations: List[VideoObservation]) -> Dict[str, DistributionResult]:
        views = [o.views for o in observations if o.views is not None]
        likes = [o.likes for o in observations if o.likes is not None]
        comments = [o.comments_count for o in observations if o.comments_count is not None]
        return {
            "views": DistributionMetrics.distribution(views),
            "likes": DistributionMetrics.distribution(likes),
            "comments": DistributionMetrics.distribution(comments),
        }
