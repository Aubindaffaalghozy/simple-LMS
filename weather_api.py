import json
import os
import time
import requests
import redis

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6380")),
    db=int(os.getenv("REDIS_DB", "0")),
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


def get_weather(city: str):
    """Simulasi API call lambat dengan Redis caching selama 5 menit."""
    cache_key = f"weather:{city.lower()}"

    try:
        cached = r.get(cache_key)
        if cached is not None:
            return {"city": city, "source": "cache", "data": json.loads(cached)}
    except redis.exceptions.ConnectionError:
        cached = None

    time.sleep(2)  # Simulasi API lambat
    try:
        response = requests.get(f"https://api.example.com/weather/{city}", timeout=5)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        payload = {"city": city, "condition": "sunny", "temp_c": 30}

    try:
        r.setex(cache_key, 300, json.dumps(payload))
    except redis.exceptions.ConnectionError:
        pass

    return {"city": city, "source": "api", "data": payload}
