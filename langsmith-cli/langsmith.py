#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
import os
import sys
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime, timedelta
import argparse

API_BASE = "https://api.smith.langchain.com"

def get_headers():
    api_key = os.environ.get("LANGSMITH_API_KEY")
    if not api_key:
        print("Error: LANGSMITH_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    return {"X-Api-Key": api_key}

def http_request(url, method="GET", data=None):
    headers = get_headers()
    if data:
        data = json.dumps(data).encode('utf-8')
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ""
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        if error_body:
            print(f"Response: {error_body}", file=sys.stderr)
        if data:
            print(f"Request payload: {data.decode('utf-8')}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        sys.exit(1)

def get_sessions():
    return http_request(f"{API_BASE}/api/v1/sessions")

def get_session(session_id):
    return http_request(f"{API_BASE}/api/v1/sessions/{session_id}")

def get_thread(thread_id, session_id):
    data = http_request(f"{API_BASE}/api/v1/runs/threads/{thread_id}?session_id={session_id}")

    # Process escaped JSON in previews.all_messages
    if "previews" in data and "all_messages" in data["previews"]:
        try:
            messages_str = data["previews"]["all_messages"]
            # Split by double newlines and parse each message
            messages = []
            for msg in messages_str.split('\n\n'):
                msg = msg.strip()
                if msg:
                    parsed_msg = json.loads(msg)
                    # Parse tool content if it's JSON
                    if parsed_msg.get("role") == "tool" and "content" in parsed_msg:
                        try:
                            parsed_msg["content"] = json.loads(parsed_msg["content"])
                        except:
                            pass
                    # Parse tool_calls arguments if it's JSON
                    if parsed_msg.get("role") == "assistant" and "tool_calls" in parsed_msg:
                        for tool_call in parsed_msg["tool_calls"]:
                            if "function" in tool_call and "arguments" in tool_call["function"]:
                                try:
                                    tool_call["function"]["arguments"] = json.loads(tool_call["function"]["arguments"])
                                except:
                                    pass
                    messages.append(parsed_msg)
            data["previews"]["all_messages"] = messages
        except Exception as e:
            pass

        # Remove redundant keys
        data["previews"].pop("first_human_last_ai", None)
        data["previews"].pop("human_ai_pairs", None)

    return data

def get_runs(session_id, since_minutes=5):
    start_time = (datetime.utcnow() - timedelta(minutes=since_minutes)).strftime("%Y-%m-%dT%H:%M:%S")
    payload = {
        "session": [session_id],
        "start_time": start_time,
        "select": ["name", "run_type", "start_time", "end_time", "status", "error", "thread_id"],
        "limit": 5
    }
    return http_request(f"{API_BASE}/api/v1/runs/query", method="POST", data=payload)

def get_last_thread(session_id):
    # Try progressively longer time windows
    for minutes in [5, 15, 30, 60]:
        start_time = (datetime.utcnow() - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S")
        payload = {
            "session": [session_id],
            "start_time": start_time,
            "select": ["name", "run_type", "start_time", "end_time", "status", "error", "thread_id"],
            "limit": 5
        }
        runs = http_request(f"{API_BASE}/api/v1/runs/query", method="POST", data=payload)

        if runs.get("runs"):
            # Get thread_id from most recent run
            for run in runs["runs"]:
                if run.get("thread_id"):
                    return get_thread(run["thread_id"], session_id)

    print("No runs with thread_id found in last 60 minutes", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="LangSmith CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("sessions", help="Get all sessions")

    session_parser = subparsers.add_parser("session", help="Get specific session")
    session_parser.add_argument("session_id")

    thread_parser = subparsers.add_parser("thread", help="Get thread")
    thread_parser.add_argument("thread_id")
    thread_parser.add_argument("--session", required=True)

    runs_parser = subparsers.add_parser("runs", help="Get runs")
    runs_parser.add_argument("--session", required=True)
    runs_parser.add_argument("--since", default="5m", help="Time window (e.g., 5m, 15m)")

    last_thread_parser = subparsers.add_parser("last-thread", help="Get last thread automatically")
    last_thread_parser.add_argument("--session", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "sessions":
        print(json.dumps(get_sessions(), indent=2))
    elif args.command == "session":
        print(json.dumps(get_session(args.session_id), indent=2))
    elif args.command == "thread":
        print(json.dumps(get_thread(args.thread_id, args.session), indent=2))
    elif args.command == "runs":
        minutes = int(args.since.rstrip("m"))
        print(json.dumps(get_runs(args.session, minutes), indent=2))
    elif args.command == "last-thread":
        print(json.dumps(get_last_thread(args.session), indent=2))

if __name__ == "__main__":
    main()
