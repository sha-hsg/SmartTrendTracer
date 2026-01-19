# MinerU PDF Processing Service

An isolated microservice for PDF to Markdown conversion using MinerU, running on port 8003.

## Why Isolated Service?

MinerU has specific dependency requirements (especially for `timm` and other ML libraries) that can conflict with the main application. By isolating it in its own environment, we avoid dependency conflicts while still getting high-quality PDF processing.

## Setup

1. Run the setup script to create an isolated environment and install dependencies:
```bash
./setup_mineru.sh
```

2. Start the service:
```bash
./start_mineru_service.sh
```

The service will run on `http://localhost:8003`

## API Endpoints

### Health Check
```
GET /health
```
Returns the status of the MinerU service.

### Convert PDF
```
POST /convert
Content-Type: multipart/form-data

Parameters:
- file: PDF file to convert
- output_format: "markdown" (default)
- parse_tables: "true" or "false" (default: false for stability)
```

## Features

- High-quality PDF to Markdown conversion
- Table parsing (optional, disabled by default for stability)
- Formula recognition
- Layout preservation
- Isolated environment prevents dependency conflicts

## Troubleshooting

If MinerU fails with dependency errors:
1. Delete the `mineru_env` directory
2. Run `./setup_mineru.sh` again
3. The setup will install fresh dependencies

## Integration

The main PDF processor service automatically uses this MinerU service as a fallback when the Marker service fails. Priority order:
1. Marker Service (port 8002) - Best quality
2. MinerU Service (port 8003) - Second best
3. pypdfium2 - Basic fallback