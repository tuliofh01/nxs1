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
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configure Logging with 50MB limit (5 files x 10MB)
from logging.handlers import RotatingFileHandler

LOG_DIR = Path.home() / ".cloudfared-tunneling" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Create rotating file handler
rotating_handler = RotatingFileHandler(
    LOG_DIR / "tunnel.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5  # 5 files = 50MB total
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        rotating_handler,
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("cloudfared")

app = Flask(__name__)
CORS(app)

# Global state
TUNNEL_PROCESS: Optional[subprocess.Popen] = None
TUNNEL_URL: Optional[str] = None
START_TIME: Optional[float] = None


class TunnelManager:
    """Manages the Cloudflare Tunnel process"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.tunnel_url: Optional[str] = None
        
    def start(self, service_url: str = "ssh://localhost:22") -> Dict[str, Any]:
        """Start the cloudflared tunnel"""
        global TUNNEL_PROCESS, TUNNEL_URL, START_TIME
        
        if self.process and self.process.poll() is None:
            return {"status": "running", "url": self.tunnel_url}
        
        try:
            # Start cloudflared tunnel
            cmd = ["cloudflared", "tunnel", "--url", service_url]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for URL to be established
            time.sleep(5)
            
            # For now, return success - URL extraction would need proper parsing
            TUNNEL_PROCESS = self.process
            START_TIME = time.time()
            TUNNEL_URL = f"tunnel://{self.process.pid}"
            
            logger.info(f"Tunnel started with PID {self.process.pid}")
            
            return {
                "status": "starting",
                "pid": self.process.pid,
                "service": service_url
            }
            
        except Exception as e:
            logger.error(f"Failed to start tunnel: {e}")
            return {"status": "error", "message": str(e)}
    
    def stop(self) -> Dict[str, Any]:
        """Stop the cloudflared tunnel"""
        global TUNNEL_PROCESS, TUNNEL_URL, START_TIME
        
        if not self.process:
            return {"status": "stopped"}
        
        try:
            self.process.terminate()
            self.process.wait(timeout=10)
            
            TUNNEL_PROCESS = None
            TUNNEL_URL = None
            START_TIME = None
            
            logger.info("Tunnel stopped")
            return {"status": "stopped"}
            
        except Exception as e:
            logger.error(f"Failed to stop tunnel: {e}")
            return {"status": "error", "message": str(e)}
    
    def status(self) -> Dict[str, Any]:
        """Get tunnel status"""
        if not self.process:
            return {
                "status": "stopped",
                "uptime": 0
            }
        
        if self.process.poll() is not None:
            return {
                "status": "crashed",
                "exit_code": self.process.returncode
            }
        
        uptime = int(time.time() - START_TIME) if START_TIME else 0
        
        return {
            "status": "running",
            "pid": self.process.pid,
            "uptime": uptime,
            "url": TUNNEL_URL
        }
    
    def get_logs(self, lines: int = 100) -> list:
        """Get recent tunnel logs"""
        try:
            # Try to get logs from journalctl for SSH
            result = subprocess.run(
                ["journalctl", "-u", "sshd", "-n", str(lines), "--no-pager"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.splitlines()
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return []


# Initialize manager
tunnel_manager = TunnelManager()


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/tunnel/start", methods=["POST"])
def start_tunnel():
    """Start the tunnel"""
    data = request.get_json() or {}
    service_url = data.get("service", "ssh://localhost:22")
    
    result = tunnel_manager.start(service_url)
    return jsonify(result)


@app.route("/api/tunnel/stop", methods=["POST"])
def stop_tunnel():
    """Stop the tunnel"""
    result = tunnel_manager.stop()
    return jsonify(result)


@app.route("/api/tunnel/status", methods=["GET"])
def get_status():
    """Get tunnel status"""
    result = tunnel_manager.status()
    return jsonify(result)


@app.route("/api/logs", methods=["GET"])
def get_logs():
    """Get recent logs"""
    lines = request.args.get("lines", 100, type=int)
    logs = tunnel_manager.get_logs(lines)
    return jsonify({
        "logs": logs,
        "count": len(logs)
    })


@app.route("/api/system/info", methods=["GET"])
def system_info():
    """Get system information"""
    import psutil
    
    return jsonify({
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "uptime": int(time.time() - psutil.boot_time())
    })


if __name__ == "__main__":
    logger.info("Starting Cloudfared Tunnel Manager Backend")
    app.run(host="0.0.0.0", port=5000, debug=True)
