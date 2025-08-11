import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add src to path
sys.path.insert(0, 'src')

from agent.graph import graph

def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = ['OPENAI_API_KEY', 'TAVILY_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    print("✓ Environment validation passed")
    print(f"✓ OPENAI_API_KEY: {'*' * 10}{os.getenv('OPENAI_API_KEY')[-4:] if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
    print(f"✓ TAVILY_API_KEY: {'*' * 10}{os.getenv('TAVILY_API_KEY')[-4:] if os.getenv('TAVILY_API_KEY') else 'NOT SET'}")

def validate_graph():
    """Validate that the graph is properly configured."""
    try:
        print(f"✓ Graph type: {type(graph)}")
        print(f"✓ Graph nodes: {list(graph.nodes.keys()) if hasattr(graph, 'nodes') else 'No nodes attribute'}")
        return True
    except Exception as e:
        print(f"✗ Graph validation failed: {e}")
        return False

async def test_graph():
    """Test the graph with proper error handling and validation."""
    print("=== LangGraph Testing Infrastructure ===")
    print()
    
    # Step 1: Environment validation
    try:
        validate_environment()
    except ValueError as e:
        print(f"✗ Environment setup failed: {e}")
        return False
    
    # Step 2: Graph validation
    if not validate_graph():
        return False
    
    # Step 3: Test state preparation
    state = {
        'messages': [], 
        'topic': 'Taylor Swift musical evolution', 
        'extraction_schema': {
            'type': 'object', 
            'properties': {
                'test': {'type': 'string'}
            }
        }, 
        'loop_step': 0, 
        'info': None
    }
    
    print(f"✓ Test state prepared: {list(state.keys())}")
    print()
    
    # Step 4: Graph execution test
    print("=== Testing Graph Execution ===")
    try:
        print("Executing graph.ainvoke()...")
        result = await graph.ainvoke(state)
        
        print("✓ Graph execution successful")
        print(f"✓ Result type: {type(result)}")
        print(f"✓ Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"✓ Result content: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Graph execution failed")
        print(f"✗ Error type: {type(e).__name__}")
        print(f"✗ Error message: {str(e)}")
        
        # Provide specific guidance based on error type
        if "OPENAI_API_KEY" in str(e):
            print("→ Issue: OpenAI API key not accessible")
            print("→ Check: .env file loading and environment variable access")
        elif "TAVILY_API_KEY" in str(e):
            print("→ Issue: Tavily API key not accessible")
            print("→ Check: .env file loading and environment variable access")
        elif "aget_node" in str(e):
            print("→ Issue: LangGraph API compatibility")
            print("→ Check: LangGraph version and node access methods")
        else:
            print("→ Issue: Unknown error")
            print("→ Check: Full error details above")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_graph())
    print()
    print("=== Test Summary ===")
    if success:
        print("✓ All tests passed - Graph is working correctly")
    else:
        print("✗ Tests failed - Review error details above")
        sys.exit(1)
