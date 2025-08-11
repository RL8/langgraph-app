#!/usr/bin/env python3
"""CLI interface for running experiments with the data enrichment agent."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent.graph import graph
from agent.dataset_manager import ResearchDatasetManager, create_mvp_dataset_from_runs

def run_single_experiment(topic: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single experiment with the agent."""
    print(f"🔬 Running experiment: {topic}")
    print("-" * 60)
    
    try:
        # Run the agent
        result = asyncio.run(graph.ainvoke({
            "topic": topic,
            "extraction_schema": schema
        }))
        
        # Display results
        if result.get("info"):
            print("✅ Experiment completed successfully!")
            print("📊 Extracted information:")
            print(json.dumps(result["info"], indent=2))
        else:
            print("❌ Experiment did not complete successfully")
            
        print(f"🔄 Loop steps: {result.get('loop_step', 0)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during experiment: {e}")
        return {"error": str(e)}

def run_music_analysis_experiments():
    """Run predefined music analysis experiments."""
    music_topics = [
        {
            "topic": "Billie Eilish's dark pop aesthetic and mental health themes",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "thematic_elements": {"type": "array", "items": {"type": "string"}},
                    "musical_style": {"type": "array", "items": {"type": "string"}},
                    "lyrical_focus": {"type": "array", "items": {"type": "string"}},
                    "production_characteristics": {"type": "string"},
                    "cultural_impact": {"type": "string"}
                }
            }
        },
        {
            "topic": "Post Malone's genre-blending and emotional authenticity",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "genre_fusion": {"type": "array", "items": {"type": "string"}},
                    "emotional_themes": {"type": "array", "items": {"type": "string"}},
                    "musical_evolution": {"type": "string"},
                    "signature_elements": {"type": "array", "items": {"type": "string"}},
                    "fan_connection": {"type": "string"}
                }
            }
        },
        {
            "topic": "Ariana Grande's vocal technique and empowerment messages",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "vocal_characteristics": {"type": "array", "items": {"type": "string"}},
                    "empowerment_themes": {"type": "array", "items": {"type": "string"}},
                    "musical_phases": {"type": "array", "items": {"type": "string"}},
                    "lyrical_evolution": {"type": "string"},
                    "artistic_growth": {"type": "string"}
                }
            }
        }
    ]
    
    print("🎵 Running music analysis experiments...")
    print("=" * 60)
    
    results = []
    for i, topic_data in enumerate(music_topics, 1):
        print(f"\n📝 Experiment {i}: {topic_data['topic']}")
        result = run_single_experiment(topic_data['topic'], topic_data['extraction_schema'])
        results.append(result)
        print("\n" + "=" * 60)
    
    print(f"\n🎉 Music analysis experiments completed! ({len(results)} experiments)")
    return results

def run_current_events_experiments():
    """Run experiments on current events to test tool usage."""
    current_events_topics = [
        {
            "topic": "Latest developments in AI regulation and policy",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "key_policies": {"type": "array", "items": {"type": "string"}},
                    "regulatory_bodies": {"type": "array", "items": {"type": "string"}},
                    "major_developments": {"type": "array", "items": {"type": "string"}},
                    "industry_impact": {"type": "string"},
                    "timeline": {"type": "string"}
                }
            }
        },
        {
            "topic": "Recent climate change initiatives and their effectiveness",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "initiatives": {"type": "array", "items": {"type": "string"}},
                    "countries_involved": {"type": "array", "items": {"type": "string"}},
                    "effectiveness_metrics": {"type": "array", "items": {"type": "string"}},
                    "challenges": {"type": "string"},
                    "future_outlook": {"type": "string"}
                }
            }
        }
    ]
    
    print("📰 Running current events experiments...")
    print("=" * 60)
    
    results = []
    for i, topic_data in enumerate(current_events_topics, 1):
        print(f"\n📝 Experiment {i}: {topic_data['topic']}")
        result = run_single_experiment(topic_data['topic'], topic_data['extraction_schema'])
        results.append(result)
        print("\n" + "=" * 60)
    
    print(f"\n🎉 Current events experiments completed! ({len(results)} experiments)")
    return results

