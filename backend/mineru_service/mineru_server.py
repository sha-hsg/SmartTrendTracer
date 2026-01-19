#!/usr/bin/env python3
"""
MinerU PDF Processing Service
Isolated service for PDF to Markdown conversion using MinerU
Runs on port 8003
"""

import os
import sys
import tempfile
import logging
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.services.image_manager import ImageManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure persistent output directory
MINERU_OUTPUT_BASE = Path("data/mineru_output")
MINERU_OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
logger.info(f"MinerU output directory: {MINERU_OUTPUT_BASE.absolute()}")

# Get the venv mineru binary path
SCRIPT_DIR = Path(__file__).parent
MINERU_BIN = SCRIPT_DIR / "mineru_env" / "bin" / "mineru"
logger.info(f"MinerU binary path: {MINERU_BIN}")

app = FastAPI(title="MinerU PDF Processing Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check cache
_mineru_available = None

def check_mineru() -> bool:
    """Check if MinerU is available"""
    global _mineru_available
    if _mineru_available is not None:
        return _mineru_available
    
    try:
        # Check CLI availability (that's all we really need)
        result = subprocess.run([str(MINERU_BIN), '--help'], capture_output=True, text=True)
        _mineru_available = result.returncode == 0

        if _mineru_available:
            logger.info("✅ MinerU CLI is available and ready")
        else:
            logger.error("❌ MinerU CLI not available")

        return _mineru_available

    except Exception as e:
        logger.error(f"❌ MinerU check failed: {e}")
        _mineru_available = False
        return False

def send_progress_callback(callback_url: str, progress_data: dict):
    """Send progress update to callback URL"""
    if not callback_url:
        return
    
    try:
        import requests
        response = requests.post(callback_url, json=progress_data, timeout=5.0)
        if response.status_code == 200:
            logger.info(f"Progress callback sent: {progress_data.get('message', 'N/A')}")
        else:
            logger.warning(f"Progress callback failed: {response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to send progress callback: {e}")

def cleanup_old_outputs(max_age_hours: int = 24):
    """Clean up old output directories older than max_age_hours"""
    try:
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned = 0
        for output_dir in MINERU_OUTPUT_BASE.iterdir():
            if output_dir.is_dir():
                # Check directory modification time
                if output_dir.stat().st_mtime < cutoff_time:
                    shutil.rmtree(output_dir, ignore_errors=True)
                    cleaned += 1
        if cleaned > 0:
            logger.info(f"Cleaned {cleaned} old output directories")
    except Exception as e:
        logger.error(f"Error cleaning old outputs: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    mineru_available = check_mineru()
    
    # Optional: Clean up old outputs on health check
    # cleanup_old_outputs(max_age_hours=48)
    
    return {
        "status": "healthy" if mineru_available else "degraded",
        "mineru": "available" if mineru_available else "unavailable",
        "service": "MinerU PDF Processor",
        "port": 8003
    }

@app.post("/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    output_format: str = Form("markdown"),
    parse_tables: str = Form("false"),
    paper_id: Optional[int] = Form(None),
    callback_url: Optional[str] = Form(None)
):
    """
    Convert PDF to markdown using MinerU with image extraction
    
    Args:
        file: PDF file to convert
        output_format: Output format (only markdown supported currently)
        parse_tables: Whether to parse tables (disabled by default for stability)
        paper_id: Optional paper ID for image storage
    """
    
    if not check_mineru():
        raise HTTPException(status_code=503, detail="MinerU is not available")
    
    if output_format != "markdown":
        raise HTTPException(status_code=400, detail="Only markdown output is supported")
    
    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        pdf_path = tmp_file.name
    
    try:
        # Store the original filename before it gets reassigned
        original_filename = file.filename
        logger.info(f"Processing PDF: {original_filename}")
        
        # Send initial progress
        send_progress_callback(callback_url, {
            "stage": "initializing",
            "message": "Starting PDF processing with MinerU",
            "progress": 0
        })
        
        # Create a unique output directory for this processing job
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_id = f"{timestamp}_{paper_id or 'temp'}_{Path(original_filename).stem}"
        output_dir = MINERU_OUTPUT_BASE / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Processing in directory: {output_dir}")
        
        # Send processing start
        send_progress_callback(callback_url, {
            "stage": "processing",
            "message": "MinerU is analyzing the PDF structure...",
            "progress": 10
        })
        
        # Build command
        cmd = [str(MINERU_BIN), '-p', pdf_path, '-o', str(output_dir)]

        # Add table parsing option
        if parse_tables.lower() == "false":
            cmd.extend(['-t', 'false'])
            logger.info("Table detection disabled for stability")

        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run MinerU with progress monitoring
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Monitor progress
        progress_stages = {
            "Initializing": 20,
            "Loading PDF": 30,
            "Extracting layout": 40,
            "Processing pages": 50,
            "Extracting text": 60,
            "Extracting images": 70,
            "Generating markdown": 80,
            "Finalizing": 90
        }
        
        last_progress = 10
        output_lines = []
        
        # Read output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                output_lines.append(line)
                logger.debug(f"MinerU output: {line.strip()}")
                
                # Check for progress indicators
                for stage, progress_value in progress_stages.items():
                    if stage.lower() in line.lower() and progress_value > last_progress:
                        send_progress_callback(callback_url, {
                            "stage": "processing",
                            "message": f"MinerU: {stage}...",
                            "progress": progress_value
                        })
                        last_progress = progress_value
                        break
        
        # Wait for process to complete
        process.wait()
        
        if process.returncode != 0:
            error_output = ''.join(output_lines)
            logger.error(f"MinerU failed: {error_output}")
            send_progress_callback(callback_url, {
                "stage": "failed",
                "message": "MinerU processing failed",
                "progress": 0,
                "error": error_output[:500]  # Limit error message size
            })
            raise HTTPException(
                status_code=500, 
                detail=f"MinerU processing failed: {error_output[:500]}"
            )
        
        # Add a small delay to ensure files are fully written
        import time
        time.sleep(0.5)
        
        # Debug: List all files in output directory
        logger.info(f"Listing all files in output directory: {output_dir}")
        import os
        for root, dirs, files in os.walk(str(output_dir)):
            level = root.replace(str(output_dir), '').count(os.sep)
            if level < 3:  # Limit depth for logging
                logger.info(f"{'  ' * level}{os.path.basename(root)}/")
                for file in files[:5]:  # Show first 5 files
                    logger.info(f"{'  ' * (level + 1)}{file}")
                if len(files) > 5:
                    logger.info(f"{'  ' * (level + 1)}... and {len(files) - 5} more files")
        
        # Find output files
        pdf_name = Path(original_filename).stem
        output_subdir = Path(output_dir) / pdf_name
        
        # MinerU creates output in <pdf_name>/auto/ directory
        auto_dir = output_subdir / "auto" if output_subdir.exists() else None
        
        # Look for markdown files
        md_files = []
        if auto_dir and auto_dir.exists():
            md_files = list(auto_dir.glob("*.md"))
        if not md_files and output_subdir.exists():
            md_files = list(output_subdir.glob("*.md"))
        if not md_files:
            # Try alternative locations
            md_files = list(Path(output_dir).glob("**/*.md"))
        
        if not md_files:
            logger.error("No markdown output generated")
            raise HTTPException(
                status_code=500,
                detail="MinerU did not generate any output"
            )
        
        # Read the markdown content
        markdown_content = md_files[0].read_text(encoding='utf-8')
        
        # Initialize image metadata
        image_metadata = []
        
        # Process images if paper_id is provided
        if paper_id:
            send_progress_callback(callback_url, {
                "stage": "processing",
                "message": "Processing extracted images...",
                "progress": 85
            })
            
            # Initialize image manager
            image_manager = ImageManager()
            
            # Look for extracted images
            image_files = {}
            image_dirs = []
            
            # MinerU outputs images in <pdf_name>/auto/images/
            if auto_dir and auto_dir.exists():
                auto_images = auto_dir / "images"
                if auto_images.exists():
                    image_dirs.append(auto_images)
                    logger.info(f"Found MinerU images directory: {auto_images}")
                    # List the first few images found
                    img_files = list(auto_images.glob("*.jpg")) + list(auto_images.glob("*.png"))
                    if img_files:
                        logger.info(f"  Contains {len(img_files)} image files")
                        for img in img_files[:3]:
                            logger.info(f"    - {img.name}")
                else:
                    logger.info(f"No images subdirectory in {auto_dir}, checking auto dir itself")
                    # Check if images are directly in auto directory
                    auto_images_direct = list(auto_dir.glob("*.jpg")) + list(auto_dir.glob("*.png"))
                    if auto_images_direct:
                        image_dirs.append(auto_dir)
                        logger.info(f"Found {len(auto_images_direct)} images directly in auto directory")
            
            # Also check other possible locations
            if output_subdir and output_subdir.exists():
                # Check for images subdirectory
                img_subdir = output_subdir / "images"
                if img_subdir.exists() and img_subdir not in image_dirs:
                    image_dirs.append(img_subdir)
                    logger.info(f"Found images subdirectory: {img_subdir}")
                
                # Check all subdirectories for images
                for subdir in output_subdir.rglob("*"):
                    if subdir.is_dir() and subdir.name in ["images", "imgs", "figures", "assets"]:
                        if subdir not in image_dirs:
                            image_dirs.append(subdir)
                            logger.info(f"Found additional image directory: {subdir}")
            
            # Fallback: search entire output directory for any images
            if not image_dirs:
                logger.info("No specific image directories found, searching entire output directory")
                # Look for any directory containing images
                for root, dirs, files in os.walk(output_dir):
                    root_path = Path(root)
                    img_files = [f for f in files if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                    if img_files:
                        image_dirs.append(root_path)
                        logger.info(f"Found images in: {root_path.relative_to(output_dir) if root != output_dir else '.'}")
                        logger.info(f"  Contains {len(img_files)} images, first few: {img_files[:3]}")
                
                if not image_dirs:
                    logger.warning("No images found anywhere in output directory!")
                    image_dirs.append(Path(output_dir))
            
            logger.info(f"Searching for images in {len(image_dirs)} directories:")
            for dir_path in image_dirs:
                logger.info(f"  - {dir_path}")
            
            # Collect all image files with their relative paths as used in markdown
            for img_dir in image_dirs:
                logger.info(f"Checking directory: {img_dir}")
                for pattern in ["*.png", "*.jpg", "*.jpeg"]:
                    found_files = list(img_dir.glob(pattern))
                    logger.info(f"  Found {len(found_files)} {pattern} files")
                    for img_file in found_files:
                        # Store with multiple possible keys
                        # 1. Just the filename
                        image_files[img_file.name] = str(img_file)
                        # 2. With 'images/' prefix (as MinerU often references them)
                        image_files[f"images/{img_file.name}"] = str(img_file)
                        # 3. Full relative path from output_subdir
                        if output_subdir and output_subdir.exists():
                            try:
                                rel_path = img_file.relative_to(output_subdir)
                                image_files[str(rel_path)] = str(img_file)
                            except ValueError:
                                pass  # File not under output_subdir
                        # 4. Also try relative to auto_dir
                        if auto_dir and auto_dir.exists():
                            try:
                                rel_path = img_file.relative_to(auto_dir)
                                image_files[str(rel_path)] = str(img_file)
                            except ValueError:
                                pass
            
            # Debug: Log all collected image paths
            actual_image_count = len(set(image_files.values()))  # Count unique files
            logger.info(f"Found {actual_image_count} unique images with {len(image_files)} path mappings")
            if image_files and logger.level <= logging.DEBUG:
                for key, path in list(image_files.items())[:5]:  # Show first 5
                    logger.debug(f"  Image mapping: '{key}' -> '{path}'")
            
            # Log the image files dictionary for debugging
            if image_files:
                logger.info(f"Image files dictionary has {len(image_files)} mappings:")
                for key, path in list(image_files.items())[:3]:  # Show first 3
                    logger.info(f"  '{key}' -> '{path}'")
            else:
                logger.warning("No image files found to process!")
            
            # Process markdown to update image references
            logger.info(f"Processing markdown images for paper {paper_id}...")
            markdown_content, image_metadata = image_manager.process_markdown_images(
                paper_id=paper_id,
                markdown=markdown_content,
                image_files=image_files,
                processor="mineru"
            )
            
            logger.info(f"Processed {len(image_metadata)} images for paper {paper_id}")
            if image_metadata:
                for img in image_metadata[:3]:  # Show first 3
                    logger.info(f"  Saved image: {img.get('path', 'unknown')}")
            
        # Extract metadata if available
        metadata = {
            "filename": original_filename,
            "page_count": 0,
            "processor": "mineru",
            "images_extracted": len(image_metadata) if paper_id else 0
        }
            
        # Look for metadata JSON
        json_files = list(output_subdir.glob("*.json")) if output_subdir.exists() else []
        if json_files:
            try:
                meta_data = json.loads(json_files[0].read_text())
                if 'page_count' in meta_data:
                    metadata['page_count'] = meta_data['page_count']
                if 'title' in meta_data:
                    metadata['title'] = meta_data['title']
            except:
                pass
            
        logger.info(f"Successfully processed {original_filename}")
        
        # Send completion callback
        send_progress_callback(callback_url, {
            "stage": "completed",
            "message": f"Successfully processed with MinerU ({len(image_metadata)} images extracted)",
            "progress": 100
        })
        
        return JSONResponse({
            "success": True,
            "content": markdown_content,
            "metadata": metadata,
            "message": f"Processed with MinerU" + (f" ({len(image_metadata)} images extracted)" if paper_id else "")
        })
            
    except subprocess.TimeoutExpired:
        logger.error("MinerU processing timeout")
        raise HTTPException(status_code=504, detail="Processing timeout")
        
    except Exception as e:
        logger.error(f"Error converting PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Clean up temp file
        try:
            os.unlink(pdf_path)
        except:
            pass

@app.post("/convert_advanced")
async def convert_pdf_advanced(
    file: UploadFile = File(...),
    enable_ocr: bool = Form(False),
    parse_tables: bool = Form(False),
    parse_formulas: bool = Form(True)
):
    """
    Advanced PDF conversion with more options
    
    Args:
        file: PDF file to convert
        enable_ocr: Enable OCR for scanned documents
        parse_tables: Enable table parsing (may be unstable)
        parse_formulas: Enable formula parsing
    """
    
    if not check_mineru():
        raise HTTPException(status_code=503, detail="MinerU is not available")
    
    # For now, redirect to basic convert with table option
    return await convert_pdf(
        file=file,
        output_format="markdown",
        parse_tables="true" if parse_tables else "false"
    )

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("🚀 Starting MinerU PDF Processing Service")
    logger.info("="*60)
    
    # Check MinerU availability on startup
    if check_mineru():
        logger.info("✅ MinerU is ready")
    else:
        logger.warning("⚠️  MinerU is not available - service will run in degraded mode")
    
    logger.info("📡 Service running on http://localhost:8003")
    logger.info("="*60)
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8003)