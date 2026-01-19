"""
Test script for LLM Manager Service
Tests initialization, configuration loading, and basic completion
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.llm_manager import LLMManager, get_llm_manager


def test_initialization():
    """Test LLM Manager initialization"""
    print("=" * 60)
    print("TEST 1: LLM Manager Initialization")
    print("=" * 60)

    try:
        manager = get_llm_manager()
        print("✅ LLM Manager initialized successfully")

        # Check singleton pattern
        manager2 = get_llm_manager()
        assert manager is manager2, "❌ Singleton pattern failed"
        print("✅ Singleton pattern working")

        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration loading"""
    print("\n" + "=" * 60)
    print("TEST 2: Configuration Loading")
    print("=" * 60)

    try:
        manager = get_llm_manager()

        # Get all available tasks
        tasks = manager.get_all_tasks()
        print(f"✅ Found {len(tasks)} task types configured")
        print(f"   Sample tasks: {', '.join(list(tasks)[:5])}")

        # Get info for specific task
        tag_info = manager.get_task_info('tag_suggestion')
        if tag_info:
            print(f"✅ Tag suggestion task info:")
            print(f"   Model: {tag_info['model']}")
            print(f"   Provider: {tag_info['provider']}")
            print(f"   Temperature: {tag_info['temperature']}")
            print(f"   Max tokens: {tag_info['max_tokens']}")
        else:
            print("⚠️  Tag suggestion task not found in config")

        # Get available models
        models = manager.get_available_models()
        print(f"✅ Available model groups: {len(models)}")

        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_user_preferences():
    """Test user preference management"""
    print("\n" + "=" * 60)
    print("TEST 3: User Preferences")
    print("=" * 60)

    try:
        manager = get_llm_manager()

        # Set preference to use summarization_comprehensive for tag_suggestion task
        manager.set_user_preference('tag_suggestion', 'summarization_comprehensive', user_id='test_user')
        print("✅ Set user preference: tag_suggestion -> summarization_comprehensive")

        # Get preference
        pref = manager.get_user_preference('tag_suggestion', user_id='test_user')
        assert pref == 'summarization_comprehensive', f"❌ Expected 'summarization_comprehensive', got '{pref}'"
        print(f"✅ Retrieved preference: {pref}")

        # Get all preferences
        all_prefs = manager.get_all_user_preferences(user_id='test_user')
        print(f"✅ All user preferences: {all_prefs}")

        # Clear preference for later tests
        manager.set_user_preference('tag_suggestion', None, user_id='test_user')

        return True
    except Exception as e:
        print(f"❌ User preferences test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_completion():
    """Test LLM completion (async)"""
    print("\n" + "=" * 60)
    print("TEST 4: LLM Completion (requires API key)")
    print("=" * 60)

    # Check if API key is available
    if not os.getenv('ANTHROPIC_API_KEY') and not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Skipping completion test - no API keys found")
        print("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY to test completions")
        return True

    try:
        manager = get_llm_manager()

        # Test simple completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from LiteLLM!' in exactly 4 words."}
        ]

        print("🤖 Sending test completion request...")
        response = await manager.completion(
            task_type='tag_suggestion',  # Use tag_suggestion task (Claude Sonnet 4)
            messages=messages,
            user_id='test_user'
        )

        # Extract response
        content = response.choices[0].message.content
        print(f"✅ Completion received: {content}")
        print(f"   Model used: {response.model}")
        print(f"   Tokens: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")

        return True
    except Exception as e:
        print(f"❌ Completion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sync_completion():
    """Test synchronous LLM completion"""
    print("\n" + "=" * 60)
    print("TEST 5: Synchronous LLM Completion")
    print("=" * 60)

    # Check if API key is available
    if not os.getenv('ANTHROPIC_API_KEY') and not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Skipping sync completion test - no API keys found")
        return True

    try:
        manager = get_llm_manager()

        # Test simple completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Respond with exactly one word: 'SUCCESS'"}
        ]

        print("🤖 Sending synchronous completion request...")
        response = manager.completion_sync(
            task_type='tag_suggestion',
            messages=messages,
            user_id='test_user'
        )

        # Extract response
        content = response.choices[0].message.content
        print(f"✅ Sync completion received: {content}")
        print(f"   Model used: {response.model}")

        return True
    except Exception as e:
        print(f"❌ Sync completion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 LLM MANAGER TEST SUITE")
    print("=" * 60 + "\n")

    results = []

    # Run tests
    results.append(("Initialization", test_initialization()))
    results.append(("Configuration", test_configuration()))
    results.append(("User Preferences", test_user_preferences()))
    results.append(("Async Completion", await test_completion()))
    results.append(("Sync Completion", test_sync_completion()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")

    return passed == total


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser('~/.env'))

    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