def run_comprehensive_tool_test_experiments():
    """Run experiments designed to test all tools (search and scrape)."""
    comprehensive_topics = [
        {
            "topic": "Latest developments in AI regulation and policy in 2024",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "key_policies": {"type": "array", "items": {"type": "string"}},
                    "regulatory_bodies": {"type": "array", "items": {"type": "string"}},
                    "major_developments": {"type": "array", "items": {"type": "string"}},
                    "industry_impact": {"type": "string"},
                    "timeline": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        {
            "topic": "Analyze the content and impact of https://openai.com/blog/chatgpt",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "main_topics": {"type": "array", "items": {"type": "string"}},
                    "key_features": {"type": "array", "items": {"type": "string"}},
                    "technical_details": {"type": "string"},
                    "impact_assessment": {"type": "string"},
                    "user_benefits": {"type": "array", "items": {"type": "string"}},
                    "website_content": {"type": "string"}
                }
            }
        },
        {
            "topic": "Recent climate change initiatives and their effectiveness in 2024",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "initiatives": {"type": "array", "items": {"type": "string"}},
                    "countries_involved": {"type": "array", "items": {"type": "string"}},
                    "effectiveness_metrics": {"type": "array", "items": {"type": "string"}},
                    "challenges": {"type": "string"},
                    "future_outlook": {"type": "string"},
                    "data_sources": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        {
            "topic": "Analyze the research content at https://arxiv.org/abs/2403.03190",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "research_title": {"type": "string"},
                    "authors": {"type": "array", "items": {"type": "string"}},
                    "abstract": {"type": "string"},
                    "key_findings": {"type": "array", "items": {"type": "string"}},
                    "methodology": {"type": "string"},
                    "implications": {"type": "string"},
                    "paper_content": {"type": "string"}
                }
            }
        },
        {
            "topic": "Latest developments in quantum computing research and applications",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "research_breakthroughs": {"type": "array", "items": {"type": "string"}},
                    "companies_involved": {"type": "array", "items": {"type": "string"}},
                    "applications": {"type": "array", "items": {"type": "string"}},
                    "technical_challenges": {"type": "string"},
                    "market_outlook": {"type": "string"},
                    "recent_news": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    ]
    
    print("🔬 Running comprehensive tool test experiments...")
    print("=" * 70)
    print("📋 This batch includes:")
    print("  • Current events topics (forces search tool usage)")
    print("  • Specific URLs (forces scrape tool usage)")
    print("  • Research papers (requires both search and scrape)")
    print("  • Time-sensitive topics (requires current information)")
    print("=" * 70)
    
    results = []
    for i, topic_data in enumerate(comprehensive_topics, 1):
        print(f"\n📝 Experiment {i}: {topic_data['topic']}")
        result = run_single_experiment(topic_data['topic'], topic_data['extraction_schema'])
        results.append(result)
        print("\n" + "=" * 70)
    
    print(f"\n🎉 Comprehensive tool test experiments completed! ({len(results)} experiments)")
    return results

