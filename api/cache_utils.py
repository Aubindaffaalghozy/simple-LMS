from typing import Any, Optional

from django.core.cache import cache

CACHE_PREFIX = "simple_lms"


def build_course_cache_key(scope: str, identifier: str) -> str:
    """Build a cache key for course-related endpoints."""
    return f"{CACHE_PREFIX}:course:{scope}:{identifier}"


def get_cached_course_list(identifier: str) -> Optional[Any]:
    """Retrieve cached course list response."""
    return cache.get(build_course_cache_key("list", identifier))


def set_cached_course_list(identifier: str, value: Any, timeout: int = 300) -> None:
    """Store a course list response in cache."""
    cache.set(build_course_cache_key("list", identifier), value, timeout)


def get_cached_course_detail(course_id: int) -> Optional[Any]:
    """Retrieve a cached course detail response."""
    return cache.get(build_course_cache_key("detail", str(course_id)))


def set_cached_course_detail(course_id: int, value: Any, timeout: int = 300) -> None:
    """Store a course detail response in cache."""
    cache.set(build_course_cache_key("detail", str(course_id)), value, timeout)


def invalidate_course_cache(course_id: Optional[int] = None) -> None:
    """Invalidate course cache entries after writes."""
    if course_id is not None:
        cache.delete(build_course_cache_key("detail", str(course_id)))
    cache.delete(build_course_cache_key("list", "all"))
