"""
Terminal User Interface for Cloudfared Tunnel Manager
Uses Textual for a modern terminal UI
"""

import asyncio
import requests
import threading
import time
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, Log, Label
from textual.reactive import reactive


class TunnelTUI(App):
    """Terminal UI for Cloudfared Tunnel Manager"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        height: 100%;
        padding: 1;
    }
    
    #status-panel {
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }
    
    #logs-panel {
        border: solid $secondary;
        height: 1fr;
        min-height: 10;
    }
    
    #controls {
        height: auto;
        padding: 1;
    }
    
    Button {
        margin: 0 1;
    }
    
    Label {
        width: 100%;
    }

    .status-online { color: $success; }
    .status-offline { color: $error; }
    .status-connecting { color: $warning; }
    """
    
    # Reactive state
    status_text = reactive("STOPPED")
    status_class = reactive("status-offline")
    pid_text = reactive("N/A")
    uptime_text = reactive("0s")
    url_text = reactive("Not Connected")
    
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Vertical(id="status-panel"):
                yield Static("TUNNEL STATUS", id="status-title")
                yield Label(id="status-label")
                yield Label(id="pid-label")
                yield Label(id="uptime-label")
                yield Label(id="url-label")
            
            with Horizontal(id="controls"):
                yield Button("START", variant="primary", id="start-btn")
                yield Button("STOP", variant="error", id="stop-btn")
                yield Button("REFRESH", variant="default", id="refresh-btn")
            
            with Vertical(id="logs-panel"):
                yield Static("SYSTEM LOGS", id="logs-title")
                yield Log(id="log-viewer", auto_scroll=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the app"""
        self.update_data()
        self.set_interval(2, self.update_data)
    
    def update_data(self) -> None:
        """Fetch all data from the backend"""
        try:
            # Status update
            resp = requests.get("http://localhost:5000/api/tunnel/status", timeout=1)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "stopped")
                self.status_text = status.upper()
                self.status_class = f"status-{'online' if status == 'running' else 'connecting' if status == 'starting' else 'offline'}"
                self.pid_text = str(data.get("pid", "N/A"))
                self.url_text = data.get("url", "Not Connected")
                
                uptime = data.get("uptime", 0)
                if uptime < 60:
                    self.uptime_text = f"{uptime}s"
                else:
                    self.uptime_text = f"{uptime // 60}m {uptime % 60}s"
            
            # Logs update
            log_resp = requests.get("http://localhost:5000/api/logs?lines=20", timeout=1)
            if log_resp.status_code == 200:
                logs = log_resp.json().get("logs", [])
                log_viewer = self.query_one("#log-viewer", Log)
                log_viewer.clear()
                for line in logs:
                    log_viewer.write_line(line.strip())
                    
        except Exception:
            self.status_text = "BACKEND OFFLINE"
            self.status_class = "status-offline"

    def watch_status_text(self, value: str) -> None:
        self.query_one("#status-label", Label).update(f"Status: {value}")
        
    def watch_status_class(self, value: str) -> None:
        self.query_one("#status-label", Label).set_classes(value)
        
    def watch_pid_text(self, value: str) -> None:
        self.query_one("#pid-label", Label).update(f"PID: {value}")
        
    def watch_uptime_text(self, value: str) -> None:
        self.query_one("#uptime-label", Label).update(f"Uptime: {value}")
        
    def watch_url_text(self, value: str) -> None:
        self.query_one("#url-label", Label).update(f"URL: {value}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        try:
            if button_id == "start-btn":
                requests.post("http://localhost:5000/api/tunnel/start", json={"service": "ssh://localhost:22"}, timeout=2)
            elif button_id == "stop-btn":
                requests.post("http://localhost:5000/api/tunnel/stop", timeout=2)
            self.update_data()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")


if __name__ == "__main__":
    app = TunnelTUI()
    app.run()
