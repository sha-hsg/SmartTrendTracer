#!/usr/bin/env python3
"""
Test script to verify LLM logging and provider routing
"""
import os
import sys
import logging
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the service
from app.services.llm_service import get_llm_service

def test_llm_routing():
    """Test that different models use correct providers"""
    
    service = get_llm_service()
    
    # Test 1: Check configured models
    print("\n=== Configured Models ===")
    for model_name, config in service.llm_config['models'].items():
        provider = config.get('provider', 'unknown')
        model = config.get('model', 'unknown')
        print(f"{model_name}: {provider}/{model}")
    
    # Test 2: Try to create clients for each configured model
    print("\n=== Testing Client Creation ===")
    for model_name, config in service.llm_config['models'].items():
        try:
            client = service._get_client(config)
            print(f"✓ {model_name}: Client created successfully")
        except Exception as e:
            print(f"✗ {model_name}: Failed - {e}")
    
    # Test 3: Try a simple tag suggestion (if API keys are available)
    print("\n=== Testing Tag Suggestion ===")
    test_text = "OpenAI just released GPT-5 with amazing new capabilities for reasoning and code generation."
    
    try:
        tags = service.suggest_tags(test_text, "test_user")
        print(f"Generated tags: {tags}")
    except Exception as e:
        print(f"Tag suggestion failed: {e}")
    
    print("\n=== Check logs/backend.log for detailed LLM usage logging ===")

if __name__ == "__main__":
    test_llm_routing()