"""
Test all Claude models with correct API IDs from Anthropic API.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm_manager import get_llm_manager
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

CLAUDE_MODELS = {
    "Claude Sonnet 4.5": "claude-sonnet-4-5-20250929",
    "Claude Opus 4.1": "claude-opus-4-1-20250805",
    "Claude Haiku 4.5": "claude-haiku-4-5-20251001",
    "Claude 3.5 Sonnet": "claude-sonnet-4-20250514",
}

TEST_PROMPT = "What is 2+2? Answer in one word."

async def test_claude_model(llm_manager, display_name: str, model_name: str):
    """Test a single Claude model."""

    print(f"\n{'='*60}")
    print(f"Testing: {display_name}")
    print(f"Model: {model_name}")
    print(f"{'='*60}")

    messages = [{"role": "user", "content": TEST_PROMPT}]

    try:
        response = await llm_manager.completion(
            task_type='tag_suggestion',
            messages=messages,
            user_id='test_user',
            model=model_name,
            temperature=0.3,
            max_tokens=50
        )

        actual_model = response.model
        answer = response.choices[0].message.content.strip()

        print(f"  ✅ SUCCESS")
        print(f"     Actual model: {actual_model}")
        print(f"     Response: {answer}")
        return True, actual_model

    except Exception as e:
        print(f"  ❌ FAILED")
        print(f"     Error: {str(e)[:200]}")
        return False, str(e)

async def main():
    """Test all Claude models."""

    print("\n" + "="*60)
    print("🧪 CLAUDE MODEL TEST")
    print("="*60)
    print(f"Testing {len(CLAUDE_MODELS)} Claude models...")

    llm_manager = get_llm_manager()

    results = {"success": [], "failed": []}

    for display_name, model_name in CLAUDE_MODELS.items():
        success, info = await test_claude_model(llm_manager, display_name, model_name)

        if success:
            results["success"].append({
                "display_name": display_name,
                "config_name": model_name,
                "actual_model": info
            })
        else:
            results["failed"].append({
                "display_name": display_name,
                "config_name": model_name,
                "error": info
            })

        await asyncio.sleep(1)

    # Summary
    print("\n" + "="*60)
    print("📊 CLAUDE TEST SUMMARY")
    print("="*60)

    print(f"\n✅ Working: {len(results['success'])}/{len(CLAUDE_MODELS)}")
    if results["success"]:
        for model in results["success"]:
            print(f"   • {model['display_name']}")
            print(f"     Config: {model['config_name']}")
            print(f"     Actual: {model['actual_model']}")

    print(f"\n❌ Failed: {len(results['failed'])}/{len(CLAUDE_MODELS)}")
    if results["failed"]:
        for model in results["failed"]:
            print(f"   • {model['display_name']}")
            print(f"     Error: {model['error'][:100]}...")

    success_rate = len(results["success"]) / len(CLAUDE_MODELS) * 100
    print(f"\n📈 Success Rate: {success_rate:.0f}%")

    if success_rate == 100:
        print("\n🎉 All Claude models working!")
    else:
        print("\n⚠️  Some Claude models need attention")

    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
