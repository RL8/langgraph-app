#!/usr/bin/env python3
"""Check experiment results and troubleshoot issues."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langsmith import Client

def check_experiment_results():
    """Check recent experiment results and runs."""
    
    print("🔍 Checking experiment results...")
    print("=" * 50)
    
    # Check environment
    api_key = os.getenv("LANGSMITH_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT")
    
    print(f"API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"Project: {project or 'Not set'}")
    print()
    
    if not api_key:
        print("❌ LANGSMITH_API_KEY not found in environment")
        return
    
    try:
        client = Client()
        
        # Check recent runs
        print("📊 Recent runs:")
        runs = list(client.list_runs(project_name=project, limit=10))
        
        if not runs:
            print("   No runs found")
        else:
            for i, run in enumerate(runs[:5], 1):
                run_id = str(run.id)[:8] if run.id else "unknown"
                print(f"   {i}. {run_id}... - {run.name or 'Unnamed'} - {run.status}")
                if hasattr(run, 'metadata') and run.metadata:
                    print(f"      Metadata: {list(run.metadata.keys())}")
        
        print()
        
        # Check datasets
        print("📋 Available datasets:")
        datasets = list(client.list_datasets())
        
        for dataset in datasets:
            examples = list(client.list_examples(dataset_id=dataset.id, limit=1))
            example_count = len(list(client.list_examples(dataset_id=dataset.id)))
            print(f"   {dataset.name}: {example_count} examples")
        
        print()
        
        # Check for any errors in recent runs
        print("🚨 Recent errors:")
        error_runs = [run for run in runs if run.status == "failed"]
        
        if not error_runs:
            print("   No failed runs found")
        else:
            for run in error_runs[:3]:
                run_id = str(run.id)[:8] if run.id else "unknown"
                print(f"   {run_id}... - {run.error or 'Unknown error'}")
        
    except Exception as e:
        print(f"❌ Error accessing LangSmith: {e}")
        print(f"   Type: {type(e).__name__}")
        
        if "401" in str(e):
            print("   🔧 This suggests an authentication issue")
            print("   💡 Check your LANGSMITH_API_KEY in .env file")
        elif "404" in str(e):
            print("   🔧 This suggests a project or resource not found")
        elif "rate limit" in str(e).lower():
            print("   🔧 This suggests API rate limiting")
            print("   💡 Wait a few minutes and try again")

if __name__ == "__main__":
    check_experiment_results()
