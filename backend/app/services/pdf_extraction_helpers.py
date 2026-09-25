from app.services import pdf_service_client
import logging
import os
import re
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


def text_to_markdown(text: str) -> str:
    lines = text.split('\n')
    markdown_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            markdown_lines.append('')
            continue
        if line.isupper() and len(line) < 100:
            markdown_lines.append(f"## {line.title()}")
        elif line[:2] in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.']:
            markdown_lines.append(f"### {line}")
        else:
            markdown_lines.append(line)
    return '\n'.join(markdown_lines)


def process_with_mineru_service(
    pdf_path: str,
    mineru_service_url: str,
    paper_id: Optional[int] = None,
    mongo_paper_id: Optional[str] = None,
) -> Tuple[str, Dict]:
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            data = {
                'parse_tables': 'false',
                'output_format': 'markdown'
            }
            if paper_id:
                data['paper_id'] = paper_id
                callback_id = mongo_paper_id if mongo_paper_id else str(paper_id)
                data['callback_url'] = pdf_service_client.progress_callback_url(callback_id)

            logger.info(f"🌐 Calling MinerU Service at {mineru_service_url}")
            response = requests.post(
                f"{mineru_service_url}/convert",
                files=files,
                data=data,
                timeout=18000  # 5 hours - MinerU can take hours for complex PDFs
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('content'):
                    logger.info("✅ MinerU Service processed successfully")
                    metadata = result.get('metadata', {}) or {}
                    metadata['processor'] = 'mineru_service'
                    metadata['images_extracted'] = result.get('metadata', {}).get('images_extracted', 0)
                    if paper_id and metadata.get('images_extracted', 0) > 0:
                        logger.info(f"📸 Extracted {metadata['images_extracted']} images for paper {paper_id}")
                    return result['content'], metadata
                else:
                    logger.warning(f"❌ MinerU Service failed: {result.get('detail', 'Unknown error')}")
            else:
                logger.warning(f"❌ MinerU Service HTTP error: {response.status_code}")

        return "", {}

    except requests.exceptions.Timeout:
        logger.error("⏱️ MinerU Service timeout after 180 seconds")
        return "", {}
    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 Cannot connect to MinerU Service at {mineru_service_url}")
        logger.info("   Hint: Start the service with: cd mineru_service && ./start_mineru_service.sh")
        return "", {}
    except Exception as e:
        logger.error(f"❌ MinerU Service error: {e}")
        return "", {}


def process_with_marker_cli(pdf_path: str) -> Tuple[str, Dict]:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "input")
            os.makedirs(input_dir)

            pdf_name = os.path.basename(pdf_path)
            input_pdf = os.path.join(input_dir, pdf_name)
            shutil.copy2(pdf_path, input_pdf)

            cmd = ['marker', input_dir, '--skip_existing']
            logger.info(f"Running Marker CLI: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                logger.error(f"Marker CLI failed: {result.stderr}")
                return "", {}

            md_path = os.path.join(input_dir, "markdown", pdf_name.replace('.pdf', '.md'))
            if not os.path.exists(md_path):
                md_files = []
                for root, dirs, files in os.walk(tmpdir):
                    for file in files:
                        if file.endswith('.md'):
                            md_files.append(os.path.join(root, file))
                if md_files:
                    md_path = md_files[0]
                    logger.info(f"Found markdown at: {md_path}")
                else:
                    logger.error("Marker CLI: No markdown output file found")
                    return "", {}

            with open(md_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            metadata = {
                "page_count": 0,
                "title": Path(pdf_path).stem.replace('_', ' '),
                "authors": []
            }

            meta_path = md_path.replace('.md', '_meta.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    try:
                        meta_data = json.load(f)
                        if 'page_count' in meta_data:
                            metadata['page_count'] = meta_data['page_count']
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse metadata JSON {meta_path}: {e}")

            return markdown_content, metadata

    except Exception as e:
        logger.error(f"Marker CLI processing failed: {e}")
        return "", {}


def process_with_fallback(pdf_path: str) -> Tuple[str, Dict]:
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(pdf_path)
        text_content = ""
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            textpage = page.get_textpage()
            text_content += textpage.get_text_range() + "\n\n"
            textpage.close()
            page.close()
        metadata = {
            "page_count": len(pdf),
            "title": Path(pdf_path).stem.replace('_', ' '),
            "authors": []
        }
        pdf.close()
        markdown = text_to_markdown(text_content)
        return markdown, metadata

    except Exception as e:
        logger.error(f"Fallback processing failed: {e}")
        raise


def process_with_pix2text(pdf_path: str) -> Tuple[str, Dict]:
    try:
        from pix2text import Pix2Text
        p2t = Pix2Text()
        result = p2t.recognize_pdf(pdf_path)
        markdown = ""
        for page_result in result:
            if isinstance(page_result, dict) and 'text' in page_result:
                markdown += page_result['text'] + "\n\n"
            elif isinstance(page_result, str):
                markdown += page_result + "\n\n"
        metadata = {
            "page_count": len(result) if isinstance(result, list) else 1,
            "title": Path(pdf_path).stem.replace('_', ' '),
            "authors": []
        }
        return markdown, metadata

    except Exception as e:
        logger.error(f"Pix2Text processing failed: {e}")
        raise


def process_with_mineru_cli(pdf_path: str) -> Tuple[str, Dict]:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = ['mineru', '-p', pdf_path, '-o', tmpdir]
            logger.info(f"Running MinerU CLI: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                logger.error(f"MinerU CLI failed with return code {result.returncode}")
                if result.stderr:
                    logger.error(f"MinerU stderr: {result.stderr[:500]}")
                return "", {}

            pdf_name = Path(pdf_path).stem

            possible_paths = [
                Path(tmpdir) / pdf_name / "auto" / f"{pdf_name}.md",
                Path(tmpdir) / pdf_name / f"{pdf_name}.md",
                Path(tmpdir) / f"{pdf_name}.md",
            ]

            md_path = None
            for path in possible_paths:
                if path.exists():
                    md_path = path
                    logger.info(f"Found MinerU output at: {path}")
                    break

            if not md_path:
                md_files = list(Path(tmpdir).rglob("*.md"))
                if md_files:
                    md_path = md_files[0]
                    logger.info(f"Found MinerU output via search at: {md_path}")
                else:
                    logger.error("MinerU CLI: No markdown output file generated")
                    logger.error(f"Searched in: {tmpdir}")
                    for root, dirs, files in os.walk(tmpdir):
                        level = root.replace(tmpdir, '').count(os.sep)
                        indent = ' ' * 2 * level
                        logger.debug(f'{indent}{os.path.basename(root)}/')
                        subindent = ' ' * 2 * (level + 1)
                        for file in files:
                            logger.debug(f'{subindent}{file}')
                    return "", {}

            with open(md_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            images_dir = md_path.parent / "images"
            image_count = 0
            if images_dir.exists():
                image_files = list(images_dir.glob("*"))
                image_count = len(image_files)
                if image_count > 0:
                    logger.info(f"📸 Found {image_count} images extracted by MinerU")

            metadata = {
                "page_count": 0,
                "title": Path(pdf_path).stem.replace('_', ' '),
                "authors": [],
                "processor": "mineru",
                "images_extracted": image_count
            }

            page_refs = re.findall(r'Page \d+', markdown_content)
            if page_refs:
                page_nums = [int(ref.split()[-1]) for ref in page_refs]
                metadata["page_count"] = max(page_nums)

            return markdown_content, metadata

    except subprocess.TimeoutExpired:
        logger.error("MinerU CLI processing timed out after 600 seconds")
        return "", {}
    except Exception as e:
        logger.error(f"MinerU CLI processing failed: {e}")
        return "", {}


def process_with_nougat(pdf_path: str) -> Tuple[str, Dict]:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = ['nougat', pdf_path, '-o', tmpdir]
            logger.info(f"Running Nougat CLI: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if result.returncode != 0:
                raise Exception(f"Nougat CLI failed: {result.stderr}")
            output_files = list(Path(tmpdir).glob("*.mmd"))
            if not output_files:
                output_files = list(Path(tmpdir).glob("*.md"))
            if output_files:
                markdown = output_files[0].read_text(encoding='utf-8')
            else:
                raise Exception("No output file generated")
        metadata = {
            "page_count": 0,
            "title": Path(pdf_path).stem.replace('_', ' '),
            "authors": []
        }
        if "\\begin{" in markdown or "\\[" in markdown:
            metadata["has_math"] = True
        return markdown, metadata

    except Exception as e:
        logger.error(f"Nougat processing failed: {e}")
        raise
