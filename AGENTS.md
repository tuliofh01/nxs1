# Cloudfared Tunnel Manager - Agents Guide

This project is organized into three main domains. Each domain has specific responsibilities and interacts with the others through well-defined interfaces.

## Project Structure

```
cloudfared-tunneling/
├── backend/              # Python Flask API + Terminal Interface
├── frontend/            # Angular Frontend Application  
├── src/                 # Cloudflare Worker (unchanged boilerplate)
├── worker-configuration.d.ts
├── wrangler.json
└── pyproject.toml       # Poetry project configuration
```

## Domain A: Local Backend (Python/Flask)

**Location**: `backend/`
**Purpose**: Controls cloudflared tunnel, manages logs, exposes local API

### Key Files
- `app.py` - Flask API server (port 5000)
- `tui.py` - Terminal User Interface (Textual)
- `requirements.txt` - Python dependencies

### API Endpoints
- `GET /api/tunnel/status` - Get tunnel status
- `POST /api/tunnel/start` - Start tunnel
- `POST /api/tunnel/stop` - Stop tunnel
- `GET /api/logs` - Get system logs
- `GET /api/system/info` - Get system info

### Commands
```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run Flask API
python app.py

# Run TUI
python tui.py
```

## Domain B: Frontend (Angular)

**Location**: `frontend/`
**Purpose**: Web interface for tunnel control and monitoring

### Key Files
- `src/app/app.ts` - Main application component
- `src/app/services/api.service.ts` - API communication
- `src/app/services/fingerprint.service.ts` - Browser fingerprinting
- `src/styles.scss` - Global grey/black theme

### Build & Run
```bash
# Build for production (outputs to ../src/public)
cd frontend
ng build

# Development server
ng serve

# Build for Cloudflare Worker
npm run build
```

### Features
- SSH tunnel status display
- Start/Stop controls
- Real-time log viewer
- User fingerprinting (Canvas + Audio + Hardware)
- IP address tracking
- Responsive design (media queries)
- Minimalist grey/black theme

## Domain C: Cloudflare Worker

**Location**: `src/`
**Purpose**: Serves frontend assets, stores data in D1

### Important
This directory contains the original Cloudflare boilerplate. Keep changes here minimal to ensure compatibility with upstream updates.

## Common Tasks

### Starting Development
1. **Backend**: `cd backend && python app.py`
2. **Frontend**: `cd frontend && ng serve`
3. **Worker**: `npm run dev`

### Building for Production
```bash
# Build frontend (outputs to src/public)
cd frontend && ng build

# Deploy worker
npm run deploy
```

### Log Management
- Logs are stored in `~/.cloudfared-tunneling/logs/`
- Maximum size: 50MB (5 files × 10MB)
- Rotation is automatic via Python RotatingFileHandler

## Environment Variables

Create `.env` in project root:
```bash
TUNNEL_SECRET=your_secret_here
FLASK_ENV=development
```

## Troubleshooting

### Backend won't start
- Check if port 5000 is available
- Ensure cloudflared is installed: `which cloudflared`

### Frontend build fails
- Run `npm install` in frontend directory
- Check TypeScript errors: `ng build`

### Worker deployment issues
- Ensure wrangler is authenticated: `npx wrangler login`
- Check D1 database exists
