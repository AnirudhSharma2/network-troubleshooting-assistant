# Network Troubleshooting Assistant

A full-stack troubleshooting workbench for Cisco Packet Tracer labs. It analyzes pasted CLI captures with a **deterministic rule engine**, evidence coverage scoring, root-cause prioritization, and guided learning content.

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
│ Auth (JWT) │ Rules │ Evidence │ Fix Planner │
│ Learning   │ PDF Reports │ Admin APIs      │
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
python -m pytest tests -q
```

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, React Router v6, Axios |
| Backend | Python, FastAPI, Pydantic |
| Database | SQLite (via SQLAlchemy) |
| Auth | JWT (python-jose + bcrypt) |
| Learning/Scenarios | Offline template provider (no paid API required) |
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

### 2. Evidence Coverage + Health Scoring
The analyzer reports how complete the capture is and how confident the result should be:
- Detects whether `show running-config`, `show ip interface brief`, `show ip route`, and `show vlan brief` are present
- Recommends the next commands to collect when evidence is incomplete
- Supports combined multi-device captures in a single analysis

Weighted health categories:
- **Routing**: 30%
- **Interface**: 25%
- **VLAN**: 25%
- **IP**: 20%

Severity deductions: Critical (−15), High (−10), Medium (−5), Low (−2)

### 3. Deterministic Troubleshooting Copilot
- Prioritized fix plan that orders root-cause repairs ahead of secondary symptoms
- Parsed scope summary showing how many devices, interfaces, routes, and VLANs were seen
- Learning mode that explains why each fix works without relying on a paid model

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
| Troubleshoot | `/troubleshoot` | Paste multi-device CLI output/config → analyze → see evidence, fix order, and issues |
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
2. **Configuration-based analysis** — Users paste CLI output manually from Packet Tracer
3. **Best results come from complete captures** — Missing commands reduce confidence
4. **Learning/scenario content is offline** — No paid API keys are required
5. **SQLite** — Zero-config database, suitable for demos

## 🔮 Future Enhancements

- Stronger rule coverage for ACL, NAT, DHCP, STP, and EtherChannel
- Cross-device path validation and reciprocal-route checks
- Network topology visualization (D3.js/Cytoscape)
- WebSocket real-time analysis
- Automated grading for lab exercises
