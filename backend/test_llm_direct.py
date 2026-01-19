#!/usr/bin/env python3
"""
Test LLM service directly with proper logging configuration
"""
import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up the SAME logging configuration as main.py
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# File handler with rotation (same as main.py)
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'backend.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
))

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

# Now import and test the service
from app.services.llm_service import get_llm_service

def test_with_proper_logging():
    """Test LLM service with proper logging setup"""
    
    print("\n=== Testing LLM Service with Proper Logging ===\n")
    
    service = get_llm_service()
    
    # Test Anthropic (Claude) for tag suggestions
    print("Testing Anthropic (Claude) tag generation...")
    test_text = "Just announced: GPT-5 is here with unprecedented reasoning capabilities and multimodal understanding!"
    
    try:
        tags = service.suggest_tags(test_text, "test_user")
        print(f"✓ Tags generated: {tags}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\n=== Check logs/backend.log for LLM usage entries ===")

if __name__ == "__main__":
    test_with_proper_logging()