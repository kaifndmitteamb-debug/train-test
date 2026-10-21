# FastAPI Test Project

Minimal FastAPI test app for deploying on Render free tier with Neon PostgreSQL and Upstash Redis.

## Render Start Command

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Environment Variables

Set the following environment variables in your Render service dashboard:

- `DATABASE_URL`: Connection string for Neon PostgreSQL
- `UPSTASH_REDIS_REST_URL`: Upstash Redis REST URL
- `UPSTASH_REDIS_REST_TOKEN`: Upstash Redis REST Token

## Endpoints

- `GET /health`: Returns `{"status": "ok"}`
- `GET /db-test`: Queries PostgreSQL for version using `DATABASE_URL`
- `GET /cache-test`: Sets and gets a key in Upstash Redis
- `GET /benchmark`: Measures uptime, DB connection time, DB query average time (10 runs), and Redis set/get average time (10 runs)
- `GET /stream`: Server-Sent Events stream sending current time and counter every 2 seconds (up to 15 minutes)
- `GET /seed?n=5000`: Seeds the `trains` table with `n` dummy records (default 5000, max 20000) using `execute_values`
- `GET /query-test`: Executes 3 queries on `trains` (count, select by train_no, ILIKE search) and returns latency in ms, total rows, and table size

## Load Testing

A separate tool `load_test.py` is included for concurrent load testing.

```bash
# Install load test requirements separately:
pip install -r requirements-loadtest.txt

# Run concurrent test:
python load_test.py <BASE_URL>
```

