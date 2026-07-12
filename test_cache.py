import time
from weather_api import get_weather


def main():
    # First call - should be slow (2 seconds)
    start = time.time()
    result1 = get_weather("Jakarta")
    time1 = time.time() - start
    print(f"First call: {time1:.2f}s")
    print(result1)

    # Second call - should be fast (< 0.1 second)
    start = time.time()
    result2 = get_weather("Jakarta")
    time2 = time.time() - start
    print(f"Second call (cached): {time2:.2f}s")
    print(result2)

    print("\nCatatan: setelah 5 menit cache akan expired. Untuk demo, cek TTL di Redis.")


if __name__ == "__main__":
    main()
