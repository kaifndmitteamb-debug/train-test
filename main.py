import asyncio
from datetime import datetime, timezone
import json
import os
import time
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import psycopg2
from psycopg2.extras import execute_values
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


@app.get("/stream")
async def stream():
    async def event_generator():
        counter = 0
        start_time = time.time()
        max_duration = 15 * 60  # 15 minutes (900 seconds)
        while time.time() - start_time < max_duration:
            counter += 1
            now_iso = datetime.now(timezone.utc).isoformat()
            payload = json.dumps({"server_time": now_iso, "counter": counter})
            yield f"data: {payload}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/seed")
def seed(n: int = 5000):
    try:
        if n > 20000:
            n = 20000
        elif n < 1:
            n = 1

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {"error": "DATABASE_URL environment variable is not set"}

        conn = psycopg2.connect(database_url)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS trains (
                        id SERIAL PRIMARY KEY,
                        train_no TEXT,
                        name TEXT,
                        source TEXT,
                        destination TEXT
                    );
                """)

                dummy_rows = [
                    (
                        f"TR-{i:05d}",
                        f"Express Train {i}",
                        f"Station {i % 100}",
                        f"Station {(i + 1) % 100}",
                    )
                    for i in range(1, n + 1)
                ]

                t_start = time.perf_counter()
                execute_values(
                    cur,
                    "INSERT INTO trains (train_no, name, source, destination) VALUES %s",
                    dummy_rows,
                    page_size=1000,
                )
                conn.commit()
                seed_time_ms = round((time.perf_counter() - t_start) * 1000, 2)

            return {"inserted": n, "seed_time_ms": seed_time_ms}
        finally:
            conn.close()
    except Exception as e:
        return {"error": str(e)}


@app.get("/query-test")
def query_test():
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {"error": "DATABASE_URL environment variable is not set"}

        conn = psycopg2.connect(database_url)
        try:
            with conn.cursor() as cur:
                # 1. Query: count(*)
                t0 = time.perf_counter()
                cur.execute("SELECT count(*) FROM trains;")
                total_rows = cur.fetchone()[0]
                t_count_ms = round((time.perf_counter() - t0) * 1000, 2)

                # 2. Query: select by train_no with LIMIT 1
                t1 = time.perf_counter()
                cur.execute("SELECT * FROM trains WHERE train_no = 'TR-00001' LIMIT 1;")
                cur.fetchone()
                t_select_ms = round((time.perf_counter() - t1) * 1000, 2)

                # 3. Query: search with ILIKE on name LIMIT 20
                t2 = time.perf_counter()
                cur.execute("SELECT * FROM trains WHERE name ILIKE '%Express%' LIMIT 20;")
                cur.fetchall()
                t_ilike_ms = round((time.perf_counter() - t2) * 1000, 2)

                # Table size using pg_total_relation_size
                cur.execute("SELECT pg_total_relation_size('trains');")
                table_size = cur.fetchone()[0]

            return {
                "count_query_ms": t_count_ms,
                "select_by_train_no_ms": t_select_ms,
                "ilike_search_ms": t_ilike_ms,
                "total_rows": total_rows,
                "table_size_bytes": table_size,
            }
        finally:
            conn.close()
    except Exception as e:
        return {"error": str(e)}


