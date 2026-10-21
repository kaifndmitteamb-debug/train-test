"""
Concurrent load testing tool for FastAPI server.
Sends 50 concurrent requests to /health and /cache-test.

Requirements Note:
    pip install requests
    (Note: 'requests' is for load testing only and should not be added to server requirements.txt)

Usage:
    python load_test.py <BASE_URL>
    e.g.:
    python load_test.py http://localhost:8000
    python load_test.py https://train-test.onrender.com
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests


def send_request(url: str):
    start = time.perf_counter()
    try:
        response = requests.get(url, timeout=15)
        elapsed_ms = (time.perf_counter() - start) * 1000
        is_error = response.status_code != 200
        return {
            "success": not is_error,
            "status_code": response.status_code,
            "latency_ms": elapsed_ms,
            "error": None if not is_error else f"HTTP {response.status_code}",
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "success": False,
            "status_code": None,
            "latency_ms": elapsed_ms,
            "error": str(e),
        }


def calculate_stats(results):
    total = len(results)
    if total == 0:
        return {}

    errors = sum(1 for r in results if not r["success"])
    latencies = [r["latency_ms"] for r in results]
    latencies.sort()

    avg_ms = sum(latencies) / total
    min_ms = latencies[0]
    max_ms = latencies[-1]

    # p95 response time calculation
    p95_index = int(0.95 * total)
    if p95_index >= total:
        p95_index = total - 1
    p95_ms = latencies[p95_index]

    return {
        "total": total,
        "errors": errors,
        "avg_ms": round(avg_ms, 2),
        "min_ms": round(min_ms, 2),
        "max_ms": round(max_ms, 2),
        "p95_ms": round(p95_ms, 2),
    }


def run_load_test(base_url: str, concurrency: int = 50):
    base_url = base_url.rstrip("/")
    endpoints = ["/health", "/cache-test"]

    print(f"==================================================")
    print(f"Target Base URL: {base_url}")
    print(f"Concurrency    : {concurrency} threads")
    print(f"Endpoints      : {', '.join(endpoints)}")
    print(f"==================================================\n")

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"Running {concurrency} concurrent requests to {endpoint}...")

        results = []
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(send_request, url) for _ in range(concurrency)]
            for future in as_completed(futures):
                results.append(future.result())

        stats = calculate_stats(results)
        print(f"Summary for {endpoint}:")
        print(f"  Total requests : {stats['total']}")
        print(f"  Errors         : {stats['errors']}")
        print(f"  Average        : {stats['avg_ms']} ms")
        print(f"  Min            : {stats['min_ms']} ms")
        print(f"  Max            : {stats['max_ms']} ms")
        print(f"  p95            : {stats['p95_ms']} ms\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Send 50 concurrent requests to /health and /cache-test."
    )
    parser.add_argument(
        "base_url",
        nargs="?",
        default="http://localhost:8000",
        help="Base URL of the service (e.g., http://localhost:8000 or https://app.onrender.com)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=50,
        help="Number of concurrent requests (default: 50)",
    )
    args = parser.parse_args()

    run_load_test(args.base_url, concurrency=args.concurrency)