def run_comprehensive_music_experiments():
    """Run comprehensive music analysis experiments with diverse themes."""
    music_topics = [
        {
            "topic": "The Weeknd's dark themes and atmospheric production",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "thematic_elements": {"type": "array", "items": {"type": "string"}},
                    "production_style": {"type": "array", "items": {"type": "string"}},
                    "signature_sounds": {"type": "array", "items": {"type": "string"}},
                    "vocal_characteristics": {"type": "string"},
                    "narrative_arc": {"type": "string"},
                    "cultural_impact": {"type": "string"}
                }
            }
        },
        {
            "topic": "Drake's emotional vulnerability and relationship themes",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "emotional_themes": {"type": "array", "items": {"type": "string"}},
                    "relationship_patterns": {"type": "array", "items": {"type": "string"}},
                    "vulnerability_expression": {"type": "string"},
                    "musical_evolution": {"type": "string"},
                    "lyrical_techniques": {"type": "array", "items": {"type": "string"}},
                    "fan_connection": {"type": "string"}
                }
            }
        },
        {
            "topic": "Taylor Swift's evolution of love themes in her discography",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "eras": {"type": "array", "items": {"type": "string"}},
                    "love_themes": {"type": "array", "items": {"type": "string"}},
                    "lyrical_patterns": {"type": "array", "items": {"type": "string"}},
                    "musical_evolution": {"type": "string"},
                    "key_songs": {"type": "array", "items": {"type": "string"}},
                    "artistic_growth": {"type": "string"}
                }
            }
        },
        {
            "topic": "Kendrick Lamar's social commentary and political themes",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "social_issues": {"type": "array", "items": {"type": "string"}},
                    "political_messages": {"type": "array", "items": {"type": "string"}},
                    "narrative_techniques": {"type": "array", "items": {"type": "string"}},
                    "cultural_impact": {"type": "string"},
                    "representative_tracks": {"type": "array", "items": {"type": "string"}},
                    "artistic_philosophy": {"type": "string"}
                }
            }
        },
        {
            "topic": "Beyoncé's empowerment themes and artistic evolution",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "empowerment_messages": {"type": "array", "items": {"type": "string"}},
                    "artistic_phases": {"type": "array", "items": {"type": "string"}},
                    "musical_innovation": {"type": "array", "items": {"type": "string"}},
                    "cultural_significance": {"type": "string"},
                    "landmark_albums": {"type": "array", "items": {"type": "string"}},
                    "feminist_impact": {"type": "string"}
                }
            }
        },
        {
            "topic": "Billie Eilish's dark pop aesthetic and mental health themes",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "thematic_elements": {"type": "array", "items": {"type": "string"}},
                    "musical_style": {"type": "array", "items": {"type": "string"}},
                    "lyrical_focus": {"type": "array", "items": {"type": "string"}},
                    "production_characteristics": {"type": "string"},
                    "cultural_impact": {"type": "string"},
                    "mental_health_representation": {"type": "string"}
                }
            }
        },
        {
            "topic": "Post Malone's genre-blending and emotional authenticity",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "genre_fusion": {"type": "array", "items": {"type": "string"}},
                    "emotional_themes": {"type": "array", "items": {"type": "string"}},
                    "musical_evolution": {"type": "string"},
                    "signature_elements": {"type": "array", "items": {"type": "string"}},
                    "fan_connection": {"type": "string"},
                    "authenticity_factors": {"type": "string"}
                }
            }
        },
        {
            "topic": "Ariana Grande's vocal technique and empowerment messages",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "vocal_characteristics": {"type": "array", "items": {"type": "string"}},
                    "empowerment_themes": {"type": "array", "items": {"type": "string"}},
                    "musical_phases": {"type": "array", "items": {"type": "string"}},
                    "lyrical_evolution": {"type": "string"},
                    "artistic_growth": {"type": "string"},
                    "vocal_technique_analysis": {"type": "string"}
                }
            }
        }
    ]
    
    print("🎵 Running comprehensive music analysis experiments...")
    print("=" * 70)
    print("📋 This batch includes:")
    print("  • The Weeknd's dark atmospheric themes")
    print("  • Drake's emotional vulnerability")
    print("  • Taylor Swift's love theme evolution")
    print("  • Kendrick Lamar's social commentary")
    print("  • Beyoncé's empowerment messages")
    print("  • Billie Eilish's mental health themes")
    print("  • Post Malone's genre-blending")
    print("  • Ariana Grande's vocal technique")
    print("=" * 70)
    
    results = []
    for i, topic_data in enumerate(music_topics, 1):
        print(f"\n📝 Experiment {i}: {topic_data['topic']}")
        result = run_single_experiment(topic_data['topic'], topic_data['extraction_schema'])
        results.append(result)
        print("\n" + "=" * 70)
    
    print(f"\n🎉 Comprehensive music analysis experiments completed! ({len(results)} experiments)")
    return results

