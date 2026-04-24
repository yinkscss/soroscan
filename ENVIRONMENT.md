# Environment Variables — Django Backend

> Source of truth: `soroscan/settings.py`. The **Default** column is what the code falls back to when the variable is absent. The **`.env.example` value** column is what the example file ships — use it as your starting point for local dev.

Copy the example file to get started:
```bash
cp django-backend/.env.example django-backend/.env
```

---

## Required

The app raises `ImproperlyConfigured` on startup if any of these are missing (unless running under pytest, which uses `settings_test.py` and never checks them).

| Variable | Description | Default (code) | `.env.example` value |
|---|---|---|---|
| `SECRET_KEY` | Django secret key; also used as JWT signing key | `django-insecure-change-this-in-production` | `django-insecure-change-this-in-production` |
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///db.sqlite3` | `postgresql://postgres:postgres@db:5432/soroscan` |
| `REDIS_URL` | Redis connection string — used for Celery broker, result backend, cache, and Django Channels simultaneously | `redis://localhost:6379/0` | `redis://redis:6379/0` |
| `SOROBAN_RPC_URL` | Soroban RPC endpoint | `https://soroban-testnet.stellar.org` | `https://soroban-testnet.stellar.org` |
| `STELLAR_NETWORK_PASSPHRASE` | Stellar network passphrase | `Test SDF Network ; September 2015` | `Test SDF Network ; September 2015` |
| `SOROSCAN_CONTRACT_ID` | Deployed contract address (C…) | `""` | `CCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` |

---

## Core Django

| Variable | Default (code) | `.env.example` value | Notes |
|---|---|---|---|
| `DEBUG` | `False` | `True` | `True` enables CORS allow-all and disables Silk auth. Never `True` in production. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | `localhost,127.0.0.1,0.0.0.0` | Comma-separated list |
| `FRONTEND_BASE_URL` | `http://localhost:3000` | `http://localhost:3000` | Used in cross-origin links/emails |

---

## CORS

| Variable | Default (code) | `.env.example` value | Notes |
|---|---|---|---|
| `CORS_ALLOWED_ORIGINS` | `[]` | `http://localhost:3000` | Comma-separated origins. When `DEBUG=True`, all origins are allowed regardless of this value (`CORS_ALLOW_ALL_ORIGINS = DEBUG`). Set explicitly in production. |

`CORS_ALLOW_CREDENTIALS = True` is hardcoded (required for Apollo Client).

---

## Rate Limiting

Format: `<requests>/<period>` where period is `second`, `minute`, `hour`, or `day`.

| Variable | Default (code) | `.env.example` value | Applies to |
|---|---|---|---|
| `RATE_LIMIT_ANON` | `60/minute` | `60/minute` | Unauthenticated REST requests |
| `RATE_LIMIT_USER` | `300/minute` | `300/minute` | Authenticated REST requests |
| `RATE_LIMIT_INGEST` | `10/minute` | `10/minute` | Ingestion endpoint |
| `RATE_LIMIT_GRAPHQL` | `100/minute` | `100/minute` | GraphQL endpoint |

---

## Cache / Query Performance

Not present in `.env.example` — override only when tuning performance.

| Variable | Default | Notes |
|---|---|---|
| `QUERY_CACHE_TTL_SECONDS` | `60` | TTL for cached REST/GraphQL search, stats, and timeline responses |
| `SLOW_QUERY_THRESHOLD_MS` | `100` | Queries slower than this are logged to `logs/slow_queries.log` |
| `DEDUP_LOG_RETENTION_DAYS` | `90` | Days before deduplication logs are purged |

---

## Stellar / Soroban

| Variable | Default (code) | `.env.example` value | Notes |
|---|---|---|---|
| `INDEXER_SECRET_KEY` | `""` | `SCXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` | Stellar keypair secret for the indexer account (generate with `stellar keys generate indexer`) |

(`SOROBAN_RPC_URL`, `STELLAR_NETWORK_PASSPHRASE`, `SOROSCAN_CONTRACT_ID` are listed under Required above.)

---

## Logging

| Variable | Default (code) | `.env.example` value | Notes |
|---|---|---|---|
| `LOG_FORMAT` | `""` | `""` (empty) | Set to `json` for structured JSON logs (recommended in production). Any other value uses plain text. |

Slow-query logs are always written to `logs/slow_queries.log` (rotating daily, 7-day retention), regardless of `LOG_FORMAT`.

