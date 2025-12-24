#!/usr/bin/env python3
"""
Restart the server with proper error handling
"""

import subprocess
import sys
import time
import signal
import os

def restart_server():
    """Restart the server."""
    print("🔄 Restarting Book RAG server...")
    
    try:
        # Kill any existing server processes
        print("1. Stopping existing server processes...")
        try:
            subprocess.run(["pkill", "-f", "start_server.py"], check=False)
            subprocess.run(["pkill", "-f", "uvicorn.*main:app"], check=False)
            time.sleep(2)
            print("   ✅ Existing processes stopped")
        except Exception as e:
            print(f"   ⚠️  Could not stop processes: {e}")
        
        # Start new server
        print("2. Starting new server...")
        print("   📍 Server will run on http://localhost:8001")
        print("   📝 Press Ctrl+C to stop the server")
        print("   🌐 Open http://localhost:8001 in your browser")
        print("\n" + "="*50)
        
        # Start server with proper error handling
        process = subprocess.Popen([
            sys.executable, "start_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Print server output
        try:
            for line in process.stdout:
                print(line.rstrip())
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            process.terminate()
            process.wait()
            print("✅ Server stopped")
            
    except Exception as e:
        print(f"❌ Failed to restart server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    restart_server()