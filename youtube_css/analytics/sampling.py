"""Video sampling methods for research.

Supports stratified temporal sampling, random sampling, and
engagement-based sampling.
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

from domain.enums import SamplingMethod
from domain.models import Video


class VideoSampler:
    """Sampler for selecting video subsets for research."""

    @staticmethod
    def sample(
        videos: List[Video],
        method: SamplingMethod,
        n: int = 20,
        strata: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> List[Video]:
        """Sample videos using the specified method."""
        if seed is not None:
            random.seed(seed)

        if method == SamplingMethod.RANDOM:
            return VideoSampler._random_sample(videos, n)
        elif method == SamplingMethod.STRATIFIED_TEMPORAL:
            return VideoSampler._stratified_temporal(videos, n, strata or "year")
        elif method == SamplingMethod.TOP_VIEWS:
            return VideoSampler._top_by(videos, n, lambda v: v.raw_metadata.get("view_count", 0))
        elif method == SamplingMethod.BOTTOM_VIEWS:
            return VideoSampler._bottom_by(videos, n, lambda v: v.raw_metadata.get("view_count", 0))
        elif method == SamplingMethod.TOP_ENGAGEMENT:
            return VideoSampler._top_by(
                videos, n, lambda v: v.raw_metadata.get("like_count", 0) + v.raw_metadata.get("comment_count", 0)
            )
        elif method == SamplingMethod.BOTTOM_ENGAGEMENT:
            return VideoSampler._bottom_by(
                videos, n, lambda v: v.raw_metadata.get("like_count", 0) + v.raw_metadata.get("comment_count", 0)
            )
        elif method == SamplingMethod.TOP_COMMENT_RATE:
            return VideoSampler._top_by(
                videos,
                n,
                lambda v: VideoSampler._safe_div(
                    v.raw_metadata.get("comment_count", 0), v.raw_metadata.get("view_count", 1)
                ),
            )
        elif method == SamplingMethod.TOP_LIKE_RATE:
            return VideoSampler._top_by(
                videos,
                n,
                lambda v: VideoSampler._safe_div(
                    v.raw_metadata.get("like_count", 0), v.raw_metadata.get("view_count", 1)
                ),
            )
        elif method == SamplingMethod.TOP_COMMENTS:
            return VideoSampler._top_by(videos, n, lambda v: v.raw_metadata.get("comment_count", 0))
        elif method == SamplingMethod.LONGEST:
            return VideoSampler._top_by(videos, n, lambda v: v.duration or 0)
        elif method == SamplingMethod.SHORTEST:
            return VideoSampler._bottom_by(videos, n, lambda v: v.duration or float("inf"))
        else:
            return VideoSampler._random_sample(videos, n)

    @staticmethod
    def _random_sample(videos: List[Video], n: int) -> List[Video]:
        if len(videos) <= n:
            return list(videos)
        return random.sample(videos, n)

    @staticmethod
    def _top_by(videos: List[Video], n: int, key: Callable[[Video], float]) -> List[Video]:
        sorted_videos = sorted(videos, key=key, reverse=True)
        return sorted_videos[:n]

    @staticmethod
    def _bottom_by(videos: List[Video], n: int, key: Callable[[Video], float]) -> List[Video]:
        sorted_videos = sorted(videos, key=key)
        return sorted_videos[:n]

    @staticmethod
    def _stratified_temporal(videos: List[Video], n: int, strata: str) -> List[Video]:
        """Stratified sampling by time period.

        Divides videos into temporal strata and samples evenly from each.
        """
        if not videos:
            return []

        def get_stratum(v: Video) -> int:
            if v.upload_date is None:
                return 0
            if strata == "year":
                return v.upload_date.year
            elif strata == "month":
                return v.upload_date.year * 100 + v.upload_date.month
            elif strata == "week":
                return v.upload_date.isocalendar()[1]
            else:
                return v.upload_date.year

        groups: Dict[int, List[Video]] = {}
        for v in videos:
            s = get_stratum(v)
            groups.setdefault(s, []).append(v)

        if not groups:
            return []

        per_stratum = max(1, n // len(groups))
        result: List[Video] = []
        for group in groups.values():
            if len(group) <= per_stratum:
                result.extend(group)
            else:
                result.extend(random.sample(group, per_stratum))

        # If we have room, fill with random from remaining
        if len(result) < n:
            remaining = [v for v in videos if v not in result]
            needed = n - len(result)
            if remaining:
                result.extend(random.sample(remaining, min(needed, len(remaining))))

        return result[:n]

    @staticmethod
    def _safe_div(a: float, b: float) -> float:
        return a / b if b != 0 else 0.0
