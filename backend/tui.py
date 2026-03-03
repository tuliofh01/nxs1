"""
Terminal User Interface for Cloudfared Tunnel Manager
Uses Textual for a modern terminal UI
"""

import asyncio
import requests
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, Log, Label
from textual.reactive import reactive
from textual.events import Key


class TunnelStatus:
    """Data class for tunnel status"""
    status: str = "stopped"
    pid: int = 0
    uptime: int = 0
    url: str = ""


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
        height: 60%;
    }
    
    #controls {
        height: auto;
        padding: 1;
    }
    
    Button {
        margin: 0 1;
    }
    
    .status-running {
        color: $success;
    }
    
    .status-stopped {
        color: $error;
    }
    
    .status-starting {
        color: $warning;
    }
    """
    
    tunnel_status = reactive(TunnelStatus())
    logs = reactive([])
    
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Vertical(id="status-panel"):
                yield Static("TUNNEL STATUS", id="status-title")
                yield Label("Status: ", id="status-label")
                yield Label("PID: ", id="pid-label")
                yield Label("Uptime: ", id="uptime-label")
                yield Label("URL: ", id="url-label")
            
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
        self.update_status()
        self.update_logs()
        
        # Set up periodic updates
        self.set_interval(5, self.update_status)
        self.set_interval(10, self.update_logs)
    
    def update_status(self) -> None:
        """Fetch and update tunnel status"""
        try:
            response = requests.get("http://localhost:5000/api/tunnel/status", timeout=2)
            if response.status_code == 200:
                data = response.json()
                self.tunnel_status = TunnelStatus(
                    status=data.get("status", "unknown"),
                    pid=data.get("pid", 0),
                    uptime=data.get("uptime", 0),
                    url=data.get("url", "")
                )
                self.refresh_status_display()
        except requests.exceptions.RequestException:
            pass
    
    def update_logs(self) -> None:
        """Fetch and update logs"""
        try:
            response = requests.get("http://localhost:5000/api/logs?lines=50", timeout=2)
            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", [])
                self.logs = logs
                self.refresh_logs_display()
        except requests.exceptions.RequestException:
            pass
    
    def refresh_status_display(self) -> None:
        """Update the status labels"""
        status = self.tunnel_status
        
        status_label = self.query_one("#status-label", Label)
        status_label.update(f"Status: [{'success' if status.status == 'running' else 'error' if status.status == 'stopped' else 'warning'}]{status.status.upper()}[/]")
        
        pid_label = self.query_one("#pid-label", Label)
        pid_label.update(f"PID: {status.pid if status.pid else 'N/A'}")
        
        uptime_label = self.query_one("#uptime-label", Label)
        uptime_label.update(f"Uptime: {self.format_uptime(status.uptime)}")
        
        url_label = self.query_one("#url-label", Label)
        url_label.update(f"URL: {status.url if status.url else 'N/A'}")
    
    def refresh_logs_display(self) -> None:
        """Update the logs display"""
        log_viewer = self.query_one("#log-viewer", Log)
        log_viewer.clear()
        for line in self.logs[-50:]:  # Show last 50 lines
            log_viewer.write(line)
    
    def format_uptime(self, seconds: int) -> str:
        """Format uptime from seconds"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        if button_id == "start-btn":
            self.start_tunnel()
        elif button_id == "stop-btn":
            self.stop_tunnel()
        elif button_id == "refresh-btn":
            self.update_status()
            self.update_logs()
    
    def start_tunnel(self) -> None:
        """Start the tunnel"""
        try:
            response = requests.post(
                "http://localhost:5000/api/tunnel/start",
                json={"service": "ssh://localhost:22"},
                timeout=5
            )
            if response.status_code == 200:
                self.update_status()
        except requests.exceptions.RequestException as e:
            self.notify(f"Error: {str(e)}")
    
    def stop_tunnel(self) -> None:
        """Stop the tunnel"""
        try:
            response = requests.post(
                "http://localhost:5000/api/tunnel/stop",
                timeout=5
            )
            if response.status_code == 200:
                self.update_status()
        except requests.exceptions.RequestException as e:
            self.notify(f"Error: {str(e)}")


if __name__ == "__main__":
    app = TunnelTUI()
    app.run()
