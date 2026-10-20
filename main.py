import os
from fastapi import FastAPI
import psycopg2
from upstash_redis import Redis

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
