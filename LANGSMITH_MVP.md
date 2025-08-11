# LangSmith MVP Integration Guide

This guide shows how to quickly get started with LangSmith dataset management for your research agent.

## Setup

1. **Install dependencies**:
   ```bash
   pip install -e .
   ```

2. **Set up LangSmith API key** in your `.env` file:
   ```bash
   LANGSMITH_API_KEY=lsv2_your_key_here
   ```

3. **Run your agent** to generate traces:
   ```bash
   langgraph dev
   ```

## Quick Start Commands

### 1. Create Dataset from Recent Runs
```bash
python scripts/manage_datasets.py create --name "my-research-dataset" --from-runs
```

### 2. List All Datasets
```bash
python scripts/manage_datasets.py list
```

### 3. Evaluate a Dataset
```bash
python scripts/manage_datasets.py evaluate --dataset-id "your_dataset_id"
```

### 4. Add Specific Run to Dataset
```bash
python scripts/manage_datasets.py add-run --run-id "your_run_id" --dataset-id "your_dataset_id"
```

## What This MVP Provides

### Enhanced Tracing
- **Metadata tracking**: Topic, extraction schema, loop steps
- **Tool usage monitoring**: Search and scrape operations
- **Research quality indicators**: Success/failure patterns

### Basic Evaluation Metrics
- **Completeness**: Did the agent extract meaningful info?
- **Tool Efficiency**: Optimal tool usage patterns
- **Research Depth**: Appropriate iteration depth

### Dataset Management
- **Automatic collection**: From successful research runs
- **Manual curation**: Add specific runs to datasets
- **Schema validation**: Structured data format

## Next Steps

1. **Run your agent** on various research topics
2. **Create your first dataset** from the generated traces
3. **Review evaluation results** in LangSmith UI
4. **Iterate** on prompts and tools based on metrics

## Viewing Results

- **Traces**: Visit [LangSmith](https://smith.langchain.com/) to see detailed traces
- **Datasets**: Navigate to Datasets & Experiments section
- **Evaluations**: Check experiment results for performance metrics

## Customization

Edit `src/agent/dataset_manager.py` to:
- Add custom evaluation metrics
- Modify dataset schemas
- Implement domain-specific evaluators
