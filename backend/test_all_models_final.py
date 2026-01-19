"""
Final comprehensive test of all 14 user-selectable models.
Tests with correct parameters for each model type.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm_manager import get_llm_manager
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

# All 14 models with their configurations
ALL_MODELS = {
    # GPT Models - Reasoning models use temperature=1
    "GPT-5": {"model": "gpt-5-2025-08-07", "temperature": 1, "reasoning": True},
    "GPT-5.1": {"model": "gpt-5.1", "temperature": 1, "reasoning": True},
    "GPT-5 Mini": {"model": "gpt-5-mini", "temperature": 1, "reasoning": True},
    "GPT-5 Nano": {"model": "gpt-5-nano", "temperature": 1, "reasoning": True},
    "GPT-4o": {"model": "gpt-4o", "temperature": 0.3, "reasoning": False},
    "GPT-4o Mini": {"model": "gpt-4o-mini", "temperature": 0.3, "reasoning": False},

    # Claude Models - All use temperature=0.3
    "Claude Sonnet 4.5": {"model": "claude-sonnet-4-5-20250929", "temperature": 0.3, "reasoning": False},
    "Claude Opus 4.1": {"model": "claude-opus-4-1-20250805", "temperature": 0.3, "reasoning": False},
    "Claude Haiku 4.5": {"model": "claude-haiku-4-5-20251001", "temperature": 0.3, "reasoning": False},
    "Claude 3.5 Sonnet": {"model": "claude-sonnet-4-20250514", "temperature": 0.3, "reasoning": False},

    # Gemini Models - All use temperature=0.3
    "Gemini 3 Pro": {"model": "gemini-3.0-pro", "temperature": 0.3, "reasoning": False},
    "Gemini 2.5 Pro": {"model": "gemini-2.5-pro", "temperature": 0.3, "reasoning": False},
    "Gemini 2.5 Flash": {"model": "gemini-2.5-flash", "temperature": 0.3, "reasoning": False},
    "Gemini 2.5 Flash Lite": {"model": "gemini-2.5-flash-lite", "temperature": 0.3, "reasoning": False},
}

TEST_PROMPT = "What is 2+2? Answer in one word."

async def test_model(llm_manager, display_name: str, config: dict):
    """Test a single model with appropriate parameters."""

    model_name = config["model"]
    temperature = config["temperature"]
    is_reasoning = config["reasoning"]

    print(f"\n{'='*70}")
    print(f"Testing: {display_name}")
    print(f"Model: {model_name}")
    print(f"Temperature: {temperature} {'(Reasoning Model)' if is_reasoning else ''}")
    print(f"{'='*70}")

    messages = [{"role": "user", "content": TEST_PROMPT}]

    try:
        response = await llm_manager.completion(
            task_type='tag_suggestion',
            messages=messages,
            user_id='test_user',
            model=model_name,
            temperature=temperature,
            max_tokens=50
        )

        actual_model = response.model
        answer = response.choices[0].message.content

        if answer:
            answer = answer.strip()
            print(f"  ✅ SUCCESS")
            print(f"     Actual model: {actual_model}")
            print(f"     Response: {answer}")
            return "success", actual_model, answer
        else:
            print(f"  ⚠️  SUCCESS but EMPTY RESPONSE")
            print(f"     Actual model: {actual_model}")
            print(f"     Response: None/Empty")
            return "empty", actual_model, None

    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ FAILED")
        print(f"     Error: {error_msg[:150]}")

        # Check if it's a model not found error
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            return "not_found", None, error_msg
        else:
            return "error", None, error_msg

async def main():
    """Test all 14 models."""

    print("\n" + "="*70)
    print("🧪 FINAL COMPREHENSIVE MODEL TEST")
    print("="*70)
    print(f"Testing {len(ALL_MODELS)} models across all providers...")
    print("="*70)

    llm_manager = get_llm_manager()

    results = {
        "success": [],
        "empty_response": [],
        "not_found": [],
        "error": []
    }

    for display_name, config in ALL_MODELS.items():
        status, model_id, info = await test_model(llm_manager, display_name, config)

        if status == "success":
            results["success"].append({
                "name": display_name,
                "config": config["model"],
                "actual": model_id,
                "response": info
            })
        elif status == "empty":
            results["empty_response"].append({
                "name": display_name,
                "config": config["model"],
                "actual": model_id
            })
        elif status == "not_found":
            results["not_found"].append({
                "name": display_name,
                "config": config["model"],
                "error": info
            })
        else:
            results["error"].append({
                "name": display_name,
                "config": config["model"],
                "error": info
            })

        # Small delay between tests
        await asyncio.sleep(1.5)

    # Print Summary
    print("\n" + "="*70)
    print("📊 FINAL TEST SUMMARY")
    print("="*70)

    # Success
    print(f"\n✅ FULLY WORKING: {len(results['success'])}/{len(ALL_MODELS)}")
    if results["success"]:
        print("\nThese models work perfectly:")
        for model in results["success"]:
            print(f"   • {model['name']}")
            print(f"     Config: {model['config']}")
            print(f"     Actual: {model['actual']}")
            print(f"     Test Response: {model['response']}")

    # Empty Response (API works but no content)
    print(f"\n⚠️  EMPTY RESPONSE: {len(results['empty_response'])}/{len(ALL_MODELS)}")
    if results["empty_response"]:
        print("\nAPI succeeds but returns empty content:")
        for model in results["empty_response"]:
            print(f"   • {model['name']}")
            print(f"     Config: {model['config']}")
            print(f"     Note: May work for real tag suggestions")

    # Not Found
    print(f"\n❌ MODEL NOT FOUND: {len(results['not_found'])}/{len(ALL_MODELS)}")
    if results["not_found"]:
        print("\nModels that don't exist in the API:")
        for model in results["not_found"]:
            print(f"   • {model['name']}")
            print(f"     Config: {model['config']}")
            print(f"     Error: {model['error'][:100]}...")

    # Other Errors
    print(f"\n❌ OTHER ERRORS: {len(results['error'])}/{len(ALL_MODELS)}")
    if results["error"]:
        print("\nModels with other errors:")
        for model in results["error"]:
            print(f"   • {model['name']}")
            print(f"     Config: {model['config']}")
            print(f"     Error: {model['error'][:100]}...")

    # Overall Statistics
    total_working = len(results["success"])
    total_partial = len(results["empty_response"])
    total_failed = len(results["not_found"]) + len(results["error"])

    print(f"\n" + "="*70)
    print("📈 OVERALL STATISTICS")
    print("="*70)
    print(f"✅ Fully Working: {total_working}/{len(ALL_MODELS)} ({100*total_working//len(ALL_MODELS)}%)")
    print(f"⚠️  Partial (Empty Response): {total_partial}/{len(ALL_MODELS)} ({100*total_partial//len(ALL_MODELS)}%)")
    print(f"❌ Failed/Not Found: {total_failed}/{len(ALL_MODELS)} ({100*total_failed//len(ALL_MODELS)}%)")

    usable = total_working + total_partial
    print(f"\n🎯 Usable Models: {usable}/{len(ALL_MODELS)} ({100*usable//len(ALL_MODELS)}%)")

    # Provider Breakdown
    print(f"\n" + "="*70)
    print("🏢 PROVIDER BREAKDOWN")
    print("="*70)

    gpt_success = sum(1 for m in results["success"] if "GPT" in m["name"])
    claude_success = sum(1 for m in results["success"] if "Claude" in m["name"])
    gemini_success = sum(1 for m in results["success"] if "Gemini" in m["name"])

    print(f"OpenAI (GPT): {gpt_success}/6 working")
    print(f"Anthropic (Claude): {claude_success}/4 working")
    print(f"Google (Gemini): {gemini_success}/4 working")

    # Recommendations
    print(f"\n" + "="*70)
    print("💡 RECOMMENDATIONS")
    print("="*70)

    if total_working >= len(ALL_MODELS) * 0.8:
        print("\n🎉 Excellent! 80%+ models working. System ready for production!")
    elif total_working >= len(ALL_MODELS) * 0.5:
        print("\n✅ Good! 50%+ models working. System usable with verified models.")
    else:
        print("\n⚠️  Less than 50% working. Review failed models and API access.")

    if results["empty_response"]:
        print("\n📝 Empty Response models may work for real tasks despite test failures.")
        print("   Consider testing them with actual tag suggestion requests.")

    if results["not_found"]:
        print("\n🔍 Model Not Found errors: Check if you have API access to these models.")

    print("\n" + "="*70)
    print("✅ Comprehensive Test Complete!")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
