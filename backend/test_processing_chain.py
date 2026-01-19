import sys
sys.path.append('.')

from app.services.pdf_processor_service import get_pdf_processor_service

processor = get_pdf_processor_service()
pdf_path = "/var/folders/8_/t8m7dznx1sl_svlp8m33ydw40000gn/T/arxiv_2507.18103.pdf"

# This should now use MinerU service as fallback
result = processor.process_pdf(pdf_path)

print(f"Success: {result.get('success')}")
print(f"Method used: {result.get('method_used')}")
if result.get('success'):
    print(f"Markdown length: {len(result.get('markdown', ''))}")
    print(f"First 200 chars: {result.get('markdown', '')[:200]}")
else:
    print(f"Error: {result.get('error')}")
