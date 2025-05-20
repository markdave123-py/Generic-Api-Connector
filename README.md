# Async‑API Connector

> **Scalable, plug‑in–ready framework for consuming any number of OAuth 2, REST‑style third‑party APIs.**
> *One plumbing layer – many thin provider adapters.*

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [High‑Level Architecture](#high-level-architecture)
3. [Directory Layout](#directory-layout)
4. [Quick Start](#quick-start)

   * [Local Python](#run-locally-with-python)
   * [Docker Compose](#run-with-docker-compose)
5. [Runtime Configuration](#runtime-configuration)
6. [Connector Registry & Extensibility](#connector-registry--extensibility)
7. [Using the Connector](#using-the-connector)
8. [Logging & Redaction](#logging--redaction)
9. [Anomaly Detection](#anomaly-detection)
10. [Testing](#testing)
11. [CI / CD](#cicd)
12. [Security Notes](#security-notes)
13. [Road‑map](#road-map)

---

## Project Overview

The **Async‑API Connector** is a production‑quality asynchronous Python SDK and mock‑server that demonstrates best‑practices for **securely** consuming third‑party REST APIs that use *client‑credentials* OAuth 2.

Core abilities

| Area                    | Highlights                                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------ |
| Async I/O               | `httpx.AsyncClient` + `async/await`                                                        |
| OAuth2                  | Automatic token refresh, endpoint override support                                         |
| Retry / Back‑off        | Exponential, respects `Retry‑After`, jitter, 429 & 5xx                                     |
| Pagination              | Page, concurrent fan‑out, concurrency limit                                                |
| Structured Logging      | JSON; redact sensitive headers/keys                                                        |
| Anomaly Detection       | In‑memory sliding window; warns on spikes / token misuse                                   |
| **Extensible Adapters** | Drop‑in connector files (`connectors/`) – Google, Facebook, Twitter, … no code duplication |
| Tests                   | 100 % async pytest suite – runs in‑process, zero sockets                                   |
| Docker                  | Multi‑stage image, `docker compose` one‑liner                                              |
| CI/CD                   | Black, Flake8, mypy, pytest, Build & push → Docker Hub                                     |

---

## High‑Level Architecture

```mermaid
flowchart TD
    subgraph "Plumbing (connector/*)"
        C1["APIClient
Retry + Logging"] --> OA[OAuth2Manager]
        C1 --> AD[AnomalyDetector]
    end

    subgraph "Adapters (connectors/*)"
        G[GoogleConnector] --> C1
        F[FacebookConnector] --> C1
        S[SimConnector] --> C1
    end

    REG[Registry] -->|"sim"| S
    REG -->|"google"| G
    REG -->|"facebook"| F

    User["Your Code"] -->|"list_users()"| G
    S -->|"/items"| Mock[FastAPI Mock]
    G -->|"/admin/users"| GoogleAPI["Google API"]
```

* **Adapters** contain only endpoint paths + tiny per‑provider helpers.
* **Plumbing** (auth, retry, logging, anomaly, pagination) stays single‑sourced.
* **Registry** allows late import – you select a provider by string name.

---

## Directory Layout

```
async-api-connector/
├── connector/                  # shared plumbing
│   ├── __init__.py             # re‑exports APIClient
│   ├── auth.py                 # OAuth2Manager
│   ├── client.py               # _request + retry/back‑off
│   ├── logger.py               # redacting JSON logger
│   ├── anomaly.py              # rate‑spike detector
│   ├── models.py               # Pydantic v2 DTOs
│   ├── base.py                 # BaseConnector ABC (NEW)
│   └── registry.py             # provider lookup map
│
├── connectors/                 # provider adapters (extensible)
│   ├── __init__.py             # empty – marks package
│   ├── sim.py                  # SimConnector -> FastAPI mock
│   └── google.py               # (example) GoogleConnector
│
├── simapi/                     # FastAPI mock API (unchanged)
│   └── main.py
│
├── tests/                      # pytest suite
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml              # build meta, flake8 cfg, entry‑points
└── README.md                   # you are here
```

---

## Quick Start

### 0 · Create provider secrets (Docker way)

For each adapter you only need **two files** — saved *outside* your repo.

```bash
mkdir -p secrets                           # if not already present
# SimConnector (used by built‑in tests)
echo "testclient"  > secrets/sim_client_id
echo "testsecret"  > secrets/sim_client_secret

# Add other providers when you create their adapters
# echo "gid"  > secrets/google_client_id
# echo "gsec" > secrets/google_client_secret
```

*Never commit the `secrets/` folder; it is listed in `.gitignore`.*

### Run Locally with Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export CLIENT_ID=testclient CLIENT_SECRET=testsecret
uvicorn simapi.main:app --port 8000 &   # start mock API
pytest -q                                # 3 tests pass
```

### Run with Docker Compose

Docker mounts the files created above into each container as
`/run/secrets/<provider>_client_id` and `…_client_secret` and the connector
picks them up automatically when `SECRET_BACKEND=docker`.

```bash
# one‑liner that builds the image, starts the FastAPI mock and executes pytest
docker compose up --build
```

```bash
docker compose up --build   # builds SDK image, spins mock API, runs tests
```

### Pull the Published Image

```bash
docker pull nwaekwudavid/async-api-connector:latest
# run tests inside
docker run --rm -e CLIENT_ID=x -e CLIENT_SECRET=y nwaekwudavid/async-api-connector
```

---

## Runtime Configuration

Environment vars handled by Pydantic Settings:

| Var                          | Default                   | Notes                 |
| ---------------------------- | ------------------------- | --------------------- |
| `BASE_URL`                   | `https://api.example.com` | per‑instance override |
| `CLIENT_ID`, `CLIENT_SECRET` | —                         | required for OAuth2   |
| `TOKEN_PATH`                 | `/oauth2/token`           | provider override     |
| `MAX_RETRIES`                | `3`                       | retry attempts        |
| `BACKOFF_FACTOR`             | `1.0`                     | exponential factor    |
| `CONCURRENCY_LIMIT`          | `10`                      | parallel page fetches |
| `RATE_THRESHOLD`             | `100`                     | anomaly detector      |

---

## Connector Registry & Extensibility

**How to add a new provider with its own encrypted secrets**

| Step | Command / File                                                                            | Purpose                           |
| ---- | ----------------------------------------------------------------------------------------- | --------------------------------- |
|  1   | `echo "tid" > secrets/twitter_client_id`<br>`echo "tsec" > secrets/twitter_client_secret` | create Docker secrets for Twitter |
|  2   | `connectors/twitter.py` (see example below)                                               | implement thin adapter            |
|  3   | `connector/registry.py` → `_PLUGINS["twitter"] = "connectors.twitter.TwitterConnector"`   | register it                       |
|  4   | `docker-compose.yml` → mount the two secrets & set `PROVIDER: twitter`                    | run it (no env creds)             |

> Docker Swarm equivalent: `docker secret create twitter_client_id -` then
> `--secret twitter_client_id` on `docker service create`.

*Register a provider in one place – no edits to shared plumbing.*

```python
from connector.registry import get_connector
import asyncio, os

# For **local dev only** you may still export env‑vars (EnvProvider).
# In Docker/Swarm you DON’T set the secrets here – they are mounted at
# /run/secrets/<provider>_client_* and picked up automatically when
# SECRET_BACKEND=docker.

os.environ.setdefault("PROVIDER", "twitter")          # choose adapter
os.environ.setdefault("SECRET_BACKEND", "env")         # dev path → EnvProvider
os.environ.setdefault("CLIENT_ID", "tid")              # dev‑only dummy value
os.environ.setdefault("CLIENT_SECRET", "tsec")         # dev‑only dummy value
os.environ.setdefault("BASE_URL", "https://api.twitter.com")

Connector = get_connector("twitter")
client = Connector(concurrency_limit=5)

async def main():
    users = await client.list_users()
    print(users[0])
    await client.close()

asyncio.run(main())
```

In **Docker / Swarm** deployments you omit the `CLIENT_ID` / `CLIENT_SECRET`
exports entirely.  Credentials are supplied by the encrypted Docker Secrets
mechanism (see above), and the connector retrieves them from
`/run/secrets/twitter_client_id` and `twitter_client_secret`.

All adapters share retry, auth, anomaly detection, and logging automatically.

---

## Logging & Redaction

* JSON logging via `connector.logger`
* Headers `Authorization`, `X‑API‑Key`, and JSON keys `access_token`, `refresh_token` are replaced with `"***REDACTED***"`.

---

## Anomaly Detection

`AnomalyDetector.record_event()` is invoked after every successful request. If the rolling 60‑second window exceeds `RATE_THRESHOLD` it logs a `WARNING`. Swap implementation easily for Prometheus counters.

---

## Testing

* `tests/conftest.py` wires **any** connector to the in‑process FastAPI mock using `ASGITransport` – fast & side‑effect‑free.
* Suite covers token refresh, retry logic, pagination fan‑out.

Commands:

```bash
pytest -q                 # run all
```

---

## CI/CD

| Stage  | Tool                                                |
| ------ | --------------------------------------------------- |
| Format | **Black** (`--check`)                               |
| Lint   | **Flake8** (configured in `pyproject.toml`)         |
| Type   | **mypy** (Pydantic plugin)                          |
| Tests  | **pytest** (async)                                  |
| Build  | **docker build** → tag commit SHA                   |
| Push   | **docker/login‑action** ➜ Docker Hub (`latest`+SHA) |

Workflow injects dummy creds for tests and real Docker Hub secrets for pushes.

---

## Security Notes

* No secrets baked into image; supply at runtime or via secret manager.
* Redaction ensures bearer tokens never hit plain logs.
* Dependabot keeps third‑party libs patched; mypy enforces types.

---

## Road‑map

1. **YAML manifest per adapter** (replace ENDPOINTS dict; zero code per endpoint).
2. Registry via **entry‑points** so external packages auto‑discover.
3. Cursor & offset pagination strategies.
4. Pluggable non‑OAuth auth (API‑Key, AWS SigV4).
5. OpenTelemetry spans for tracing.

 

*Maintained by ****Your Team Name**** – issues & PRs welcome.*
