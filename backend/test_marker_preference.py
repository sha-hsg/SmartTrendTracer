from app.services.pdf_processor_service import get_pdf_processor_service
import logging

logging.basicConfig(level=logging.INFO)

# Get the service
service = get_pdf_processor_service()

# Print service availability
print("\n📊 Service Availability:")
print(f"  Marker Service: {service.marker_service_available}")
print(f"  MinerU Service: {service.mineru_service_available}")

# Test with a PDF forcing Marker
test_pdf = "data/papers/20250815_220149_4226a804_Chiang_and_Lee_-_2023_-_Can_Large_Language_Models_Be_an_Alternative_to_Hum.pdf"

print(f"\n🔄 Processing with prefer_method='marker_service':")
result = service.process_pdf(test_pdf, prefer_method="marker_service")
print(f"  Success: {result['success']}")
print(f"  Method Used: {result.get('method_used')}")
print(f"  Content Length: {len(result.get('markdown', ''))}")
