#!/usr/bin/env python3
"""Verify that a formal experiment exists and report its run count."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables so LangSmith auth works
load_dotenv()

# Ensure src on path (not strictly needed here, but consistent)
sys.path.insert(0, str(Path(__file__).parent / "src"))

from langsmith import Client

# Project name printed when launching the experiment
PROJECT_NAME = "exp-1754818569"


def main() -> None:
    client = Client()

    # Confirm the project (session) exists
    project = client.read_project(project_name=PROJECT_NAME)
    print(f"📦 Project: {project.name} ({project.id})")

    # List runs under this project/session
    runs = list(client.list_runs(project_name=[PROJECT_NAME], limit=100))
    print(f"🔬 Experiment runs found: {len(runs)}")

    # Show a few for confirmation
    for run in runs[:5]:
        print(f"  - {run.name} | {run.status} | {run.start_time}")


if __name__ == "__main__":
    main()
