"""Dataset management for LangSmith integration.

This module provides utilities for creating and managing datasets
from research agent traces for evaluation and improvement.
"""

import json
import os
from typing import Any, Dict, List, Optional
from langsmith import Client, RunEvaluator
from langchain_core.messages import BaseMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ResearchDatasetManager:
    """Manages LangSmith datasets for research agent evaluation."""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or Client()
    
    def create_research_dataset(self, name: str, description: str = "") -> str:
        """Create a new dataset for research evaluation."""
        dataset = self.client.create_dataset(
            dataset_name=name,
            description=description
        )
        return dataset.id
    
    def add_run_to_dataset(self, run_id: str, dataset_id: str) -> None:
        """Add a specific run to a dataset."""
        self.client.create_example(
            inputs={"run_id": run_id},
            outputs={"dataset_id": dataset_id},
            dataset_id=dataset_id
        )
    
    def create_research_schema(self) -> Dict[str, Any]:
        """Create a schema for research evaluation datasets."""
        return {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "extraction_schema": {"type": "object"},
                "extracted_info": {"type": "object"},
                "loop_steps": {"type": "integer"},
                "tool_usage": {"type": "array", "items": {"type": "string"}},
                "research_quality": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["topic", "extraction_schema", "extracted_info"]
        }


class ResearchEvaluator(RunEvaluator):
    """Evaluator for research agent performance."""
    
    def evaluate_run(self, run: Any, example: Any) -> Dict[str, Any]:
        """Evaluate a research run for quality and completeness."""
        # Extract run data
        run_data = run.dict() if hasattr(run, 'dict') else run
        
        # Basic evaluation metrics
        metrics = {
            "completeness": self._evaluate_completeness(run_data),
            "tool_efficiency": self._evaluate_tool_usage(run_data),
            "research_depth": self._evaluate_research_depth(run_data)
        }
        
        return {
            "key": "research_quality",
            "score": sum(metrics.values()) / len(metrics),
            "comment": f"Completeness: {metrics['completeness']:.2f}, "
                      f"Tool Efficiency: {metrics['tool_efficiency']:.2f}, "
                      f"Research Depth: {metrics['research_depth']:.2f}"
        }
    
    def _evaluate_completeness(self, run_data: Dict[str, Any]) -> float:
        """Evaluate how complete the research is."""
        # Simple heuristic: check if info was extracted
        if "outputs" in run_data and "info" in run_data["outputs"]:
            info = run_data["outputs"]["info"]
            if info and len(str(info)) > 50:
                return 1.0
        return 0.0
    
    def _evaluate_tool_usage(self, run_data: Dict[str, Any]) -> float:
        """Evaluate tool usage efficiency."""
        # Count tool calls
        tool_calls = 0
        if "events" in run_data:
            for event in run_data["events"]:
                if event.get("event_type") == "tool_start":
                    tool_calls += 1
        
        # Simple scoring: 1-2 tools = good, 3+ = diminishing returns
        if tool_calls == 0:
            return 0.0
        elif tool_calls <= 2:
            return 1.0
        else:
            return max(0.5, 1.0 - (tool_calls - 2) * 0.2)
    
    def _evaluate_research_depth(self, run_data: Dict[str, Any]) -> float:
        """Evaluate research depth based on loop steps."""
        loop_steps = run_data.get("metadata", {}).get("loop_step", 0)
        
        # Simple scoring: 1-3 steps = good, more = diminishing returns
        if loop_steps == 0:
            return 0.0
        elif loop_steps <= 3:
            return 1.0
        else:
            return max(0.3, 1.0 - (loop_steps - 3) * 0.2)


def create_mvp_dataset_from_runs(
    project_name: str = None,
    dataset_name: str = "research-evaluation",
    max_runs: int = 50
) -> str:
    # Use project name from environment or default
    if project_name is None:
        project_name = os.getenv("LANGSMITH_PROJECT", "new-agent")
    """Create an MVP dataset from recent research runs."""
    client = Client()
    
    # Get recent runs from the project
    runs = list(client.list_runs(
        project_name=project_name,
        execution_order=1,  # Only root runs
        limit=max_runs
    ))
    
    # Create dataset
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Research agent evaluation dataset"
    )
    
    # Add runs to dataset
    for run in runs:
        if run.outputs and "info" in run.outputs:
            # Only add successful runs with extracted info
            client.create_example(
                inputs={
                    "topic": run.metadata.get("topic", ""),
                    "extraction_schema": run.metadata.get("extraction_schema", "{}")
                },
                outputs={
                    "extracted_info": run.outputs["info"],
                    "loop_steps": run.metadata.get("loop_step", 0)
                },
                dataset_id=dataset.id
            )
    
    return dataset.id
