# Network Troubleshooting Assistant — Packet Tracer MCP Server

An intelligent, full-stack web application for diagnosing and troubleshooting Cisco Packet Tracer network configurations. Features a **deterministic rule-based diagnostic engine** with AI-assisted explanations.

## 🏗 Architecture

```
┌─────────────────────────────────────────────┐
│           Frontend (React + Vite)            │
│  Dashboard │ Troubleshoot │ Learning Mode   │
│  Scenarios │ Health Score │ Reports │ Admin  │
└─────────────────┬───────────────────────────┘
                  │ REST API (HTTP/JSON)
┌─────────────────▼───────────────────────────┐
│            Backend (FastAPI)                 │
│  Auth (JWT) │ Rule Engine │ Scoring System  │
│  AI Layer   │ PDF Reports │ Admin APIs      │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│            SQLite Database                   │
│  Users │ Analyses │ Scenarios                │
└─────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

### Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

Backend runs at **http://localhost:8000** (API docs at /docs).

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**.

### Run Tests

```bash
cd backend
python tests/test_engine.py
```

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, React Router v6, Axios |
| Backend | Python, FastAPI, Pydantic |
| Database | SQLite (via SQLAlchemy) |
| Auth | JWT (python-jose + bcrypt) |
| AI | Pluggable abstraction (Mock provider included) |
| Reports | ReportLab (PDF generation) |

## 🔧 Core Features

### 1. Rule-Based Diagnostic Engine
Detects 8 categories of network issues:
- Interface shutdown / admin down / protocol down
- Missing routes / no default gateway
- Wrong subnet masks / invalid IP configs
- VLAN mismatches / non-existent VLANs
- Trunk/Access port misconfiguration  
- Duplicate IP addresses
- Physical link failures (simulated)

### 2. Health Scoring System (0–100)
Weighted categories:
- **Routing**: 30%
- **Interface**: 25%
- **VLAN**: 25%
- **IP**: 20%

Severity deductions: Critical (−15), High (−10), Medium (−5), Low (−2)

### 3. AI Abstraction Layer
- **Mock Provider**: Template-based explanations — no API key needed
- Pluggable architecture for OpenAI/Gemini integration
- AI used only for explanations and scenarios, never for core diagnosis

### 4. Scenario Generator
Pre-built practice scenarios across:
- Routing failures (easy/medium/hard)
- VLAN mismatches
- Interface problems
- IP misconfigurations
- Mixed multi-issue scenarios

### 5. PDF Report Generation
Professional reports with:
- Health score summary
- Issue table + details
- Fix commands
- Suitable for viva submission

## 📄 Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Health gauge, recent analyses, error summary |
| Troubleshoot | `/troubleshoot` | Paste config → analyze → see issues + fixes |
| Learning Mode | `/learn` | Why fixes work, concepts, analogies |
| Scenarios | `/scenarios` | Generate broken network practice labs |
| Health Score | `/health` | Weighted category breakdown |
| Reports | `/reports` | Download PDF reports |
| Admin | `/admin` | User management (admin only) |

## 👥 Roles

| Role | Access |
|------|--------|
| Student | Troubleshooting, Learning, Scenarios, own Reports |
| Engineer | All Student + advanced features |
| Admin | All + User management + Global analytics |

## 📋 API Endpoints

- `POST /api/auth/register` — Register user
- `POST /api/auth/login` — Login
- `GET /api/auth/me` — Current user
- `POST /api/analysis` — Run analysis
- `GET /api/analysis` — List analyses
- `GET /api/analysis/{id}` — Get analysis details
- `GET /api/analysis/{id}/learning` — Learning content
- `POST /api/scenarios/generate` — Generate scenario
- `GET /api/scenarios` — List scenarios
- `GET /api/reports/{id}/pdf` — Download PDF
- `GET /api/dashboard` — Dashboard data
- `GET /api/admin/users` — List users (admin)
- `PUT /api/admin/users/{id}/role` — Update role (admin)
- `GET /api/admin/analytics` — System analytics (admin)

## ⚠️ Assumptions

1. **No real-time packet sniffing** — Packet Tracer has no API for this
2. **Configuration-based analysis** — Users paste CLI outputs manually
3. **Single-device analysis** — Each analysis processes one device's output
4. **Mock AI provider** — Works without any API keys out of the box
5. **SQLite** — Zero-config database, suitable for demos

## 🔮 Future Enhancements

- Multi-device topology analysis
- Real Packet Tracer file (.pkt) parsing
- OpenAI/Gemini integration for smarter explanations
- Network topology visualization (D3.js/Cytoscape)
- WebSocket real-time analysis
- Export scenarios to .pkt files
- Automated grading for lab exercises
