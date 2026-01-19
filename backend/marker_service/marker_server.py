#!/usr/bin/env python3
"""
Marker PDF Service (CLI-only, tolerant, canonical image refs)
- PTY-run marker_single (progress in logs)
- Proceed if CLI rc != 0 when markdown exists
- Persist images via ImageManager, then:
  * Fix malformed `!(...)` → `![](...)`
  * Server mode: FS under IMAGE_BASE_DIR → /api/papers/... URLs
  * Test mode:   /api/papers/... → absolute FS paths, and normalize them
"""

from __future__ import annotations

import os, re, sys, json, pty, select, shutil, logging, tempfile, subprocess, asyncio, time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import glob

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import httpx  # For progress callbacks
import psutil  # For process health monitoring

# ---- Project import (ImageManager) ------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.services.image_manager import ImageManager  # noqa: E402

APP_VERSION = "2.6.2"
logger = logging.getLogger("marker_server")
logging.basicConfig(level=logging.INFO)

# ---- Debug & paths ----------------------------------------------------------------
DEBUG_DEFAULT = os.getenv("MARKER_DEBUG", "0").lower() in {"1", "true", "yes"}
REWRITE_TO_FILES_DEFAULT = os.getenv("MARKER_REWRITE_TO_FILES", "0").lower() in {"1", "true", "yes"}

IMAGE_BASE_DIR = os.getenv(
    "IMAGE_BASE_DIR",
    str((Path(__file__).parent.parent / "data" / "paper_images").resolve())
)

def _prepend_venv_bin_to_path():
    bin_dir = str(Path(sys.executable).parent)
    os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH','')}"
    logger.info("PATH primed with interpreter bin: %s", bin_dir)
_prepend_venv_bin_to_path()

# ---- FastAPI ----------------------------------------------------------------------
app = FastAPI(title="Marker PDF Service (CLI-only)", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# ---- Helpers ----------------------------------------------------------------------
ALLOWED_OUTPUT_FORMATS = {"markdown", "html", "json"}
IMG_EXTS = ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.svg", "*.webp")

MD_IMG_STD  = re.compile(r'!\[(?P<alt>[^\]]*)\]\((?P<url>[^)]+)\)')
MD_IMG_BARE = re.compile(r'!\((?P<url>[^)]+)\)')  # malformed style we’ve seen

def _secure_filename(name: str) -> str:
    name = os.path.basename(name or "")
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    if not name:
        name = "upload.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name

def _validate_output_format(fmt: str) -> str:
    fmt = (fmt or "").strip().lower()
    if fmt not in ALLOWED_OUTPUT_FORMATS:
        raise HTTPException(status_code=422, detail=f"Invalid output_format '{fmt}'. Allowed: {sorted(ALLOWED_OUTPUT_FORMATS)}")
    return fmt

def _send_progress_callback(callback_url: str, progress_data: dict):
    """Send progress update to callback URL"""
    if not callback_url:
        return
    
    try:
        import httpx
        with httpx.Client(timeout=5.0) as client:
            response = client.post(callback_url, json=progress_data)
            if response.status_code == 200:
                logger.info(f"Progress callback sent: {progress_data.get('message', 'N/A')}")
            else:
                logger.warning(f"Progress callback failed: {response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to send progress callback: {e}")

# ANSI escape code pattern for stripping terminal colors/formatting
_ANSI_ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\].*?\x07')