def run_custom_experiment(topic: str, schema_file: str = None):
    """Run a custom experiment with user-defined topic and schema."""
    if schema_file:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
    else:
        # Default schema
        schema = {
            "type": "object",
            "properties": {
                "key_points": {"type": "array", "items": {"type": "string"}},
                "summary": {"type": "string"},
                "analysis": {"type": "string"}
            }
        }
    
    print(f"🔬 Running custom experiment: {topic}")
    print("=" * 60)
    
    result = run_single_experiment(topic, schema)
    return result

def main():
    parser = argparse.ArgumentParser(description="CLI for running data enrichment agent experiments")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Music analysis experiments
    music_parser = subparsers.add_parser("music", help="Run music analysis experiments")
    
    # Current events experiments
    events_parser = subparsers.add_parser("events", help="Run current events experiments")
    
    # Comprehensive tool test experiments
    comprehensive_parser = subparsers.add_parser("comprehensive", help="Run comprehensive tool test experiments")
    
    # Comprehensive music analysis experiments
    comprehensive_music_parser = subparsers.add_parser("comprehensive_music", help="Run comprehensive music analysis experiments")
    
    # Custom experiment
    custom_parser = subparsers.add_parser("custom", help="Run a custom experiment")
    custom_parser.add_argument("topic", help="Research topic")
    custom_parser.add_argument("--schema", help="Path to JSON schema file")
    
    # Single experiment with topic and schema
    single_parser = subparsers.add_parser("single", help="Run a single experiment")
    single_parser.add_argument("topic", help="Research topic")
    single_parser.add_argument("--schema", help="Path to JSON schema file")
    
    # Dataset management
    dataset_parser = subparsers.add_parser("dataset", help="Manage datasets")
    dataset_subparsers = dataset_parser.add_subparsers(dest="dataset_command")
    
    create_parser = dataset_subparsers.add_parser("create", help="Create dataset from runs")
    create_parser.add_argument("--name", default="experiment-results", help="Dataset name")
    
    list_parser = dataset_subparsers.add_parser("list", help="List datasets")
    
    evaluate_parser = dataset_subparsers.add_parser("evaluate", help="Evaluate dataset")
    evaluate_parser.add_argument("--dataset-id", required=True, help="Dataset ID")
    
    args = parser.parse_args()
    
    if args.command == "music":
        run_music_analysis_experiments()
    
    elif args.command == "events":
        run_current_events_experiments()
    
    elif args.command == "comprehensive":
        run_comprehensive_tool_test_experiments()
    
    elif args.command == "comprehensive_music":
        run_comprehensive_music_experiments()
    
    elif args.command == "custom":
        run_custom_experiment(args.topic, args.schema)
    
    elif args.command == "single":
        run_custom_experiment(args.topic, args.schema)
    
    elif args.command == "dataset":
        if args.dataset_command == "create":
            dataset_id = create_mvp_dataset_from_runs(dataset_name=args.name)
            print(f"✅ Created dataset: {dataset_id}")
        
        elif args.dataset_command == "list":
            manager = ResearchDatasetManager()
            client = manager.client
            datasets = list(client.list_datasets())
            print("Available datasets:")
            for dataset in datasets:
                print(f"  {dataset.id}: {dataset.name} - {dataset.description}")
        
        elif args.dataset_command == "evaluate":
            from langsmith.evaluation import evaluate
            from agent.dataset_manager import ResearchEvaluator
            
            evaluator = ResearchEvaluator()
            results = evaluate(dataset_id=args.dataset_id, evaluator=evaluator)
            print(f"✅ Evaluation completed. Results: {results}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
