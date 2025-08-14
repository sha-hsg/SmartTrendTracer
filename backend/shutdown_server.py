#!/usr/bin/env python3
"""
Gracefully shutdown the backend server
"""
import subprocess
import signal
import time
import sys

def shutdown_server():
    """Gracefully shutdown the server"""
    print("🔄 Initiating graceful server shutdown...")
    
    # Find the process running on port 8000
    try:
        # Get process ID using lsof
        result = subprocess.run(
            ['lsof', '-ti:8000'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            print("❌ No server running on port 8000")
            return False
        
        pids = result.stdout.strip().split('\n')
        
        for pid in pids:
            try:
                pid = int(pid)
                print(f"   Sending SIGTERM to process {pid}...")
                subprocess.run(['kill', '-TERM', str(pid)])
            except (ValueError, subprocess.CalledProcessError):
                pass
        
        # Wait a moment for graceful shutdown
        time.sleep(2)
        
        # Check if processes are still running
        result = subprocess.run(
            ['lsof', '-ti:8000'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # Force kill if still running
            print("   Force killing remaining processes...")
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    subprocess.run(['kill', '-9', pid])
                except subprocess.CalledProcessError:
                    pass
        
        print("✅ Server shutdown complete")
        return True
        
    except Exception as e:
        print(f"❌ Error shutting down server: {e}")
        return False

if __name__ == "__main__":
    success = shutdown_server()
    sys.exit(0 if success else 1)