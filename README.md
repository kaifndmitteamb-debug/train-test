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