---

## Sentry

Sentry is only initialised when `SENTRY_DSN` is non-empty. Both Django and Celery integrations are registered automatically.

| Variable | Default (code) | `.env.example` value | Notes |
|---|---|---|---|
| `SENTRY_DSN` | `""` | `""` (empty) | Leave empty to disable |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | `0.1` | Float 0–1; fraction of transactions traced |
| `SENTRY_ENVIRONMENT` | `production` | `development` | Tag shown in Sentry UI |

---

## Docker Compose Port Overrides

These are consumed by `docker-compose.yml` only, not by Django. Set in `django-backend/.env` to avoid port conflicts. Commented out in `.env.example` by default.

| Variable | Default |
|---|---|
| `POSTGRES_PORT` | `5432` |
| `REDIS_PORT` | `6379` |
| `WEB_PORT` | `8000` |

---

## Profiling (django-silk)

Not present in `.env.example`. Silk is disabled by default and adds negligible overhead when off.

| Variable | Default | Notes |
|---|---|---|
| `ENABLE_SILK` | `False` | Set to `true` to enable the Silk profiler UI at `/silk/` |
| `SILK_PROFILER_LOG_DIR` | `logs/profiler` | Directory for Silk profile dumps |

When `DEBUG=False`, Silk requires authentication and authorisation automatically.

---

## Email / Alerts

Not present in `.env.example`. Configure when event-driven email alerts are needed.

| Variable | Default | Notes |
|---|---|---|
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | Use `django.core.mail.backends.console.EmailBackend` for local dev |
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP server |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_USE_TLS` | `True` | |
| `EMAIL_HOST_USER` | `""` | SMTP username |
| `EMAIL_HOST_PASSWORD` | `""` | SMTP password |
| `DEFAULT_FROM_EMAIL` | `noreply@soroscan.io` | Sender address |
| `SLACK_ALERT_TIMEOUT_SECONDS` | `10` | HTTP timeout for outbound Slack alert requests |

---

## Event Streaming

Not present in `.env.example`. Streaming to Kafka or Google Pub/Sub is disabled by default. Only one backend is active at a time.

| Variable | Default | Notes |
|---|---|---|
| `EVENT_STREAMING_ENABLED` | `False` | Master switch |
| `EVENT_STREAMING_BACKEND` | `kafka` | `kafka` or `pubsub` |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Comma-separated list |
| `KAFKA_TOPIC_TEMPLATE` | `soroscan-events-{contract_id}` | `{contract_id}` is substituted at runtime |
| `PUBSUB_PROJECT_ID` | `""` | GCP project ID (required when backend is `pubsub`) |
| `PUBSUB_TOPIC_TEMPLATE` | `soroscan-events-{contract_id}` | `{contract_id}` is substituted at runtime |

---

## S3 / Archive Storage

Not present in `.env.example`. Used by the event archiving Celery task. Leave blank to disable archiving.

| Variable | Default | Notes |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | `""` | |
| `AWS_SECRET_ACCESS_KEY` | `""` | |
| `AWS_S3_REGION_NAME` | `us-east-1` | |
| `AWS_S3_ENDPOINT_URL` | `""` | Override for S3-compatible stores (MinIO, Localstack, etc.) |

---

## Quirks

- **`REDIS_URL` is shared across four subsystems**: Celery broker, Celery result backend, Django cache, and Django Channels. All four read the same variable.
- **`DATABASE_URL` code default is SQLite**, but `.env.example` points to Postgres. The required-var check will catch a missing value in production; locally without Docker, comment out `DATABASE_URL` in `.env` to fall back to SQLite.
- **Required vars are only enforced outside of test runs.** pytest sets `DJANGO_SETTINGS_MODULE=soroscan.settings_test` (via `pytest.ini`), which uses SQLite in-memory and never checks `REQUIRED_ENV_VARS`.
- **`CORS_ALLOW_ALL_ORIGINS` is derived from `DEBUG`**, not a separate variable. Setting `DEBUG=True` in production would silently open CORS to all origins.
- **`SECRET_KEY` doubles as the JWT signing key** (`SIMPLE_JWT["SIGNING_KEY"] = SECRET_KEY`). Rotating the secret key invalidates all issued tokens.
- **`SENTRY_ENVIRONMENT` differs between code default and `.env.example`**: code defaults to `production`, example ships `development`. Make sure to set this explicitly in each environment.
