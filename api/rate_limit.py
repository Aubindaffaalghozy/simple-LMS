from django.http import JsonResponse
from ninja.errors import HttpError


class SimpleRateLimitMiddleware:
    """A simple per-IP rate limiter for API endpoints."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
            key = f"ratelimit:{client_ip}:{request.path}"
            from django.core.cache import cache

            count = cache.get(key, 0)
            if count >= 60:
                return JsonResponse(
                    {'detail': 'Too many requests. Please try again later.'},
                    status=429,
                )

            cache.set(key, count + 1, 60)
        return self.get_response(request)
