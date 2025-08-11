#!/usr/bin/env python3
"""CLI script for managing LangSmith datasets and evaluations."""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent.dataset_manager import (
    ResearchDatasetManager, 
    ResearchEvaluator, 
    create_mvp_dataset_from_runs
)
from langsmith import Client


def main():
    parser = argparse.ArgumentParser(description="Manage LangSmith datasets for research agent")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create dataset command
    create_parser = subparsers.add_parser("create", help="Create a new dataset")
    create_parser.add_argument("--name", required=True, help="Dataset name")
    create_parser.add_argument("--description", default="", help="Dataset description")
    create_parser.add_argument("--from-runs", action="store_true", help="Create from existing runs")
    create_parser.add_argument("--project", default=None, help="Project name (defaults to LANGSMITH_PROJECT env var)")
    create_parser.add_argument("--max-runs", type=int, default=50, help="Maximum runs to include")
    
    # List datasets command
    list_parser = subparsers.add_parser("list", help="List all datasets")
    
    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a dataset")
    eval_parser.add_argument("--dataset-id", required=True, help="Dataset ID to evaluate")
    eval_parser.add_argument("--project", default=None, help="Project name (defaults to LANGSMITH_PROJECT env var)")
    
    # Add run to dataset command
    add_parser = subparsers.add_parser("add-run", help="Add a run to dataset")
    add_parser.add_argument("--run-id", required=True, help="Run ID to add")
    add_parser.add_argument("--dataset-id", required=True, help="Dataset ID")
    
    args = parser.parse_args()
    
    if args.command == "create":
        if args.from_runs:
            dataset_id = create_mvp_dataset_from_runs(
                project_name=args.project,
                dataset_name=args.name,
                max_runs=args.max_runs
            )
            print(f"Created dataset from runs: {dataset_id}")
        else:
            manager = ResearchDatasetManager()
            dataset_id = manager.create_research_dataset(args.name, args.description)
            print(f"Created empty dataset: {dataset_id}")
    
    elif args.command == "list":
        client = Client()
        datasets = list(client.list_datasets())
        print("Available datasets:")
        for dataset in datasets:
            print(f"  {dataset.id}: {dataset.name} - {dataset.description}")
    
    elif args.command == "evaluate":
        from langsmith.evaluation import evaluate
        
        evaluator = ResearchEvaluator()
        results = evaluate(
            dataset_id=args.dataset_id,
            evaluator=evaluator,
            project_name=args.project
        )
        print(f"Evaluation completed. Results: {results}")
    
    elif args.command == "add-run":
        manager = ResearchDatasetManager()
        manager.add_run_to_dataset(args.run_id, args.dataset_id)
        print(f"Added run {args.run_id} to dataset {args.dataset_id}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
