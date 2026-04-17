# Network Troubleshooting Assistant

A full-stack web application that diagnoses Cisco Packet Tracer network misconfigurations from pasted CLI output. Rule-based, deterministic, and educational — no external AI or API keys required.

**Live Demo:** [Frontend (Vercel)](https://netassist-debug-fyp.vercel.app) | [Backend API (Railway)](https://netassist-api-production.up.railway.app)

---

## Architecture

```
                         +------------------+
                         |     Browser      |
                         |  React 19 + Vite |
                         +--------+---------+
                                  |
                            HTTPS + JWT
                                  |
                         +--------v---------+
                         |     FastAPI       |
                         |     Backend       |
                         +--------+---------+
                                  |
              +-------------------+-------------------+
              |                   |                   |
     +--------v------+  +--------v------+  +---------v------+
     | Cisco Parser   |  | Rule Engine   |  | Health Scoring |
     | 5 Extractors   |  | 8 Rules       |  | 0-100 Score    |
     | Multi-device   |  | 12 Failure    |  | 4 Categories   |
     | Auto-detect    |  | Types         |  | Severity-based |
     +----------------+  +---------------+  +----------------+
              |                   |                   |
              +-------------------+-------------------+
                                  |
                    +-------------v--------------+
                    |   Analysis Assistant        |
                    |   Evidence Coverage         |
                    |   Priority Fix Plan         |
                    |   Contextual Insights       |
                    +-------------+--------------+
                                  |
              +-------------------+-------------------+
              |                   |                   |
     +--------v------+  +--------v------+  +---------v------+
     | Mock AI        |  | SQLite DB     |  | PDF Reports    |
     | Explanations   |  | Users         |  | ReportLab      |
     | Analogies      |  | Analyses      |  | Viva-ready     |
     | Scenarios      |  | Scenarios     |  | Documents      |
     +----------------+  +---------------+  +----------------+
```

---

## Features

### Core Diagnosis
- **Cisco CLI Parser** — Parses `show ip interface brief`, `show ip route`, `show vlan brief`, running-config interface blocks, and router config blocks
- **Multi-Device Detection** — Automatically splits combined captures from multiple routers/switches using hostname blocks, CLI prompts, or `---` separators
- **8 Diagnostic Rules** — Detects interface shutdown, protocol down, missing routes, missing default gateway, wrong subnet mask, VLAN mismatch, trunk/access contradiction, duplicate IP, and physical link failure
- **Health Scoring (0-100)** — Weighted across 4 categories: Routing (30%), Interface (25%), VLAN (25%), IP (20%)

### Intelligence
- **Evidence Coverage Assessment** — Measures which key Cisco commands were captured, computes a confidence score, recommends what to capture next
- **Priority Fix Plan** — Issues ranked using OSI-layer-aware logic (fix Layer 1 before Layer 3), with exact Cisco IOS fix commands
- **Educational Explanations** — Plain-English descriptions, networking concept names, why-fix-works reasoning, and real-world analogies for every issue

### Platform
- **Practice Scenarios** — 10+ pre-built broken-network labs across 5 types (routing, VLAN, interface, IP, mixed) and 3 difficulty levels
- **Learning Mode** — Deep-dive educational content per issue with analogies
- **PDF Reports** — Professional diagnostic reports suitable for lab submission and viva
- **Dashboard** — Health score gauge, error trends, analysis history
- **Role-Based Access** — Student, Engineer, Admin roles with JWT authentication
- **Admin Panel** — User management, role assignment, system-wide analytics

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, React Router v6, Axios |
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Database | SQLite + SQLAlchemy ORM |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| PDF | ReportLab |
| AI Layer | Pluggable (Mock provider default, no API key needed) |
| Frontend Hosting | Vercel |
| Backend Hosting | Railway |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API available at `http://localhost:8000` | Swagger docs at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173`

### First Use

1. Open `http://localhost:5173` and register a new account
2. Login and go to the **Troubleshoot** page
3. Paste Cisco CLI output (or click "Load Sample")
4. Click **Analyze** to get diagnosis, health score, and fix plan

---

## Project Structure

```
backend/
  main.py                    # FastAPI app entry point
  config.py                  # Settings via environment variables
  database.py                # SQLAlchemy engine + session + auto-init
  schemas/__init__.py        # All Pydantic request/response models
  models/
    user.py                  # User table (roles: student/engineer/admin)
    analysis.py              # Analysis results storage
    scenario.py              # Practice scenarios
  routers/
    auth.py                  # POST /api/auth/register, /login, GET /me
    analysis.py              # POST /api/analysis, GET list/get/learning
    scenarios.py             # POST /api/scenarios/generate, GET list/get
    reports.py               # GET /api/reports/{id}/pdf
    dashboard.py             # GET /api/dashboard
    admin.py                 # Admin-only user management + analytics
  parsers/
    cisco_parser.py          # CLI text -> structured dict (5 extractors)
  services/
    auth.py                  # JWT + bcrypt + role enforcement
    scoring.py               # Weighted health score (0-100)
    analysis_assistant.py    # Evidence report + fix plan + insights
    report.py                # PDF generation (ReportLab)
    rule_engine/
      engine.py              # Orchestrator (runs all rules)
      rules.py               # 8 diagnostic rules + ALL_RULES registry
    ai/
      base.py                # Abstract AIProvider interface
      factory.py             # Provider factory (returns active provider)
      mock_provider.py       # Template-based explanations (default)
  tests/
    test_engine.py           # 14 tests: parser, rules, scoring
    test_assistant.py        # 3 tests: evidence, fix plan, multi-device

frontend/
  src/
    App.jsx                  # Route definitions
    main.jsx                 # React entry point
    context/AuthContext.jsx  # JWT state management
    services/api.js          # Axios + JWT interceptor
    components/Sidebar.jsx   # Role-filtered navigation
    pages/
      LoginPage.jsx          # Auth entry
      RegisterPage.jsx       # New user signup
      DashboardPage.jsx      # Health gauge, stats, recent analyses
      TroubleshootPage.jsx   # MAIN: paste CLI -> analyze -> results
      LearningPage.jsx       # Educational content per issue
      ScenariosPage.jsx      # Practice scenario generator
      HealthPage.jsx         # Detailed score breakdown
      ReportsPage.jsx        # PDF download
      AdminPage.jsx          # User management (admin only)
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | No | Create account |
| `POST` | `/api/auth/login` | No | Login, get JWT |
| `GET` | `/api/auth/me` | Yes | Current user profile |
| `POST` | `/api/analysis` | Yes | Run full diagnosis |
| `GET` | `/api/analysis` | Yes | List user's analyses |
| `GET` | `/api/analysis/{id}` | Yes | Get analysis by ID |
| `GET` | `/api/analysis/{id}/learning` | Yes | Learning content per issue |
| `POST` | `/api/scenarios/generate` | Yes | Generate practice scenario |
| `GET` | `/api/scenarios` | Yes | List scenarios |
| `GET` | `/api/scenarios/{id}` | Yes | Get scenario by ID |
| `GET` | `/api/reports/{id}/pdf` | Yes | Download PDF report |
| `GET` | `/api/dashboard` | Yes | User stats and trends |
| `GET` | `/api/admin/users` | Admin | List all users |
| `PUT` | `/api/admin/users/{id}/role` | Admin | Change user role |
| `DELETE` | `/api/admin/users/{id}` | Admin | Delete user |
| `GET` | `/api/admin/analytics` | Admin | System-wide stats |
| `GET` | `/api/health` | No | Health check |

---

## Diagnostic Rules

| # | Rule | Detects | Severity |
|---|---|---|---|
| 1 | `check_interface_status` | Admin shutdown, protocol down, interface down | High / Critical |
| 2 | `check_missing_routes` | Network on interface but no matching route | High |
| 3 | `check_default_gateway` | Missing 0.0.0.0/0 default route | Medium |
| 4 | `check_wrong_subnet` | /32 mask on LAN, invalid IP/mask | High / Critical |
| 5 | `check_vlan_mismatch` | Port on non-existent VLAN, missing native VLAN | High / Medium |
| 6 | `check_trunk_access` | Access mode with trunk config or vice versa | High / Medium |
| 7 | `check_duplicate_ip` | Same IP on multiple interfaces | Critical |
| 8 | `check_physical_link` | Serial/Ethernet with IP but down/down | Critical |

---

## Health Scoring

| Category | Weight | Failure Types |
|---|---|---|
| Routing | 30% | missing_route, no_default_gateway |
| Interface | 25% | interface_admin_down, interface_protocol_down, interface_down, physical_link_down |
| VLAN | 25% | vlan_not_exists, native_vlan_not_exists, trunk_access_mismatch |
| IP | 20% | wrong_subnet_mask, invalid_ip_config, duplicate_ip |

**Severity deductions per issue:** Critical (-15), High (-10), Medium (-5), Low (-2)

**Grades:** 90+ Excellent | 70-89 Good | 50-69 Fair | 30-49 Poor | <30 Critical

---

## Running Tests

```bash
cd backend
python3 -m pytest tests -v        # All 17 tests
python3 -m pytest tests -k "test_duplicate_ip" -q  # Single test
```

```bash
cd frontend
npm run build     # Production build
npm run lint      # ESLint check
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./network_troubleshooter.db` | SQLAlchemy database URL |
| `JWT_SECRET_KEY` | *(change in prod)* | JWT signing secret |
| `JWT_EXPIRATION_MINUTES` | `1440` | Token lifetime (24h) |
| `AI_PROVIDER` | `mock` | AI backend (`mock` = no API key needed) |
| `CORS_ORIGINS` | `["http://localhost:5173", ...]` | Allowed frontend origins |
| `ADMIN_BOOTSTRAP_KEY` | `None` | Set to enable admin promotion endpoint |
| `PORT` | `8000` | Server port |

### Frontend

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://{hostname}:8000/api` | Backend API base URL |

---

## Deployment

### Backend (Railway)

- Python 3.11 runtime with Uvicorn
- Set `JWT_SECRET_KEY`, `CORS_ORIGINS`, and `PORT` in Railway variables
- Auto-deploys from GitHub push to master

### Frontend (Vercel)

- Static SPA with rewrite rules (`vercel.json`)
- Set `VITE_API_URL` to Railway backend URL in Vercel environment
- Auto-deploys from GitHub push to master

---

## User Roles

| Role | Access |
|---|---|
| **Student** | Troubleshoot, Learning, Scenarios, Reports, Dashboard |
| **Engineer** | All student features |
| **Admin** | All features + User Management + System Analytics |

First registered user is auto-promoted to admin on server startup.

---

## Sample Input

Paste this into the Troubleshoot page to test:

```
hostname R1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 shutdown
!
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
R1#show ip interface brief
Interface            IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0   192.168.1.1     YES manual administratively down down
GigabitEthernet0/1   192.168.1.1     YES manual up                    up
Serial0/0/0          10.0.0.1        YES manual down                  down
!
R1#show ip route
Gateway of last resort is not set
C    192.168.1.0/24 is directly connected, GigabitEthernet0/1
```

**Expected result:** 5 issues detected (admin shutdown, duplicate IP, physical link down, interface down, no default gateway), health score ~55/100.

---

## Assumptions

1. **No real-time packet sniffing** — Cisco Packet Tracer has no API for live data export
2. **Configuration-based analysis** — Users paste CLI output manually from Packet Tracer terminal
3. **Best results from complete captures** — Missing commands reduce evidence confidence
4. **Learning/scenario content is offline** — No paid API keys required for any feature
5. **SQLite database** — Zero-config, suitable for demos and classroom use

---

## Future Enhancements

- Network topology visualization (D3.js / React Flow)
- Cross-device path validation and reciprocal-route checks
- Real AI chatbot integration (Claude/Gemini) for conversational troubleshooting
- ACL, NAT, DHCP, STP, and EtherChannel rule coverage
- Interactive fix simulator with command validation
- Gamified learning with XP, badges, and leaderboards
- Diff-based before/after analysis comparison

---

## License

This project is developed for educational purposes as part of a Final Year Project.
