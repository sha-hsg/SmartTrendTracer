# Marker PDF Service - Isolated Environment

## Overview
This is an isolated Marker PDF service that runs in its own environment to avoid package conflicts with SmartTrendTracer. Marker produces excellent PDF to Markdown conversion results.

## Features
- **Isolated Environment**: Runs in separate virtual environment to avoid dependency conflicts
- **High Quality**: Marker delivers brilliant PDF processing results
- **Multiple Modes**: 
  - Standard conversion
  - LLM-enhanced conversion for highest accuracy
  - Table extraction
- **REST API**: Clean HTTP interface accessible from SmartTrendTracer

## Setup Instructions

### 1. Initial Setup (One-time)
```bash
cd backend/marker_service
chmod +x setup_marker.sh start_marker_service.sh
./setup_marker.sh
```

This will:
- Create an isolated Python virtual environment
- Install marker-pdf with all dependencies
- Install FastAPI server components

### 2. Start the Service
```bash
cd backend/marker_service
./start_marker_service.sh
```

The service will run on **http://localhost:8002**

### 3. Verify Service
```bash
# Check health
curl http://localhost:8002/health

# Should return:
# {"status": "healthy", "marker": "available"}
```

## Integration with SmartTrendTracer

The PDF processor service automatically detects and uses the Marker service when available. Priority order:
1. **Marker Service** (best - isolated environment)
2. **MinerU** (reliable fallback)
3. **pypdfium2** (basic fallback)

## API Endpoints

### Convert PDF to Markdown
```bash
curl -X POST http://localhost:8002/convert \
  -F "file=@paper.pdf" \
  -F "output_format=markdown" \
  -F "force_ocr=false"
```

### Convert with LLM Enhancement
```bash
curl -X POST http://localhost:8002/convert_with_llm \
  -F "file=@paper.pdf" \
  -F "llm_service=gemini" \
  -F "gemini_api_key=YOUR_API_KEY" \
  -F "force_ocr=true"
```

### Extract Tables Only
```bash
curl -X POST http://localhost:8002/extract_tables \
  -F "file=@paper.pdf" \
  -F "use_llm=true" \
  -F "output_format=json"
```

## Configuration Options

### Force OCR
- Use `force_ocr=true` for:
  - Documents with poor text extraction
  - Inline math equations
  - Complex layouts

### LLM Services
Available LLM backends for enhanced processing:
- `gemini` - Google Gemini (requires API key)
- `ollama` - Local models
- `claude` - Anthropic Claude
- `openai` - OpenAI GPT models

### Output Formats
- `markdown` - Clean markdown with LaTeX math
- `json` - Structured JSON with bounding boxes
- `html` - HTML output
- `chunks` - Flattened chunks for RAG

## Troubleshooting

### Service Not Starting
```bash
# Check if port 8002 is in use
lsof -i :8002

# Kill existing process if needed
kill -9 <PID>
```

### Marker Not Found
```bash
# Ensure setup completed
cd marker_service
./setup_marker.sh
```

### Connection Refused
```bash
# Make sure service is running
cd marker_service
./start_marker_service.sh
```

## Performance Tips

1. **Batch Processing**: Process multiple PDFs concurrently
2. **Page Ranges**: Use `page_range` for large PDFs
3. **Caching**: Models are cached after first load
4. **LLM Mode**: Use sparingly - slower but highest quality

## Benefits Over Direct Integration

1. **No Dependency Conflicts**: Isolated from SmartTrendTracer environment
2. **Easy Updates**: Update Marker without affecting main system
3. **Scalability**: Can run on different machine if needed
4. **Stability**: Service crashes don't affect main application
5. **Flexibility**: Easy to switch between processors

## Testing

Test with sample PDFs:
```bash
# Test basic conversion
curl -X POST http://localhost:8002/convert \
  -F "file=@../documents/1601.06133v1-15yrs-of-dbpedia.pdf" \
  -F "output_format=markdown" \
  -o test_output.md

# View result
cat test_output.md
```

## Logs

Service logs are displayed in the terminal where `start_marker_service.sh` is running. 

For production, consider redirecting to a log file:
```bash
./start_marker_service.sh > marker_service.log 2>&1 &
```