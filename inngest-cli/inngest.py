#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "requests",
#   "click",
# ]
# ///

import os
import sys
import json
from datetime import datetime, timedelta
import click
import requests


API_BASE = "http://localhost:8288"


def get_api_key():
    key = os.environ.get("INNGEST_SIGNING_KEY")
    if not key:
        click.echo("Error: INNGEST_SIGNING_KEY environment variable not set", err=True)
        sys.exit(1)
    return key


def make_request(endpoint, params=None):
    url = f"{API_BASE}{endpoint}"
    headers = {"Authorization": f"Bearer {get_api_key()}"}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()

        # Handle if API returns JSON string instead of parsed object
        if isinstance(result, str):
            result = json.loads(result)

        return result
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
def cli():
    """Inngest CLI - Interact with Inngest API"""
    pass


@cli.command()
@click.option("--since", default="5m", help="Time window (e.g., 15m for 15 minutes)")
@click.option("--name", help="Filter by event name")
def events(since, name):
    """List recent events"""
    # Parse time window
    if since.endswith("m"):
        minutes = int(since[:-1])
        timestamp = datetime.utcnow() - timedelta(minutes=minutes)
        received_after = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        click.echo("Error: --since must be in format {int}m", err=True)
        sys.exit(1)

    params = {"received_after": received_after}
    if name:
        params["name"] = name

    data = make_request("/v1/events", params)

    if not data:
        click.echo("No events found")
        return

    # Handle if data is dict with events key or direct list
    events_list = data if isinstance(data, list) else data.get('data', data.get('events', []))

    if not events_list:
        click.echo("No events found")
        return

    for event in events_list:
        if isinstance(event, dict):
            click.echo(f"{event.get('internal_id', 'N/A')} - {event.get('name', 'N/A')} - {event.get('ts', 'N/A')}")
        else:
            click.echo(event)


@cli.command()
@click.argument("internal_id")
def event(internal_id):
    """Get details of a specific event"""
    data = make_request(f"/v1/events/{internal_id}")
    click.echo(data)


@cli.command()
@click.option("--event", "event_id", required=True, help="Event internal ID")
def runs(event_id):
    """Get all function runs initialized by a specific event"""
    data = make_request(f"/v1/events/{event_id}/runs")

    if not data:
        click.echo("No runs found")
        return

    # Handle if data is dict with runs key or direct list
    runs_list = data if isinstance(data, list) else data.get('data', data.get('runs', []))

    if not runs_list:
        click.echo("No runs found")
        return

    for run in runs_list:
        if isinstance(run, dict):
            click.echo(f"{run.get('run_id', 'N/A')} - {run.get('status', 'N/A')}")
        else:
            click.echo(run)


@cli.command()
@click.argument("run_id")
def run(run_id):
    """Get details of a specific function run"""
    data = make_request(f"/v1/runs/{run_id}")
    click.echo(data)


if __name__ == "__main__":
    cli()
