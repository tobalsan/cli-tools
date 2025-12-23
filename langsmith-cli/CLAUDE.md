# CLI tool to consume LangSmith API

A Python CLI tool implemented as a `uv` single-file script with inline dependency declarations (per https://docs.astral.sh/uv/guides/scripts/#declaring-script-dependencies).

The script is symlinked at `~/.local/bin/langsmith` for system-wide access.

API URL: `https://api.smith.langchain.com`

## Authentication

Read the API key from current environment variable `LANGSMITH_API_KEY`.
Set the X-Api-Key header with the API key.

## Endpoints

Get sessions: `GET /api/v1/sessions`
Get a specific session: `GET /api/v1/sessions/{session_id}`
Get thread: `GET /api/v1/runs/threads/{thread_id}`

Get runs: `POST /api/v1/runs/query`

This endpoint is VERY verbose, therefore always use this payload to limit the size of the response:

```json
{
  "session": [
    "session_id"
  ],
  "start_time": "2025-10-26T19:10:00",
  "select": [
    "name",
    "run_type",
    "start_time",
    "end_time",
    "status",
    "error",
    "thread_id"
  ],
  "limit": 5
}
```

Note: time is GMT.
The goal is just to retrieve the `thread_id`, and query next the thread endpoint.

## Expected behavior

Get sessions: 

```bash
langsmith sessions
```

Get a specific session 

```bash
langsmith session <session_id>
```

Get thread:

```bash
langsmith thread <thread_id>
```

Get runs (relative time, last 5m by default):

```bash
langsmith runs --session <session_id> --since 15m
```

Automatically retrieve last thread (from last run):

```bash
langsmith last-thread
```

This command must:
- first retrieve the most recent runs (trying successively the last 5, 15, 30, and last 60 minutes, stop as soon as run data is returned), 
- extract the `thread_id` from the last run,
- retrieve the thread data using the `thread_id`.


## Thread processing 

Example of a thread response: `./get-thread-output.json`.

In the `previews.all_messages` key, there's an escaped JSON string. Convert it to a proper JSON before output.

In the `previews.human_ai_pairs` and `previews.first_human_last_ai` are XML strings. Keep them as is. 

The final output of a thread should be a structured JSON showing:
- All the messages in order, 
- the human/AI pairs,
- the first human message and the last AI message.



