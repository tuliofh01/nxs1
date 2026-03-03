"""
Cloudfared Tunnel Manager - Backend Application
Flask API for managing Cloudflare Tunnel and system monitoring
"""

import os
import sys
import subprocess
import logging
import time
import signal
import threading
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from flask import Flask, jsonify, request
from flask_cors import CORS
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WORKER_URL = os.getenv("WORKER_URL", "https://nxs1.tuliofh01.workers.dev")
TUNNEL_SECRET = os.getenv("TUNNEL_SECRET", "")

# Configure Logging with 50MB limit (5 files x 10MB)
LOG_DIR = Path.home() / ".cloudfared-tunneling" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("cloudfared")
logger.setLevel(logging.INFO)

# Create rotating file handler
rotating_handler = RotatingFileHandler(
    LOG_DIR / "tunnel.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5  # 5 files = 50MB total
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rotating_handler.setFormatter(formatter)

# Stream handler for console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(rotating_handler)
logger.addHandler(stream_handler)

app = Flask(__name__)
CORS(app)

# Global state
class GlobalState:
    process: Optional[subprocess.Popen] = None
    tunnel_url: str = "Not Connected"
    start_time: Optional[float] = None
    is_syncing: bool = False

state = GlobalState()

def sync_with_worker():
    """Background thread to sync status and logs with Cloudflare Worker"""
    last_log_count = 0
    while True:
        try:
            # Get current logs to send new ones
            current_logs = tunnel_manager.get_logs(100)
            new_logs = []
            if len(current_logs) > last_log_count:
                new_logs = current_logs[last_log_count:]
            elif len(current_logs) < last_log_count:
                new_logs = current_logs # Log rotation happened
            
            last_log_count = len(current_logs)

            status_data = {
                "tunnelUrl": state.tunnel_url,
                "logs": new_logs,
                "timestamp": int(time.time() * 1000)
            }
            headers = {}
            if TUNNEL_SECRET:
                headers["Authorization"] = f"Bearer {TUNNEL_SECRET}"
            
            requests.post(
                f"{WORKER_URL}/api/tunnel",
                json=status_data,
                headers=headers,
                timeout=10
            )
        except Exception as e:
            logger.debug(f"Sync failed: {e}")
        
        time.sleep(30)  # Sync every 30 seconds

class TunnelManager:
    """Manages the Cloudflare Tunnel process"""
    
    def start(self, service_url: str = "ssh://localhost:22") -> Dict[str, Any]:
        """Start the cloudflared tunnel"""
        if state.process and state.process.poll() is None:
            return {"status": "running", "url": state.tunnel_url}
        
        try:
            # Start cloudflared tunnel
            # Use --origincert if needed, but --url for quick tunnels
            cmd = ["cloudflared", "tunnel", "--url", service_url]
            state.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            state.start_time = time.time()
            state.tunnel_url = "Connecting..."
            
            # Start a thread to parse stderr for the URL
            def monitor_output(proc):
                if proc.stderr:
                    for line in proc.stderr:
                        logger.info(f"cloudflared: {line.strip()}")
                        if "trycloudflare.com" in line:
                            # Extract URL
                            parts = line.split()
                            for p in parts:
                                if "https://" in p and "trycloudflare.com" in p:
                                    state.tunnel_url = p.strip()
                                    logger.info(f"Tunnel URL found: {state.tunnel_url}")
                                    break
            
            threading.Thread(target=monitor_output, args=(state.process,), daemon=True).start()
            
            return {
                "status": "starting",
                "pid": state.process.pid,
                "service": service_url
            }
            
        except Exception as e:
            logger.error(f"Failed to start tunnel: {e}")
            return {"status": "error", "message": str(e)}
    
    def stop(self) -> Dict[str, Any]:
        """Stop the cloudflared tunnel"""
        if not state.process:
            return {"status": "stopped"}
        
        try:
            state.process.terminate()
            try:
                state.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                state.process.kill()
            
            state.process = None
            state.tunnel_url = "Not Connected"
            state.start_time = None
            
            logger.info("Tunnel stopped")
            return {"status": "stopped"}
            
        except Exception as e:
            logger.error(f"Failed to stop tunnel: {e}")
            return {"status": "error", "message": str(e)}
    
    def status(self) -> Dict[str, Any]:
        """Get tunnel status"""
        if not state.process:
            return {
                "status": "stopped",
                "uptime": 0,
                "url": "Not Connected"
            }
        
        poll = state.process.poll()
        if poll is not None:
            return {
                "status": "crashed",
                "exit_code": poll,
                "url": "Error"
            }
        
        uptime = int(time.time() - state.start_time) if state.start_time else 0
        
        return {
            "status": "running",
            "pid": state.process.pid,
            "uptime": uptime,
            "url": state.tunnel_url
        }
    
    def get_logs(self, lines: int = 100) -> list:
        """Get recent tunnel logs from journalctl and local file"""
        logs = []
        try:
            # Local app logs
            log_file = LOG_DIR / "tunnel.log"
            if log_file.exists():
                with open(log_file, "r") as f:
                    logs.extend(f.readlines()[-lines:])
            
            # System logs for sshd
            result = subprocess.run(
                ["journalctl", "-u", "sshd", "-n", str(lines), "--no-pager"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                logs.extend(result.stdout.splitlines())
                
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            
        return sorted(logs)[-lines:]

# Initialize manager
tunnel_manager = TunnelManager()

# Start sync thread
threading.Thread(target=sync_with_worker, daemon=True).start()

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/tunnel/start", methods=["POST"])
def start_tunnel():
    data = request.get_json() or {}
    service_url = data.get("service", "ssh://localhost:22")
    return jsonify(tunnel_manager.start(service_url))

@app.route("/api/tunnel/stop", methods=["POST"])
def stop_tunnel():
    return jsonify(tunnel_manager.stop())

@app.route("/api/tunnel/status", methods=["GET"])
def get_status():
    return jsonify(tunnel_manager.status())

@app.route("/api/logs", methods=["GET"])
def get_logs():
    lines = request.args.get("lines", 100, type=int)
    logs = tunnel_manager.get_logs(lines)
    return jsonify({
        "logs": logs,
        "count": len(logs)
    })

@app.route("/api/system/info", methods=["GET"])
def system_info():
    import psutil
    try:
        return jsonify({
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "uptime": int(time.time() - psutil.boot_time())
        })
    except Exception:
        return jsonify({"error": "Failed to get system info"}), 500

if __name__ == "__main__":
    logger.info("Starting Cloudfared Tunnel Manager Backend")
    # In production use a real WSGI server like gunicorn
    app.run(host="0.0.0.0", port=5000)
