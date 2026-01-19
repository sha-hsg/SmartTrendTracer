"""
Quick test for Gemini models with correct API names.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm_manager import get_llm_manager
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

GEMINI_MODELS = {
    "Gemini 3 Pro Preview": "gemini-3.0-pro",
    "Gemini 2.5 Pro": "gemini-2.5-pro",
    "Gemini 2.5 Flash": "gemini-2.5-flash",
    "Gemini 2.5 Flash Lite": "gemini-2.5-flash-lite",
}

TEST_PROMPT = "What is 2+2? Answer in one word."

async def test_gemini_model(llm_manager, display_name: str, model_name: str):
    """Test a single Gemini model."""

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
    """Test all Gemini models."""

    print("\n" + "="*60)
    print("🧪 GEMINI MODEL TEST")
    print("="*60)
    print(f"Testing {len(GEMINI_MODELS)} Gemini models with correct API names...")

    llm_manager = get_llm_manager()

    results = {"success": [], "failed": []}

    for display_name, model_name in GEMINI_MODELS.items():
        success, info = await test_gemini_model(llm_manager, display_name, model_name)

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
    print("📊 GEMINI TEST SUMMARY")
    print("="*60)

    print(f"\n✅ Working: {len(results['success'])}/{len(GEMINI_MODELS)}")
    if results["success"]:
        for model in results["success"]:
            print(f"   • {model['display_name']}")
            print(f"     Config: {model['config_name']}")
            print(f"     Actual: {model['actual_model']}")

    print(f"\n❌ Failed: {len(results['failed'])}/{len(GEMINI_MODELS)}")
    if results["failed"]:
        for model in results["failed"]:
            print(f"   • {model['display_name']}")
            print(f"     Error: {model['error'][:100]}...")

    success_rate = len(results["success"]) / len(GEMINI_MODELS) * 100
    print(f"\n📈 Success Rate: {success_rate:.0f}%")

    if success_rate == 100:
        print("\n🎉 All Gemini models working!")
    else:
        print("\n⚠️  Some Gemini models need attention")

    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