def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text (colors, cursor movements, etc.)"""
    return _ANSI_ESCAPE_PATTERN.sub('', text)

def _get_process_health(pid: int, out_dir: str) -> dict:
    """Collect process health metrics using psutil"""
    try:
        process = psutil.Process(pid)

        # Get CPU and memory info
        cpu_times = process.cpu_times()
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent(interval=0.1)

        # Check for output files
        out_path = Path(out_dir)
        markdown_exists = False
        image_count = 0

        if out_path.exists():
            # Check for markdown file
            md_files = list(out_path.glob("*.md"))
            markdown_exists = len(md_files) > 0

            # Count images
            for ext in ["*.png", "*.jpg", "*.jpeg"]:
                image_count += len(list(out_path.glob(ext)))

        return {
            "pid": pid,
            "cpu_time": cpu_times.user + cpu_times.system,
            "memory_mb": memory_info.rss / (1024 * 1024),
            "cpu_percent": cpu_percent,
            "output_files": {
                "markdown_exists": markdown_exists,
                "image_count": image_count
            }
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
        logger.warning(f"Failed to get process health: {e}")
        return {
            "pid": pid,
            "cpu_time": 0,
            "memory_mb": 0,
            "cpu_percent": 0,
            "output_files": {
                "markdown_exists": False,
                "image_count": 0
            }
        }

def _parse_marker_progress(line: str) -> Optional[dict]:
    """Parse marker output for progress information (supports TQDM format)"""
    # Strip ANSI escape codes first (important for Linux terminals)
    line = _strip_ansi(line.strip())

    if not line:
        return None

    # TQDM progress bar pattern: "50%|█████     | 25/50 [00:15<00:15, 1.66it/s]"
    # More flexible pattern that handles various bar characters
    tqdm_match = re.search(r'(\d+)%\s*\|[^\|]*\|\s*(\d+)/(\d+)', line)
    if tqdm_match:
        percent_str, current_str, total_str = tqdm_match.groups()
        percent = int(percent_str)
        current = int(current_str)
        total = int(total_str)

        # Extract description before progress bar if present
        desc_match = re.search(r'^([^:]+):\s*\d+%', line)
        description = desc_match.group(1).strip() if desc_match else "Processing"

        # Determine stage based on description
        stage = "processing"
        if "layout" in description.lower():
            stage = "layout_detection"
        elif "ocr" in description.lower() or "text" in description.lower():
            stage = "text_extraction"
        elif "image" in description.lower():
            stage = "image_extraction"
        elif "page" in description.lower():
            stage = "page_processing"

        return {
            "stage": stage,
            "message": f"{description}: {current}/{total} ({percent}%)",
            "progress": percent,
            "current": current,
            "total": total
        }

    # Fallback: look for standalone percentage (e.g., "Processing... 75%")
    elif "%" in line:
        match = re.search(r'(\d+)%', line)
        if match:
            percent = int(match.group(1))
            # Try to extract meaningful message
            message = line[:80] if len(line) <= 80 else line[:77] + "..."
            return {
                "stage": "processing",
                "message": message,
                "progress": percent
            }

    # Fallback: recognize common Marker stage keywords
    elif any(keyword in line.lower() for keyword in ["extracting", "converting", "detecting", "finalizing", "loading"]):
        stage_keywords = {
            "extracting images": ("image_extraction", 30),
            "detecting layout": ("layout_detection", 20),
            "extracting text": ("text_extraction", 50),
            "converting": ("markdown_conversion", 75),
            "finalizing": ("finalizing", 90),
            "loading model": ("initialization", 10)
        }

        for keyword, (stage, progress) in stage_keywords.items():
            if keyword in line.lower():
                return {
                    "stage": stage,
                    "message": line[:80] if len(line) <= 80 else line[:77] + "...",
                    "progress": progress
                }

    return None

def _cli_run_streaming(pdf_path: str, out_dir: str, callback_url: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
    cmd = ["marker_single", pdf_path, "--output_dir", out_dir]
    env = os.environ.copy(); env.setdefault("PYTHONUNBUFFERED", "1"); env.setdefault("TQDM_DISABLE", "0")
    try:
        logger.info("CLI: %s %s", cmd[0], " ".join(cmd[1:]))
        master_fd, slave_fd = pty.openpty()
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=slave_fd, stderr=slave_fd,
                                    close_fds=True, env=env, text=False)
        finally:
            os.close(slave_fd)
        chunks: List[str] = []
        last_callback_time = 0.0  # Track time of last callback for throttling
        callback_interval = 2.0  # Minimum seconds between callbacks
        heartbeat_interval = 15.0  # Send heartbeat if no progress update for this long
        last_progress_update = time.time()  # Track when we last got a real progress update

        # Send initial progress
        if callback_url:
            _send_progress_callback(callback_url, {
                "stage": "initializing",
                "message": "Starting PDF processing with Marker",
                "progress": 0
            })
            last_callback_time = time.time()

        while True:
            r, _, _ = select.select([master_fd], [], [], 0.1)
            if master_fd in r:
                data = os.read(master_fd, 8192)
                if not data: break
                s = data.decode(errors="replace"); sys.stdout.write(s); sys.stdout.flush(); chunks.append(s)

                # Parse progress and send callbacks with time-based throttling
                if callback_url:
                    current_time = time.time()
                    if (current_time - last_callback_time) >= callback_interval:
                        # Split on both \r and \n (TQDM uses \r for in-place updates)
                        found_progress = False
                        for line in re.split(r'[\r\n]+', s):
                            if line.strip():
                                progress_info = _parse_marker_progress(line)
                                if progress_info:
                                    # Add process health data
                                    progress_info['health'] = _get_process_health(proc.pid, out_dir)
                                    _send_progress_callback(callback_url, progress_info)
                                    last_callback_time = current_time
                                    last_progress_update = current_time
                                    found_progress = True
                                    break  # Only send one update per interval

                        # Heartbeat fallback: if no progress found and it's been a while
                        if not found_progress and (current_time - last_progress_update) >= heartbeat_interval:
                            health = _get_process_health(proc.pid, out_dir)
                            _send_progress_callback(callback_url, {
                                "stage": "processing",
                                "message": f"Processing... (CPU: {health.get('cpu_percent', 0):.1f}%, RAM: {health.get('memory_mb', 0):.0f}MB)",
                                "progress": -1,  # -1 indicates indeterminate progress
                                "health": health
                            })
                            last_callback_time = current_time
                            last_progress_update = current_time  # Reset to avoid spamming
            else:
                # No data received, but process still running - check for heartbeat
                if callback_url:
                    current_time = time.time()
                    if (current_time - last_progress_update) >= heartbeat_interval:
                        health = _get_process_health(proc.pid, out_dir)
                        _send_progress_callback(callback_url, {
                            "stage": "processing",
                            "message": f"Processing... (CPU: {health.get('cpu_percent', 0):.1f}%, RAM: {health.get('memory_mb', 0):.0f}MB)",
                            "progress": -1,  # -1 indicates indeterminate progress
                            "health": health
                        })
                        last_progress_update = current_time

            if proc.poll() is not None:
                while True:
                    try: data = os.read(master_fd, 8192)
                    except OSError: data = b""
                    if not data: break
                    s = data.decode(errors="replace"); sys.stdout.write(s); sys.stdout.flush(); chunks.append(s)

                    # Parse final progress (no throttling for final output)
                    if callback_url:
                        # Split on both \r and \n (TQDM uses \r for in-place updates)
                        for line in re.split(r'[\r\n]+', s):
                            if line.strip():
                                progress_info = _parse_marker_progress(line)
                                if progress_info:
                                    # Add process health data
                                    progress_info['health'] = _get_process_health(proc.pid, out_dir)
                                    _send_progress_callback(callback_url, progress_info)
                                    break  # Only send last progress update
                break
        os.close(master_fd)
        combined = "".join(chunks); rc = proc.returncode; ok = (rc == 0)
        
        # Send completion callback
        if callback_url:
            if ok:
                _send_progress_callback(callback_url, {
                    "stage": "completed",
                    "message": "PDF processing completed successfully",
                    "progress": 100
                })
            else:
                _send_progress_callback(callback_url, {
                    "stage": "failed", 
                    "message": f"PDF processing failed (exit code: {rc})",
                    "progress": 0,
                    "error": f"Command failed with exit code {rc}"
                })
        
        return ok, combined, rc
    except FileNotFoundError:
        msg = "marker_single not found in PATH. Install marker-pdf in this venv."
        logger.error(msg); return False, msg, 127
    except Exception as e:
        msg = f"unexpected CLI error: {e}"
        logger.error(msg); return False, msg, None

def _cli_find_markdown_and_meta(root: str, stem_preference: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    root_p = Path(root); md_path: Optional[str] = None
    if stem_preference:
        cand = root_p / f"{stem_preference}.md"
        if cand.exists(): md_path = str(cand)
    if not md_path:
        for p in root_p.rglob("*.md"): md_path = str(p); break
    meta_path: Optional[str] = None
    if md_path:
        cand_meta = Path(md_path).with_name(Path(md_path).stem + "_meta.json")
        if cand_meta.exists(): meta_path = str(cand_meta)
        else:
            for j in root_p.rglob("*_meta.json"): meta_path = str(j); break
    return md_path, meta_path

def _cli_collect_images(root: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for ext in IMG_EXTS:
        for p in Path(root).rglob(ext): mapping[p.name] = str(p)
    return mapping

def _masked(s: Optional[str]) -> str:
    if not s: return ""
    return "****" if len(s) <= 8 else s[:4] + "…" + s[-4:]

def _is_under(base: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve()); return True
    except Exception:
        return False

def _fs_to_api(url: str, paper_id: int, base_dir: str) -> Optional[str]:
    p = Path(url); base = Path(base_dir)
    if p.is_absolute() and _is_under(base, p):
        try: tail = str(p.resolve().relative_to(base.resolve()))
        except Exception: return None
        return f"/api/papers/{paper_id}/images/{tail}"
    return None

def _api_to_fs(url: str, paper_id: int, base_dir: str) -> Optional[str]:
    prefix = f"/api/papers/{paper_id}/images/"
    if url.startswith(prefix):
        tail = url[len(prefix):].lstrip("/")
        return str(Path(base_dir) / tail)
    return None

def _normalize_images_to_standard(markdown_text: str) -> str:
    return MD_IMG_BARE.sub(lambda m: f"![]({m.group('url').strip()})", markdown_text or "")

def _coerce_abs_fs(url: str) -> str:
    u = url.strip()
    if u.lower().startswith("file://"): u = u[7:]
    if u.startswith("~/"): u = os.path.expanduser(u)
    if sys.platform == "darwin":
        if u.startswith("Users/") or u.startswith("Volumes/"): u = "/" + u
    return u

def _dedupe_base_prefix(url: str, base_dir: str) -> str:
    """
    Collapse the case where the URL starts with IMAGE_BASE_DIR and then contains
    another absolute path (e.g., '/Users/...') by keeping the absolute tail.
    """
    base = str(Path(base_dir).resolve())
    m = re.search(r"(/Users/|/Volumes/)", url)
    if url.startswith(base) and m and m.start() > 0:
        return url[m.start():]
    return url

def _normalize_fs_urls_for_tests(markdown_text: str, *, base_dir: str) -> str:
    def repl(m):
        alt = m.group("alt"); url = m.group("url").strip()
        norm = _coerce_abs_fs(url)
        norm = _dedupe_base_prefix(norm, base_dir)
        return f"![{alt}]({norm})"
    return MD_IMG_STD.sub(repl, markdown_text or "")

def _canonicalize_image_urls(markdown_text: str, *, paper_id: Optional[int], base_dir: str, to_files: bool) -> str:
    if not paper_id: return markdown_text or ""
    def repl(m):
        alt = m.group("alt"); url = m.group("url").strip()
        if to_files:
            fs = _api_to_fs(url, paper_id, base_dir)
            if fs: return f"![{alt}]({fs})"
            # leave as-is; later pass will normalize any remaining FS lookalikes
            return m.group(0)
        else:
            api = _fs_to_api(url, paper_id, base_dir)
            if api: return f"![{alt}]({api})"
            return m.group(0)
    return MD_IMG_STD.sub(repl, markdown_text or "")

# ---- Endpoints -------------------------------------------------------------------
@app.get("/")
def read_root():
    return {
        "service": "Marker PDF Service (CLI-only)",
        "status": "running",
        "version": APP_VERSION,
        "debug_default": DEBUG_DEFAULT,
        "rewrite_to_files_default": REWRITE_TO_FILES_DEFAULT,
        "image_base_dir": IMAGE_BASE_DIR,
        "endpoints": {"/convert": "...", "/health": "...", "/llm_health": "...", "/debug/which": "..."},
    }

@app.get("/health")
def health_check():
    import shutil as _sh
    found = _sh.which("marker_single")
    return {"status": "healthy" if found else "unhealthy",
            "marker": "available" if found else "unavailable",  # Backend expects this
            "marker_single": found or "not found",
            "detail": None if found else "Install marker-pdf into this venv.",
            "image_base_dir": IMAGE_BASE_DIR}

@app.get("/llm_health")
def llm_health():
    env = os.environ
    return {
        "openai": bool(env.get("OPENAI_API_KEY")),
        "anthropic": bool(env.get("ANTHROPIC_API_KEY")),
        "google_gemini": bool(env.get("GOOGLE_API_KEY")),
        "xai": bool(env.get("XAI_API_KEY") or env.get("GROK_API_KEY")),
        "deepseek": bool(env.get("DEEPSEEK_API_KEY")),
        "huggingface": bool(env.get("HUGGINGFACE_TOKEN")),
        "keys": {k: ("****" if not env.get(k) else (env.get(k)[:4] + "…" + env.get(k)[-4:])) for k in
                 ["OPENAI_API_KEY","ANTHROPIC_API_KEY","GOOGLE_API_KEY","XAI_API_KEY","DEEPSEEK_API_KEY","HUGGINGFACE_TOKEN"]},
    }

@app.get("/debug/which")
def debug_which():
    import shutil as _sh
    return {"marker_single": _sh.which("marker_single"), "python": sys.executable, "PATH_head": os.environ.get("PATH","")[:500]}

# ---- Core conversion --------------------------------------------------------------
@app.post("/convert")
def convert_pdf(
    file: UploadFile = File(...),
    output_format: str = Form("markdown"),
    paper_id: Optional[int] = Form(None),
    debug: bool = Form(DEBUG_DEFAULT),
    rewrite_to_files: bool = Form(REWRITE_TO_FILES_DEFAULT),
    callback_url: Optional[str] = Form(None),  # Progress callback URL
    # compatibility params (ignored by CLI)
    force_ocr: bool = Form(False),
    page_range: Optional[str] = Form(None),
    strip_existing_ocr: bool = Form(False),
    use_llm: bool = Form(True),
    skip_tables: bool = Form(False),
    llm_light: bool = Form(False),
    llm_service: Optional[str] = Form(None),
    llm_temperature: Optional[float] = Form(None),
    llm_max_tokens: Optional[int] = Form(None),
):
    _ = _validate_output_format(output_format)
    orig_name = _secure_filename(file.filename or "upload.pdf")
    if not orig_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are supported.")

    # run directory
    if debug:
        keep_root = Path(__file__).parent / "debug_runs"; keep_root.mkdir(parents=True, exist_ok=True)
        run_dir = tempfile.mkdtemp(prefix="marker_cli_", dir=str(keep_root)); kept_dir = run_dir
    else:
        run_dir = tempfile.mkdtemp(prefix="marker_cli_"); kept_dir = None

    pdf_path = os.path.join(run_dir, orig_name)

    try:
        with open(pdf_path, "wb") as f: shutil.copyfileobj(file.file, f)
        ok, cli_logs, rc = _cli_run_streaming(pdf_path, run_dir, callback_url=callback_url)

        stem = Path(orig_name).stem
        md_path, meta_path = _cli_find_markdown_and_meta(run_dir, stem_preference=stem)
        md_exists = bool(md_path and Path(md_path).exists())

        if not ok and not md_exists:
            tree = []
            for d in sorted(Path(run_dir).glob("*")):
                if d.is_dir():
                    entries = [f"  {p.name}" for p in sorted(d.glob('*'))[:50]]
                    tree.append(f"{d.name}/\n" + "\n".join(entries))
                else:
                    tree.append(d.name)
            detail = "marker_single failed (no markdown found)"
            if debug:
                detail = {"error": detail, "rc": rc, "dir_tree": tree, "cli_logs": cli_logs[-6000:], "kept_dir": kept_dir or run_dir}
            raise HTTPException(status_code=500, detail=detail)

        if not md_exists:
            detail = "CLI reported success but no markdown file was produced"
            if debug: detail = {"error": detail, "rc": rc, "cli_logs": cli_logs[-6000:], "kept_dir": kept_dir or run_dir}
            raise HTTPException(status_code=500, detail=detail)

        markdown_text = Path(md_path).read_text(encoding="utf-8", errors="replace")
        metadata: Dict[str, Any] = {}
        if meta_path and Path(meta_path).exists():
            try: metadata = json.loads(Path(meta_path).read_text(encoding="utf-8", errors="replace")) or {}
            except Exception: metadata = {}

        images_count = 0; image_meta: List[Dict[str, Any]] = []
        if paper_id:
            try:
                image_manager = ImageManager(base_path=IMAGE_BASE_DIR)
            except TypeError:
                os.environ.setdefault("IMAGE_BASE_DIR", IMAGE_BASE_DIR)
                image_manager = ImageManager()
            image_files = _cli_collect_images(run_dir)
            try:
                rewritten_text, image_meta = image_manager.process_markdown_images(
                    paper_id=paper_id, markdown=markdown_text, image_files=image_files, processor="marker",
                )
                markdown_text = rewritten_text
                images_count = len(image_meta)
                logger.info("Persisted %d images for paper %s", images_count, paper_id)
            except Exception as img_err:
                logger.warning("ImageManager failed: %s", img_err, exc_info=True)

        # normalize + canonicalize
        markdown_text = _normalize_images_to_standard(markdown_text)
        if paper_id:
            if rewrite_to_files:
                # API → FS
                markdown_text = _canonicalize_image_urls(markdown_text, paper_id=paper_id, base_dir=IMAGE_BASE_DIR, to_files=True)
                # Absolute path cleanup for tests
                markdown_text = _normalize_fs_urls_for_tests(markdown_text, base_dir=IMAGE_BASE_DIR)
            else:
                # FS → API
                markdown_text = _canonicalize_image_urls(markdown_text, paper_id=paper_id, base_dir=IMAGE_BASE_DIR, to_files=False)

        payload: Dict[str, Any] = {
            "success": True,
            "format": output_format,
            "content": markdown_text,
            "metadata": metadata,
            "images": images_count,
            "images_extracted": images_count if paper_id else 0,
            "tables_skipped": False,
            "llm_used": bool(use_llm),
            "page_range": "all",
            "forced_cli": True,
        }

        if debug:
            payload["_debug"] = {
                "cli_rc": rc,
                "cli_logs": cli_logs[-6000:],
                "disk_images_found": len(_cli_collect_images(run_dir)),
                "kept_dir": kept_dir or run_dir,
                "md_file": md_path,
                "meta_file": meta_path,
                "image_base_dir": IMAGE_BASE_DIR,
                "image_meta": image_meta,
                "rewrite_to_files": bool(rewrite_to_files),
            }

        logger.info("CLI conversion ok: %s (rc=%s, md=%s)", orig_name, rc, md_path)
        return payload

    except HTTPException: raise
    except Exception as e:
        logger.error("Unexpected server error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if not debug and os.path.exists(run_dir):
            try: shutil.rmtree(run_dir)
            except Exception as cleanup_err:
                logger.warning("Failed to clean up run dir: %s", cleanup_err)

if __name__ == "__main__":
    import uvicorn
    print(f"Starting Marker PDF service (CLI-only) on http://0.0.0.0:8002 (v{APP_VERSION}) ...")
    uvicorn.run(app, host="0.0.0.0", port=8002)