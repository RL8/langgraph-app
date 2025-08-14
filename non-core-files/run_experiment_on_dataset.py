#!/usr/bin/env python3
"""Run a formal Experiment on a LangSmith dataset so it shows under Experiments."""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Ensure src on path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from langsmith import Client
from langchain_core.runnables import RunnableLambda
from agent.graph import graph

DATASET_NAME = "new-music-analysis-2024"  # dataset name in Studio
EXPERIMENT_NAME = "new-music-analysis-2024-exp"


def build_chain():
    """Return a Runnable that maps dataset inputs to the graph's expected input."""

    def _invoke(inputs: dict):
        topic = inputs.get("topic")
        extraction_schema = inputs.get("extraction_schema")
        # Skip empty/bad examples gracefully
        if not topic or not extraction_schema or not isinstance(extraction_schema, dict):
            return {"info": None, "loop_step": 0}
        return graph.invoke({
            "messages": [],
            "topic": topic,
            "extraction_schema": extraction_schema,
        })

    return RunnableLambda(_invoke)


def main() -> None:
    client = Client()

    unique_project = f"exp-{int(time.time())}"

    run_info = client.run_on_dataset(
        dataset_name=DATASET_NAME,
        llm_or_chain_factory=build_chain,
        evaluation_name=EXPERIMENT_NAME,
        project_name=unique_project,
        concurrency_level=4,
        max_examples=5,
        description="Experiment run of graph on new-music-analysis-2024 (subset of 5 examples)",
    )

    print("✅ Experiment launched")
    print(f"  Dataset: {DATASET_NAME}")
    print(f"  Experiment name: {EXPERIMENT_NAME}")
    print(f"  Project (session): {unique_project}")
    print("  Tip: Open the dataset in Studio → Experiments tab; you should see a new experiment entry now.")


if __name__ == "__main__":
    main()
