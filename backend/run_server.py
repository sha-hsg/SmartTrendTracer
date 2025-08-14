#!/usr/bin/env python3
"""
Run the SmartTrendTracer backend server with proper shutdown handling.

Notes:
- Avoid custom signal handlers when using Uvicorn reload=True (reloader spawns subprocesses).
- This script runs without reload for predictable graceful shutdown.
"""

import signal
import sys
import logging
from typing import Optional

import uvicorn
from app.config import API_HOST, API_PORT

logger = logging.getLogger("smarttrendtracer.server")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Global server reference so our handler can request a graceful stop
server: Optional[uvicorn.Server] = None


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully without hard exit."""
    global server
    banner = "=" * 60
    logger.info("\n%s\n🛑 Shutdown signal received (%s)\n   Stopping server gracefully...\n%s", banner, sig, banner)

    # Ask any background systems to stop (best-effort)
    try:
        from app.improved_rate_limiter import shutdown_rate_limiter
        shutdown_rate_limiter()
        logger.info("Rate limiter shutdown requested.")
    except Exception as e:
        logger.debug("No rate limiter to shut down or failed to stop cleanly: %s", e)

    # Tell Uvicorn to exit its loop; let it drain gracefully
    if server is not None:
        server.should_exit = True
    # Do NOT sys.exit() here: let the event loop unwind gracefully.


def main():
    global server

    # Register signal handlers (guard SIGTERM for platforms that lack it)
    signal.signal(signal.SIGINT, signal_handler)
    try:
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception:
        logger.debug("SIGTERM not available on this platform.")

    logger.info("=" * 60)
    logger.info("🚀 SmartTrendTracer Backend Starting...")
    logger.info("=" * 60)
    logger.info("📡 API Server: http://%s:%s", API_HOST, API_PORT)
    logger.info("📚 API Docs: http://%s:%s/docs", API_HOST, API_PORT)
    logger.info("🎨 Dashboard: http://localhost:3000")
    logger.info("")
    logger.info("✨ Features on startup:")
    logger.info("  • Automatic gap-filling (collects tweets since last run)")
    logger.info("  • Scheduled collection every 30 minutes")
    logger.info("  • Interactive AI tagging system")
    logger.info("")
    logger.info("🛑 To shutdown properly: Press Ctrl+C")
    logger.info("=" * 60)

    # IMPORTANT: reload=False to keep signal handling predictable here.
    config = uvicorn.Config(
        app="app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,          # <— keep False if you use custom handlers
        log_level="info",
    )

    server = uvicorn.Server(config)

    try:
        server.run()
        logger.info("✅ Server stopped gracefully")
    except KeyboardInterrupt:
        logger.info("✅ Keyboard interrupt: server exiting")
    except Exception as e:
        logger.exception("❌ Server error: %s", e)
        # (Optionally) set a non-zero exit code on fatal errors:
        sys.exit(1)
    finally:
        logger.info("👋 Goodbye!")


if __name__ == "__main__":
    main()