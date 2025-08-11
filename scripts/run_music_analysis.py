#!/usr/bin/env python3
"""Run the research agent on music analysis topics to generate traces."""

import asyncio
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent.graph import graph

async def run_music_analysis():
    """Run the agent on music analysis topics."""
    
    # Music analysis topics with appropriate schemas
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
    
    print("🎵 Running music analysis research agent...")
    print("=" * 60)
    
    for i, topic_data in enumerate(music_topics, 1):
        print(f"\n📝 Research {i}: {topic_data['topic']}")
        print("-" * 50)
        
        try:
            # Run the agent
            result = await graph.ainvoke({
                "topic": topic_data["topic"],
                "extraction_schema": topic_data["extraction_schema"]
            })
            
            # Display results
            if result.get("info"):
                print("✅ Research completed successfully!")
                print("📊 Extracted information:")
                print(json.dumps(result["info"], indent=2))
            else:
                print("❌ Research did not complete successfully")
                
            print(f"🔄 Loop steps: {result.get('loop_step', 0)}")
            
        except Exception as e:
            print(f"❌ Error during research: {e}")
        
        print("\n" + "=" * 60)
    
    print("\n🎉 Music analysis research completed!")
    print("💡 Check LangSmith for detailed traces and performance metrics")

if __name__ == "__main__":
    asyncio.run(run_music_analysis())
