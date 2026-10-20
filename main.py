import os
import time
from fastapi import FastAPI
import psycopg2
from upstash_redis import Redis

START = time.time()

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-test")
def db_test():
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {"error": "DATABASE_URL environment variable is not set"}

        conn = psycopg2.connect(database_url)
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
        conn.close()
        return {"db": version}
    except Exception as e:
        return {"error": str(e)}


@app.get("/cache-test")
def cache_test():
    try:
        redis_url = os.getenv("UPSTASH_REDIS_REST_URL")
        redis_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        if not redis_url or not redis_token:
            return {
                "error": "UPSTASH_REDIS_REST_URL or UPSTASH_REDIS_REST_TOKEN environment variable is not set"
            }

        redis = Redis(url=redis_url, token=redis_token)
        redis.set("test", "hello")
        value = redis.get("test")
        return {"cache": value}
    except Exception as e:
        return {"error": str(e)}


@app.get("/benchmark")
def benchmark():
    result = {
        "uptime_sec": round(time.time() - START, 1)
    }

    # Database benchmark
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            result["db_error"] = "DATABASE_URL environment variable is not set"
        else:
            t_connect_start = time.perf_counter()
            conn = psycopg2.connect(database_url)
            t_connect_end = time.perf_counter()
            result["db_connect_ms"] = round((t_connect_end - t_connect_start) * 1000, 2)

            try:
                with conn.cursor() as cur:
                    total_query_time = 0.0
                    for _ in range(10):
                        t_q_start = time.perf_counter()
                        cur.execute("SELECT 1;")
                        cur.fetchone()
                        total_query_time += time.perf_counter() - t_q_start
                    result["db_query_avg_ms"] = round((total_query_time / 10) * 1000, 2)
            finally:
                conn.close()
    except Exception as e:
        result["db_error"] = str(e)

    # Redis benchmark
    try:
        redis_url = os.getenv("UPSTASH_REDIS_REST_URL")
        redis_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        if not redis_url or not redis_token:
            result["redis_error"] = (
                "UPSTASH_REDIS_REST_URL or UPSTASH_REDIS_REST_TOKEN environment variable is not set"
            )
        else:
            redis = Redis(url=redis_url, token=redis_token)
            total_redis_time = 0.0
            for _ in range(10):
                t_r_start = time.perf_counter()
                redis.set("bench", "1")
                redis.get("bench")
                total_redis_time += time.perf_counter() - t_r_start
            result["redis_avg_ms"] = round((total_redis_time / 10) * 1000, 2)
    except Exception as e:
        result["redis_error"] = str(e)

    return result

