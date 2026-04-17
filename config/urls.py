"""
URL configuration for LMS project.
"""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import redis


def health_check(request):
    """Health check endpoint to verify all services are running."""
    try:
        # Test Database
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "✓ Connected"
    except Exception as e:
        db_status = f"✗ Error: {str(e)}"

    try:
        # Test Redis
        r = redis.Redis(host='redis', port=6379, db=0)
        r.ping()
        redis_status = "✓ Connected"
    except Exception as e:
        redis_status = f"✗ Error: {str(e)}"

    try:
        # Test Cache
        cache.set('test_key', 'test_value', 60)
        cache_value = cache.get('test_key')
        cache_status = "✓ Working" if cache_value else "✗ Cache Error"
    except Exception as e:
        cache_status = f"✗ Error: {str(e)}"

    return JsonResponse({
        'status': 'ok',
        'message': 'Simple LMS Application is running',
        'services': {
            'database': db_status,
            'redis': redis_status,
            'cache': cache_status,
        }
    }, json_dumps_params={'indent': 2})


@cache_page(60)
def cached_endpoint(request):
    """Test endpoint to verify caching is working."""
    import time
    current_time = time.time()
    return JsonResponse({
        'message': 'This response is cached for 60 seconds',
        'timestamp': current_time,
    })


def home(request):
    """Home page endpoint."""
    return JsonResponse({
        'message': 'Welcome to Simple LMS',
        'endpoints': {
            'health': '/health/',
            'cached': '/cached/',
            'admin': '/admin/',
        }
    }, json_dumps_params={'indent': 2})


urlpatterns = [
    path('', home, name='home'),
    path('health/', health_check, name='health'),
    path('cached/', cached_endpoint, name='cached'),
    path('admin/', admin.site.urls),
]
