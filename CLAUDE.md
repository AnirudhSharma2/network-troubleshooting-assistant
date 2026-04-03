# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack network troubleshooting assistant for Cisco Packet Tracer. Users paste Cisco IOS CLI output/configs, and the app runs deterministic rule-based diagnostics — no external AI or API keys required.

**Stack**: React 19 + Vite (frontend, deployed on Vercel) | FastAPI + SQLAlchemy (backend, deployed on Render) | SQLite | JWT auth

## Common Commands

### Backend
```bash
cd backend
pip install -r requirements.txt                    # Install dependencies
uvicorn main:app --reload --port 8000              # Run dev server
python -m pytest tests -q                          # Run all tests
python -m pytest tests/test_engine.py -q           # Run a single test file
python -m pytest tests/test_engine.py -k "test_name" -q  # Run a single test by name
```

### Frontend
```bash
cd frontend
npm install        # Install dependencies
npm run dev        # Start dev server (port 5173)
npm run build      # Production build
npm run lint       # ESLint
```

Note: Frontend has no test suite configured (no Jest/Vitest).

## Architecture

### Core Analysis Pipeline

The central workflow flows through these layers in sequence:

1. **Parser** (`parsers/cisco_parser.py`) — `parse_all(raw_text)` auto-detects single vs. multi-device captures, splits by hostname/prompt/separator, and extracts interfaces, routes, VLANs, interface configs, and router configs per device.

2. **Rule Engine** (`services/rule_engine/`) — `engine.py` orchestrates: parses input via `parse_all()`, then runs all rules from `rules.py`. Each rule returns a list of issue dicts with `{rule, failure_type, device, interface, severity, detail, fix_command}`.

3. **Scoring** (`services/scoring.py`) — `calculate_health_score(issues)` computes a weighted 0–100 score across four categories: Routing (30%), Interface (25%), VLAN (25%), IP (20%). Deductions vary by severity (critical: -15, high: -10, medium: -5, low: -2).

4. **Analysis Assistant** (`services/analysis_assistant.py`) — `build_analysis_artifacts()` produces three artifacts:
   - **Evidence report**: coverage assessment based on which of 4 key commands are present (running-config 35%, interface brief 25%, ip route 20%, vlan brief 20%)
   - **Fix plan**: issues ordered by root-cause priority weight (duplicate IP=100 down to missing route=70)
   - **Insights**: educational bullet points

5. **Analysis Router** (`routers/analysis.py`) — `POST /api/analysis` ties it all together: parse → rules → score → artifacts → persist to DB → return response.

### Parser Multi-Device Detection

The parser (`parsers/cisco_parser.py`) tries three strategies in order to split multi-device captures:
1. **Hostname blocks** — looks for `hostname X` config keywords
2. **Prompt patterns** — extracts device names from CLI prompts (e.g., `R1#`, `SW1>`)
3. **Separator blocks** — splits on `---` or `===` delimiters

If none match, input is treated as a single device. All per-device parsing uses the same extraction functions for interfaces, routes, VLANs, interface configs, and router configs.

### Rule Engine Conventions

Rules live in `services/rule_engine/rules.py` and are registered in the `ALL_RULES` list. Each rule function:
- Takes a `parsed` dict (output of `parse_all()`)
- Uses `_iter_device_views(parsed)` to iterate uniformly over single or multi-device data
- Returns a list of issue dicts with keys: `rule`, `failure_type`, `device`, `interface`, `severity`, `detail`, `fix_command`

Current rules (8): `check_interface_status`, `check_missing_routes`, `check_default_gateway`, `check_wrong_subnet`, `check_vlan_mismatch`, `check_trunk_access`, `check_duplicate_ip`, `check_physical_link`.

### AI Provider Layer

`services/ai/` has an abstract `AIProvider` base class with a mock implementation. The mock provider uses templates — no API keys needed. The factory in `factory.py` returns the active provider based on `AI_PROVIDER` config setting.

### Authentication

JWT-based with role hierarchy: `student`, `engineer`, `admin`. Auth service in `services/auth.py` provides `get_current_user` (FastAPI dependency) and `require_role(*roles)` factory. Tokens stored in localStorage on the frontend via `AuthContext`.

### API Endpoints

Six routers registered in `main.py`:
- **`/api/auth`** — register, login, get current user
- **`/api/analysis`** — run analysis (POST), list/get analyses, learning content
- **`/api/scenarios`** — generate practice scenarios, list/get
- **`/api/reports`** — PDF export per analysis (ReportLab)
- **`/api/dashboard`** — user stats, health trend, error summary
- **`/api/admin`** — user management, system analytics (admin-only)

### Frontend

`App.jsx` defines routes. Protected routes use a `ProtectedLayout` wrapper (Sidebar + TopBar). The main analysis UI is `TroubleshootPage.jsx` — it posts raw CLI text to `/api/analysis` and renders results. API calls go through `services/api.js` (Axios with JWT interceptor).

Request/response schemas are defined in `backend/schemas/__init__.py` (Pydantic models for all endpoints).

Frontend API base URL defaults to `${window.location.hostname}:8000/api`, overridable via `VITE_API_URL` env variable.

### Database

SQLite with SQLAlchemy ORM. Three models: `User`, `Analysis`, `Scenario`. Tables auto-created on startup via `init_db()` in the FastAPI lifespan handler (`database.py`).

## Configuration

Backend settings are in `config.py` using Pydantic Settings (loaded from environment variables). Key settings: `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM` (HS256), `JWT_EXPIRATION_MINUTES` (1440), `AI_PROVIDER` (default "mock"), `CORS_ORIGINS`, `PORT`.

## Deployment

- **Backend**: Render (`render.yaml`) — Python 3.11, uvicorn
- **Frontend**: Vercel (`vercel.json`) — SPA rewrite rules
