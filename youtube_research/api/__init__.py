"""
API endpoints for YouTube research.

Provides REST API for channel analysis, video analysis,
and research queries.
"""

from .routes import router

__all__ = ['router']