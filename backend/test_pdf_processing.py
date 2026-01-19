import asyncio
import sys
sys.path.append('.')

from app.services.async_pdf_processor import get_async_pdf_processor

async def test_processing():
    processor = get_async_pdf_processor()
    pdf_path = "/var/folders/8_/t8m7dznx1sl_svlp8m33ydw40000gn/T/arxiv_2507.18103.pdf"
    result = await processor.process_pdf_async(pdf_path)
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Method used: {result.get('method_used')}")
        print(f"Markdown length: {len(result.get('markdown', ''))}")
    else:
        print(f"Error: {result.get('error')}")
    return result

asyncio.run(test_processing())
