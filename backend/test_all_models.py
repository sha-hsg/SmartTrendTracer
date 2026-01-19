"""
Test all 14 user-selectable models in LiteLLM config.
Tests both with and without temperature for reasoning models.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm_manager import get_llm_manager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Test models mapping (frontend name -> backend model name)
TEST_MODELS = {
    # GPT Models
    "GPT-5": "gpt-5-2025-08-07",
    "GPT-5.1": "gpt-5.1",
    "GPT-5 Mini": "gpt-5-mini",
    "GPT-5 Nano": "gpt-5-nano",
    "GPT-4o": "gpt-4o",
    "GPT-4o Mini": "gpt-4o-mini",

    # Claude Models
    "Claude Sonnet 4.5": "claude-sonnet-4-5-20250929",
    "Claude Opus 4.1": "claude-opus-4-1-20250805",
    "Claude Haiku 4.5": "claude-haiku-4-5-20250805",
    "Claude 3.5 Sonnet": "claude-sonnet-4-20250514",

    # Gemini Models
    "Gemini 3 Pro": "gemini-3.0-pro",
    "Gemini 2.5 Pro": "gemini-2.5-pro",
    "Gemini 2.5 Flash": "gemini-2.5-flash",
    "Gemini 2.5 Flash Lite": "gemini-2.5-flash-lite",
}

# Simple test prompt
TEST_PROMPT = "What is 2+2? Answer in one word."

async def test_model(llm_manager, display_name: str, model_name: str):
    """Test a single model with and without temperature."""

    print(f"\n{'='*80}")
    print(f"Testing: {display_name}")
    print(f"Model: {model_name}")
    print(f"{'='*80}")

    messages = [
        {"role": "user", "content": TEST_PROMPT}
    ]

    # Try with temperature first
    try:
        print(f"  🔄 Attempt 1: With temperature=0.3...")
        response = await llm_manager.completion(
            task_type='tag_suggestion',  # Use existing task type
            messages=messages,
            user_id='test_user',
            model=model_name,
            temperature=0.3,
            max_tokens=50
        )

        actual_model = response.model
        answer = response.choices[0].message.content.strip()

        print(f"  ✅ SUCCESS (with temperature)")
        print(f"     Actual model: {actual_model}")
        print(f"     Response: {answer}")
        return True, actual_model, "with_temperature"

    except Exception as e:
        error_msg = str(e).lower()

        # Check if it's a temperature-related error
        if "temperature" in error_msg or "does not support" in error_msg or "reasoning" in error_msg:
            print(f"  ⚠️  Temperature not supported, trying without...")

            # Try without temperature
            try:
                response = await llm_manager.completion(
                    task_type='tag_suggestion',
                    messages=messages,
                    user_id='test_user',
                    model=model_name,
                    max_tokens=50
                )

                actual_model = response.model
                answer = response.choices[0].message.content.strip()

                print(f"  ✅ SUCCESS (reasoning model - no temperature)")
                print(f"     Actual model: {actual_model}")
                print(f"     Response: {answer}")
                return True, actual_model, "no_temperature"

            except Exception as e2:
                print(f"  ❌ FAILED (even without temperature)")
                print(f"     Error: {str(e2)[:200]}")
                return False, None, str(e2)
        else:
            print(f"  ❌ FAILED")
            print(f"     Error: {str(e)[:200]}")
            return False, None, str(e)

async def main():
    """Test all models."""

    print("\n" + "="*80)
    print("🧪 LLM MODEL AVAILABILITY TEST")
    print("="*80)
    print(f"Testing {len(TEST_MODELS)} models...")

    llm_manager = get_llm_manager()

    results = {
        "success": [],
        "reasoning_models": [],
        "failed": []
    }

    # Test each model
    for display_name, model_name in TEST_MODELS.items():
        success, actual_model, mode = await test_model(llm_manager, display_name, model_name)

        if success:
            if mode == "no_temperature":
                results["reasoning_models"].append({
                    "display_name": display_name,
                    "config_name": model_name,
                    "actual_model": actual_model
                })
            else:
                results["success"].append({
                    "display_name": display_name,
                    "config_name": model_name,
                    "actual_model": actual_model
                })
        else:
            results["failed"].append({
                "display_name": display_name,
                "config_name": model_name,
                "error": mode
            })

        # Small delay between tests to avoid rate limits
        await asyncio.sleep(2)

    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    print(f"\n✅ Standard Models Working: {len(results['success'])}/{len(TEST_MODELS)}")
    if results["success"]:
        for model in results["success"]:
            print(f"   • {model['display_name']}")
            print(f"     Config: {model['config_name']}")
            print(f"     Actual: {model['actual_model']}")

    print(f"\n🧠 Reasoning Models Working: {len(results['reasoning_models'])}/{len(TEST_MODELS)}")
    if results["reasoning_models"]:
        for model in results["reasoning_models"]:
            print(f"   • {model['display_name']} (no temperature support)")
            print(f"     Config: {model['config_name']}")
            print(f"     Actual: {model['actual_model']}")

    print(f"\n❌ Failed Models: {len(results['failed'])}/{len(TEST_MODELS)}")
    if results["failed"]:
        for model in results["failed"]:
            print(f"   • {model['display_name']}")
            print(f"     Config: {model['config_name']}")
            print(f"     Error: {model['error'][:100]}...")

    # Recommendations
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80)

    if results["failed"]:
        print("\n⚠️  Failed models may need:")
        print("   1. Different API model names (check provider documentation)")
        print("   2. API access/permissions (some models require special access)")
        print("   3. Models may not exist yet (future releases)")
        print("\n   You should update the model_mapping in concepts_suggestions_mongodb.py")
        print("   to use working model names for the failed models.")

    if results["reasoning_models"]:
        print("\n🧠 Reasoning models detected:")
        print("   These models don't support temperature parameter.")
        print("   Backend should handle these specially (remove temperature parameter).")

    total_working = len(results["success"]) + len(results["reasoning_models"])
    print(f"\n📈 Overall Success Rate: {total_working}/{len(TEST_MODELS)} ({100*total_working//len(TEST_MODELS)}%)")

    print("\n" + "="*80)
    print("✅ Test Complete!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
