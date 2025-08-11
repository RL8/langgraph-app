#!/usr/bin/env python3
"""Create synthetic music analysis examples for the dataset."""

import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent.dataset_manager import ResearchDatasetManager

def create_music_analysis_examples():
    """Create synthetic examples for music analysis research."""
    
    manager = ResearchDatasetManager()
    
    # Create dataset for music analysis
    dataset_id = manager.create_research_dataset(
        name="music-analysis-baseline",
        description="Synthetic examples for music analysis research agent"
    )
    
    # Sample music analysis topics and schemas
    examples = [
        {
            "topic": "Taylor Swift's evolution of love themes in her discography",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "eras": {"type": "array", "items": {"type": "string"}},
                    "love_themes": {"type": "array", "items": {"type": "string"}},
                    "lyrical_patterns": {"type": "array", "items": {"type": "string"}},
                    "musical_evolution": {"type": "string"},
                    "key_songs": {"type": "array", "items": {"type": "string"}}
                }
            },
            "extracted_info": {
                "eras": ["Debut", "Fearless", "Speak Now", "Red", "1989", "Reputation", "Lover", "Folklore", "Evermore", "Midnights"],
                "love_themes": ["Innocent romance", "Heartbreak", "Mature relationships", "Self-love", "Complex emotions"],
                "lyrical_patterns": ["Storytelling", "Metaphors", "Personal anecdotes", "Emotional vulnerability"],
                "musical_evolution": "From country to pop to indie folk, showing growth in both sound and lyrical depth",
                "key_songs": ["Love Story", "All Too Well", "Blank Space", "Cardigan", "Anti-Hero"]
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
                    "representative_tracks": {"type": "array", "items": {"type": "string"}}
                }
            },
            "extracted_info": {
                "social_issues": ["Racial inequality", "Police brutality", "Poverty", "Mental health", "Identity"],
                "political_messages": ["Black empowerment", "Systemic racism", "Community unity", "Personal responsibility"],
                "narrative_techniques": ["Concept albums", "Character development", "Multiple perspectives", "Biblical references"],
                "cultural_impact": "Revolutionized hip-hop storytelling and brought social issues to mainstream attention",
                "representative_tracks": ["Alright", "HUMBLE.", "DNA.", "FEAR.", "The Art of Peer Pressure"]
            }
        },
        {
            "topic": "The Weeknd's dark themes and atmospheric production",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "thematic_elements": {"type": "array", "items": {"type": "string"}},
                    "production_style": {"type": "array", "items": {"type": "string"}},
                    "vocal_characteristics": {"type": "string"},
                    "narrative_arc": {"type": "string"},
                    "signature_sounds": {"type": "array", "items": {"type": "string"}}
                }
            },
            "extracted_info": {
                "thematic_elements": ["Hedonism", "Loneliness", "Redemption", "Nightlife", "Toxic relationships"],
                "production_style": ["Dark synth-pop", "R&B", "Alternative", "Cinematic", "Atmospheric"],
                "vocal_characteristics": "Distinctive falsetto with emotional range and vulnerability",
                "narrative_arc": "From dark hedonistic lifestyle to seeking redemption and self-reflection",
                "signature_sounds": ["Synth-heavy production", "Reverb effects", "Dark melodies", "Smooth transitions"]
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
                    "landmark_albums": {"type": "array", "items": {"type": "string"}}
                }
            },
            "extracted_info": {
                "empowerment_messages": ["Female empowerment", "Black excellence", "Self-worth", "Independence", "Cultural pride"],
                "artistic_phases": ["Destiny's Child", "Solo pop", "R&B evolution", "Visual albums", "Cultural statements"],
                "musical_innovation": ["Genre blending", "Visual storytelling", "Concept albums", "Social commentary"],
                "cultural_significance": "Redefined pop music and became a symbol of Black female empowerment",
                "landmark_albums": ["Dangerously in Love", "B'Day", "4", "Beyoncé", "Lemonade", "Renaissance"]
            }
        },
        {
            "topic": "Drake's emotional vulnerability and relationship themes",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "emotional_themes": {"type": "array", "items": {"type": "string"}},
                    "relationship_patterns": {"type": "array", "items": {"type": "string"}},
                    "lyrical_style": {"type": "string"},
                    "musical_versatility": {"type": "array", "items": {"type": "string"}},
                    "defining_characteristics": {"type": "array", "items": {"type": "string"}}
                }
            },
            "extracted_info": {
                "emotional_themes": ["Heartbreak", "Success guilt", "Loneliness", "Trust issues", "Self-reflection"],
                "relationship_patterns": ["Commitment fears", "Trust issues", "Emotional distance", "Past trauma"],
                "lyrical_style": "Confessional and vulnerable, often addressing personal struggles and relationships",
                "musical_versatility": ["Hip-hop", "R&B", "Pop", "Dancehall", "Trap"],
                "defining_characteristics": ["Emotional honesty", "Melodic rap", "Relatable lyrics", "Cultural fusion"]
            }
        }
    ]
    
    # Add examples to dataset
    client = manager.client
    for i, example in enumerate(examples):
        client.create_example(
            inputs={
                "topic": example["topic"],
                "extraction_schema": example["extraction_schema"]
            },
            outputs={
                "extracted_info": example["extracted_info"],
                "loop_steps": 3,  # Simulated research depth
                "research_quality": 0.85  # High quality synthetic data
            },
            dataset_id=dataset_id
        )
        print(f"Added example {i+1}: {example['topic'][:50]}...")
    
    print(f"\n✅ Created music analysis dataset: {dataset_id}")
    print(f"📊 Added {len(examples)} synthetic examples")
    print(f"🎵 Topics covered: Taylor Swift, Kendrick Lamar, The Weeknd, Beyoncé, Drake")
    
    return dataset_id

if __name__ == "__main__":
    create_music_analysis_examples()
