"""
URL configuration for LMS project.
"""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import redis

try:
    from django.apps import apps
    apps.populate(settings.INSTALLED_APPS)
except Exception:
    pass

try:
    from api.views import api as api_router, dashboard_summary_view, analytics_dashboard_view
except Exception as exc:
    api_router = None
    dashboard_summary_view = None
    analytics_dashboard_view = None
    import logging
    logging.getLogger(__name__).warning("API router import failed: %s", exc)

from weather_api import get_weather


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
            'weather': '/weather/?city=Jakarta',
            'admin': '/admin/',
        }
    }, json_dumps_params={'indent': 2})


def weather_demo(request):
    """Demo endpoint for Redis caching."""
    city = request.GET.get('city', 'Jakarta')
    return JsonResponse(get_weather(city), json_dumps_params={'indent': 2})


urlpatterns = [
    path('', home, name='home'),
    path('health/', health_check, name='health'),
    path('cached/', cached_endpoint, name='cached'),
    path('weather/', weather_demo, name='weather'),
    path('dashboard/summary/', dashboard_summary_view, name='dashboard-summary') if dashboard_summary_view is not None else None,
    path('dashboard/analytics/', analytics_dashboard_view, name='dashboard-analytics') if analytics_dashboard_view is not None else None,
    path('admin/', admin.site.urls),
]

urlpatterns = [pattern for pattern in urlpatterns if pattern is not None]

if api_router is not None:
    urlpatterns.append(path('api/', api_router.urls))
