#!/usr/bin/env python3
"""
Comprehensive debug test for Tag Reorganizer
Tests all components with detailed debug output
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

class TagReorganizerDebugTest:
    """Debug test suite for tag reorganizer"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.debug_log = []
        self.test_results = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Add to debug log with timestamp"""
        entry = {
            "time": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.debug_log.append(entry)
        print(f"[{entry['level']}] {entry['message']}")
    
    async def test_debug_endpoints(self):
        """Test all debug endpoints"""
        self.log("Testing debug endpoints...", "INFO")
        
        async with aiohttp.ClientSession() as session:
            # Test concept stats endpoint
            try:
                async with session.get(f"{self.base_url}/api/tags/reorganize/debug/current-concepts") as resp:
                    if resp.status == 200:
                        stats = await resp.json()
                        self.log(f"✅ Concept stats loaded: {stats['total_concepts']} concepts", "SUCCESS")
                        self.log(f"   - Unorganized: {stats.get('unorganized', 0)}", "INFO")
                        self.log(f"   - Auto-generated: {stats.get('auto_generated', 0)}", "INFO")
                        self.test_results['concept_stats'] = stats
                    else:
                        self.log(f"❌ Failed to load concept stats: HTTP {resp.status}", "ERROR")
            except Exception as e:
                self.log(f"❌ Error testing concept stats: {e}", "ERROR")
            
            # Test GPT-5 config endpoint
            try:
                async with session.get(f"{self.base_url}/api/tags/reorganize/debug/test-gpt5-config") as resp:
                    if resp.status == 200:
                        config = await resp.json()
                        if config.get('llm_config', {}).get('found'):
                            self.log(f"✅ GPT-5 config found: {config['llm_config']['model']}", "SUCCESS")
                            self.log(f"   - Max tokens: {config['llm_config'].get('max_tokens', 'N/A')}", "INFO")
                            self.log(f"   - Temperature: {config['llm_config'].get('temperature', 'N/A')}", "INFO")
                        else:
                            self.log("⚠️  GPT-5 config not found, checking alternatives...", "WARNING")
                        
                        if config.get('environment', {}).get('OPENAI_API_KEY'):
                            self.log("✅ OpenAI API key configured", "SUCCESS")
                        else:
                            self.log("❌ OpenAI API key not found", "ERROR")
                        
                        self.test_results['gpt5_config'] = config
                    else:
                        self.log(f"❌ Failed to test GPT-5 config: HTTP {resp.status}", "ERROR")
            except Exception as e:
                self.log(f"❌ Error testing GPT-5 config: {e}", "ERROR")
    
    async def test_service_initialization(self):
        """Test service initialization directly"""
        self.log("Testing service initialization...", "INFO")
        
        try:
            from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer
            from app.services.concept_only_tag_service import ConceptOnlyTagService
            
            # Test GPT-5 reorganizer
            self.log("Initializing GPT-5 reorganizer...", "INFO")
            reorganizer = GPT5TagReorganizer()
            
            if reorganizer.model_config:
                self.log(f"✅ GPT-5 reorganizer initialized with model: {reorganizer.model_config.get('model')}", "SUCCESS")
            else:
                self.log("❌ GPT-5 reorganizer failed to load model config", "ERROR")
            
            # Test concept service
            self.log("Initializing concept service...", "INFO")
            concept_service = ConceptOnlyTagService()
            
            all_concepts = concept_service.get_all_concepts_with_counts()
            self.log(f"✅ Concept service loaded {len(all_concepts)} concepts", "SUCCESS")
            
            # Test with small sample
            if len(all_concepts) > 0:
                sample_tags = []
                for concept in all_concepts[:5]:
                    sample_tags.append({
                        'id': concept.get('id'),
                        'tag': concept.get('slug'),
                        'display_name': concept.get('display_name'),
                        'count': concept.get('count', 0),
                        'current_parents': concept.get('parents', [])
                    })
                
                self.log(f"Testing with {len(sample_tags)} sample tags...", "INFO")
                
                # Test reorganization with debug info
                result, debug_info = reorganizer.reorganize_tags_with_debug(sample_tags[:2])
                
                if debug_info:
                    self.log("Debug info from reorganization:", "DEBUG")
                    if 'input_stats' in debug_info:
                        self.log(f"  Input: {debug_info['input_stats']}", "DEBUG")
                    if 'output_stats' in debug_info:
                        self.log(f"  Output: {debug_info['output_stats']}", "DEBUG")
                    if 'validation' in debug_info:
                        self.log(f"  Validation: {debug_info['validation']}", "DEBUG")
                
                self.test_results['service_test'] = {
                    'success': True,
                    'sample_size': len(sample_tags),
                    'debug_info': debug_info
                }
            
        except Exception as e:
            self.log(f"❌ Service initialization error: {e}", "ERROR")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            self.test_results['service_test'] = {
                'success': False,
                'error': str(e)
            }
    
    async def test_async_reorganization_start(self):
        """Test starting an async reorganization task"""
        self.log("Testing async reorganization start...", "INFO")
        
        async with aiohttp.ClientSession() as session:
            try:
                # Start a test reorganization
                payload = {
                    "mode": "gpt5",
                    "include_all": True,
                    "batch_size": 5  # Small batch for testing
                }
                
                async with session.post(
                    f"{self.base_url}/api/tags/reorganize/start",
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        task_id = result.get('task_id')
                        self.log(f"✅ Started reorganization task: {task_id}", "SUCCESS")
                        
                        # Wait a bit and check status
                        await asyncio.sleep(2)
                        
                        async with session.get(f"{self.base_url}/api/tags/reorganize/status/{task_id}") as status_resp:
                            if status_resp.status == 200:
                                status = await status_resp.json()
                                self.log(f"Task status: {status.get('status')}", "INFO")
                                self.log(f"Progress: {status.get('progress')}%", "INFO")
                                
                                # Cancel the task to clean up
                                await session.post(f"{self.base_url}/api/tags/reorganize/cancel/{task_id}")
                                self.log("Task cancelled for cleanup", "INFO")
                                
                        self.test_results['async_test'] = {
                            'success': True,
                            'task_id': task_id
                        }
                    else:
                        self.log(f"❌ Failed to start reorganization: HTTP {resp.status}", "ERROR")
                        error_text = await resp.text()
                        self.log(f"Error: {error_text}", "ERROR")
                        
            except Exception as e:
                self.log(f"❌ Error testing async reorganization: {e}", "ERROR")
                self.test_results['async_test'] = {
                    'success': False,
                    'error': str(e)
                }
    
    def generate_report(self):
        """Generate final debug report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_results": self.test_results,
            "debug_log": self.debug_log,
            "summary": {
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results.values() if r.get('success')),
                "failed": sum(1 for r in self.test_results.values() if not r.get('success'))
            }
        }
        
        # Save report to file
        report_path = Path("data/tag_reorganizer_debug_report.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.log(f"Debug report saved to: {report_path}", "INFO")
        
        return report
    
    async def run_all_tests(self):
        """Run all debug tests"""
        print("\n" + "="*80)
        print(" TAG REORGANIZER DEBUG TEST SUITE")
        print("="*80)
        
        self.log("Starting comprehensive debug tests...", "INFO")
        
        # Run tests
        await self.test_debug_endpoints()
        await self.test_service_initialization()
        await self.test_async_reorganization_start()
        
        # Generate report
        report = self.generate_report()
        
        # Print summary
        print("\n" + "="*80)
        print(" TEST SUMMARY")
        print("="*80)
        print(f"Total tests: {report['summary']['total_tests']}")
        print(f"✅ Passed: {report['summary']['passed']}")
        print(f"❌ Failed: {report['summary']['failed']}")
        
        if report['summary']['failed'] == 0:
            print("\n🎉 ALL TESTS PASSED - Tag Reorganizer is ready!")
        else:
            print("\n⚠️  Some tests failed - check the debug report for details")
        
        print(f"\n📄 Full report saved to: data/tag_reorganizer_debug_report.json")
        print("="*80)
        
        return report['summary']['failed'] == 0

async def main():
    """Main test runner"""
    tester = TagReorganizerDebugTest()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)