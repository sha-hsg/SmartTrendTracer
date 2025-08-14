#!/usr/bin/env python3
"""Test Claude 4 models through our LLM service"""

from app.services.llm_service import LLMService
import json

# Initialize the service
llm_service = LLMService()

# Load the config to see what model we're using
with open('llm.json', 'r') as f:
    config = json.load(f)
    
print("Current configuration:")
print(f"Tag suggestion model: {config['models']['tag_suggestion']['model']}")
print(f"Provider: {config['models']['tag_suggestion']['provider']}")
print()

# Test tag suggestion
test_tweet = """
GPT-5 rollout shows impressive multimodal capabilities with real-time 
video understanding and complex reasoning chains. The new architecture 
demonstrates 10x improvement in efficiency compared to GPT-4.
"""

print("Testing tag suggestion with Claude 4...")
try:
    tags = llm_service.suggest_tags(test_tweet, "testuser")
    # Remove the API success marker if present
    if "__api_success__" in tags:
        tags.remove("__api_success__")
    print(f"✓ Success! Generated tags: {tags}")
    print(f"Model used: {llm_service.get_model_used('tag_suggestion')}")
except Exception as e:
    print(f"✗ Error: {e}")