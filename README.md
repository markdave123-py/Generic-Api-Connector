# Async API Connector

A fully‑featured, asynchronous Python connector that interacts with a simulated third‑party API, designed for high reliability, security, and ease of integration.

## Features
- **Async/await + httpx** for non‑blocking IO
- **OAuth2 Client Credentials** authentication
- **Pydantic** models for type safety
- **Retry with exponential backoff** (network & 5xx/429)
- **Pagination helper** + optional concurrent page fetch
- **Anomaly detection** for rate spikes & repeated 401s
- **Structured logging** with sensitive‑data redaction
- **Easy plug‑in design** – import `connector.APIClient` and go
- **Unit & integration tests** with `pytest` & `pytest‑asyncio`
- **Dockerized** development & CI pipeline (GitHub Actions)

## Quick Start
```bash
# Clone repo & enter
$ git clone https://github.com/your-org/async-api-connector.git
$ cd async-api-connector

# Run simulation + tests
$ docker-compose up --build