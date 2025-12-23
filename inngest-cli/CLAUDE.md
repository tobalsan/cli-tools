# CLI tool to consume Inngest API

API URL: `https://localhost:8288`

## Authentication

Read the API key from current environment variable `INNGEST_SIGNING_KEY`.
Use bearer token in the Authorization header when making requests to protected resources.

Example: `Authorization: Bearer <API_KEY>`

## Endpoints

List events: `GET /v1/events`
Use the following query params:
- `name`: Filter by event name
- `received_after`: List events received after this RFC3339 timestamp

Get an event: `GET /v1/events/{internal_id}`
Get runs initialized by a given event: `GET /v1/events/{internal_id}/runs`
Get a function run: `GET /v1/runs/{run_id}`

## Expected behavior

List the recent events (in the last 5m by default). Optional parameter `--since` to specify a different time window, format `{int}m` for minutes.

```bash
inngest events --since 15m
# Filter by event name
inngest events --name agent.response.complete
```

Get details of a specific event by its internal ID.

```bash
inngest event <internal_id>
```

Get all function runs initialized by a specific event.

```bash
inngest runs --event <internal_id>
```

Get details of a specific function run by its run ID.

```bash
inngest run <run_id>
```
