#!/usr/bin/env python3
"""
Test MinerU and Nougat processors specifically
"""

import os
import time
import subprocess
from pathlib import Path
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_mineru(pdf_path):
    """Test MinerU directly"""
    logger.info("\n" + "="*60)
    logger.info("⛏️  Testing MinerU")
    logger.info("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run MinerU CLI
        cmd = ['mineru', '-p', str(pdf_path), '-o', tmpdir]
        logger.info(f"Command: {' '.join(cmd)}")
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            processing_time = time.time() - start_time
            
            if result.returncode == 0:
                # Look for output files
                pdf_name = Path(pdf_path).stem
                output_dir = Path(tmpdir) / pdf_name
                
                md_files = list(output_dir.glob("*.md")) if output_dir.exists() else []
                if not md_files:
                    md_files = list(Path(tmpdir).glob("**/*.md"))
                
                if md_files:
                    content = md_files[0].read_text(encoding='utf-8')
                    logger.info(f"✅ SUCCESS!")
                    logger.info(f"   Time: {processing_time:.2f} seconds")
                    logger.info(f"   Output file: {md_files[0].name}")
                    logger.info(f"   Content length: {len(content)} characters")
                    logger.info(f"   Sample: {content[:200]}...")
                    return True
                else:
                    logger.error(f"❌ No markdown file generated")
                    logger.error(f"   Output directory contents: {list(Path(tmpdir).rglob('*'))}")
                    return False
            else:
                logger.error(f"❌ MinerU failed with exit code {result.returncode}")
                logger.error(f"   STDERR: {result.stderr[:500]}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ MinerU timed out after 300 seconds")
            return False
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False

def test_nougat(pdf_path):
    """Test Nougat directly"""
    logger.info("\n" + "="*60)
    logger.info("🍫 Testing Nougat")
    logger.info("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run Nougat CLI
        cmd = ['nougat', str(pdf_path), '-o', tmpdir]
        logger.info(f"Command: {' '.join(cmd)}")
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            processing_time = time.time() - start_time
            
            if result.returncode == 0:
                # Look for output files
                output_files = list(Path(tmpdir).glob("*.mmd"))  # Nougat uses .mmd
                if not output_files:
                    output_files = list(Path(tmpdir).glob("*.md"))
                
                if output_files:
                    content = output_files[0].read_text(encoding='utf-8')
                    logger.info(f"✅ SUCCESS!")
                    logger.info(f"   Time: {processing_time:.2f} seconds")
                    logger.info(f"   Output file: {output_files[0].name}")
                    logger.info(f"   Content length: {len(content)} characters")
                    logger.info(f"   Sample: {content[:200]}...")
                    return True
                else:
                    logger.error(f"❌ No markdown file generated")
                    return False
            else:
                logger.error(f"❌ Nougat failed with exit code {result.returncode}")
                logger.error(f"   STDERR: {result.stderr[:500]}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Nougat timed out after 300 seconds")
            return False
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False

def main():
    """Test all PDFs with MinerU and Nougat"""
    pdf_dir = Path("documents")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error("No PDF files found in documents folder")
        return
    
    logger.info("="*60)
    logger.info("🔬 TESTING MINERU AND NOUGAT")
    logger.info("="*60)
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Track results
    mineru_success = 0
    nougat_success = 0
    
    for pdf_path in pdf_files:
        logger.info("\n" + "="*60)
        logger.info(f"📄 Processing: {pdf_path.name[:50]}...")
        logger.info("="*60)
        
        # Test MinerU
        if test_mineru(pdf_path):
            mineru_success += 1
        
        # Test Nougat
        if test_nougat(pdf_path):
            nougat_success += 1
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 SUMMARY")
    logger.info("="*60)
    logger.info(f"MinerU: {mineru_success}/{len(pdf_files)} successful")
    logger.info(f"Nougat: {nougat_success}/{len(pdf_files)} successful")
    
    if mineru_success < len(pdf_files):
        logger.info("\n⚠️  MinerU issues detected. Check if all dependencies are installed.")
    if nougat_success < len(pdf_files):
        logger.info("\n⚠️  Nougat issues detected. May need transformers version adjustment.")

if __name__ == "__main__":
    main()