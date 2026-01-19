# PDF Processing Setup for SmartTrendTracer

## Overview
SmartTrendTracer uses MinerU as the primary PDF processor for converting research papers to markdown format. This document outlines the setup, configuration, and usage.

## Current Configuration

### Primary Processor: MinerU
- **Status**: ✅ Working
- **Processing Time**: ~85-114 seconds per PDF
- **Success Rate**: 100% (tested on 3 academic papers)
- **Special Configuration**: Table detection disabled to avoid compatibility issues

### Fallback Processor: pypdfium2
- **Status**: ✅ Working
- **Processing Time**: <1 second per PDF
- **Quality**: Basic text extraction only (no formatting)

## Installation

### 1. Install MinerU
```bash
pip install mineru
```

### 2. Fix Dependencies
Due to a compatibility issue with rapid_table, you need to downgrade it:
```bash
pip install rapid_table==1.0.5 --force-reinstall
```

### 3. Verify Installation
```bash
# Test MinerU CLI
mineru --version

# Test with Python script
python test_pdf_integration.py
```

## Usage

### Command Line Processing
```bash
# Process a single PDF (table detection disabled)
mineru -p document.pdf -o output_dir -t false
```

### Python API
```python
from app.services.pdf_processor_service import PDFProcessorService

# Initialize service
service = PDFProcessorService()

# Process PDF
result = service.process_pdf("path/to/document.pdf")

if result['success']:
    markdown = result['markdown']
    print(f"Processed with: {result['method_used']}")
    print(f"Content length: {len(markdown)} characters")
```

### Batch Processing
```bash
# Use the provided script to process multiple PDFs
python extract_all_pdfs.py
```

## Output

### Markdown Files
- **Location**: `backend/pdf_outputs/`
- **Format**: Clean markdown with preserved LaTeX formulas
- **Features**:
  - Proper heading hierarchy
  - Mathematical formulas in LaTeX notation
  - References preserved
  - Clean paragraph formatting

### Extracted Images
- **Location**: `backend/pdf_outputs/{pdf_name}_images/`
- **Format**: Original image formats (PNG, JPG, etc.)

## Sample Output Structure
```
backend/pdf_outputs/
├── Paper1.md                    # Markdown content
├── Paper1_images/               # Extracted images
│   ├── image1.png
│   └── image2.jpg
├── Paper2.md
└── Paper2_images/
```

## Troubleshooting

### Issue: MinerU fails with rapid_table error
**Error**: `RapidTableInput.__init__() got an unexpected keyword argument 'model_path'`
**Solution**: 
```bash
pip install rapid_table==1.0.5 --force-reinstall
```

### Issue: MinerU timeout on complex PDFs
**Solution**: Table detection is already disabled by default in our configuration

### Issue: Marker import errors
**Status**: Marker has transformer compatibility issues, use MinerU instead

### Issue: Nougat fails with transformer errors
**Status**: Nougat has version compatibility issues with transformers v4.42+

## Performance Benchmarks

| PDF Document | Pages | MinerU Time | pypdfium2 Time | Output Size |
|-------------|-------|-------------|----------------|-------------|
| Chiang et al. 2023 | 25 | 114s | 0.1s | 80KB |
| Gu & Dao 2024 | 37 | 102s | 0.36s | 137KB |
| Schmidgall et al. 2025 | 39 | 86s | 0.24s | 144KB |

## Configuration Notes

### MinerU Settings
- **Table Detection**: Disabled (`-t false`)
- **Timeout**: 600 seconds
- **Output Format**: Markdown (.md)

### Environment Variables
No special environment variables required for MinerU.

## API Integration

The PDF processor is integrated into SmartTrendTracer's paper management system:

1. **Upload Endpoint**: `/api/papers/upload`
2. **Processing**: Automatic conversion to markdown
3. **Storage**: Papers stored in database with extracted content
4. **Search**: Content is indexed for RAG search

## Testing

### Integration Test
```bash
# Run the integration test
python test_pdf_integration.py
```

### Manual Testing
```bash
# Test all PDFs in documents folder
python test_final_processors.py
```

## Future Improvements

1. **Table Detection**: Investigate fixing rapid_table compatibility
2. **Parallel Processing**: Add support for processing multiple PDFs concurrently
3. **Progress Tracking**: Add real-time progress updates for long processing
4. **Caching**: Cache processed PDFs to avoid reprocessing

## Alternatives Evaluated

### ❌ Docling
- **Issue**: Causes segmentation faults on macOS (MPS-related)
- **Status**: Disabled

### ❌ Marker
- **Issue**: Transformer compatibility errors, timeouts on complex PDFs
- **Status**: Available as secondary option but unreliable

### ❌ Nougat
- **Issue**: Incompatible with current transformer versions
- **Status**: Not working

### ✅ pypdfium2
- **Status**: Working as fallback
- **Use Case**: Quick basic text extraction when quality isn't critical

## Maintenance

### Updating Dependencies
Be cautious when updating:
- `rapid_table`: Must stay at v1.0.5
- `transformers`: May break Marker/Nougat compatibility
- `mineru`: Check changelog for breaking changes

### Monitoring
- Check processing times regularly
- Monitor failure rates
- Review output quality periodically

---

Last Updated: January 14, 2025
Configuration Status: ✅ Working