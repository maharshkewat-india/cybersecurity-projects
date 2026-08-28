# Digital Forensics Evidence Management System

A modern web-based platform for managing digital forensic cases, evidence, and chain-of-custody. Built with a FastAPI backend, Next.js frontend, and SQLite for portable local storage.

## ⚠️ Important Disclaimer

This is an **educational and evidence-management** toolkit. It is **NOT** a replacement for:
- Professional forensic disk imaging
- Hardware write blockers
- Validated forensic acquisition software (EnCase, FTK, X-Ways)
- Legal evidence-handling procedures

The application preserves original hashes and provides transparent audit/custody history, but should NOT be used in real legal cases without proper validation and certification.

## Features

### Core Functionality
- **Secure Authentication** - PBKDF2-HMAC-SHA256 password hashing with random salts, JWT-based sessions
- **Role-Based Access Control (RBAC)** - 5 default roles with 20+ granular permissions
- **Case Management** - Create, edit, close, and archive cases
- **Evidence Management** - Register evidence with real file paths (no file copying)
- **MD5 & SHA-256 Hashing** - Chunked streaming hash computation
- **Hash Verification** - Detect file integrity violations
- **Chain of Custody** - Complete custody event tracking with timeline view
- **Investigation Notes** - Analysis notes per case
- **Audit Logging** - Append-only audit trail of all operations
- **User Management** - Admin-controlled user accounts
- **Report Generation** - JSON reports for case summary, evidence, custody, audit
- **Modern Web UI** - Dark-themed, responsive, accessible

### Security
- Passwords hashed with PBKDF2-HMAC-SHA256 (210,000 iterations)
- Random 16-byte salts per user
- JWT tokens (HS256, 7-day expiry) for stateless auth
- SQL injection prevention (parameterized queries)
- Foreign key enforcement
- Permission checks at service layer (not just UI)
- Audit log is append-only from normal UI
- Session management with expiry

## Architecture

```
02 Digital Forensics Evidence Management System/
├── backend/                  # FastAPI backend
│   ├── main.py               # Entry point (uvicorn)
│   ├── app.py                # FastAPI app factory
│   ├── requirements.txt      # Python dependencies
│   ├── api/                  # REST endpoints (auth, cases, evidence, custody, audit, users, reports)
│   ├── auth/                 # PBKDF2 hashing, RBAC, authentication (reused from CLI app)
│   ├── core/                 # JWT security, FastAPI dependencies (RBAC)
│   ├── database/             # SQLite + schema
│   ├── models/               # Data models
│   ├── schemas/              # Pydantic request/response models
│   └── services/             # Business logic (reused from CLI app)
│
├── frontend/                 # Next.js 16 + React 19 + Tailwind CSS 4
│   ├── src/
│   │   ├── app/              # App Router pages (login, dashboard, cases, etc.)
│   │   ├── components/       # UI components (shadcn-style)
│   │   ├── hooks/            # useAuth, etc.
│   │   ├── lib/              # API client, auth, utils
│   │   └── types/            # TypeScript types
│   └── package.json
│
├── legacy/                   # Original Tkinter app (preserved, marked deprecated)
│   ├── app.py                # DEPRECATED
│   ├── launcher.py           # DEPRECATED
│   ├── ui/                   # DEPRECATED
│   └── (database, auth, services, models — copied into backend/)
│
├── demo/                     # Automated demo (CLI)
├── data/                     # SQLite database location
├── tests/                    # Test suite
├── RUN_ME.bat                # Windows launcher (backend + frontend)
├── requirements.txt          # Top-level dependencies overview
└── README.md                 # This file
```

## Installation

### Requirements
- **Python 3.10+** (for FastAPI backend)
- **Node.js 18+** (for Next.js frontend)
- Windows 10/11, macOS, or Linux

### Windows Setup
1. Install Python from [python.org](https://www.python.org/downloads/) (✅ check "Add Python to PATH")
2. Install Node.js from [nodejs.org](https://nodejs.org/)
3. Double-click `RUN_ME.bat`
   - Creates a Python virtual environment
   - Installs backend dependencies
   - Installs frontend dependencies
   - Initializes the database
   - Starts both servers in separate windows
   - Opens your browser to the app

### Manual Setup (any OS)
```bash
# Backend
cd "02 Digital Forensics Evidence Management System"
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r backend/requirements.txt
cd backend && python main.py

# Frontend (in a new terminal)
cd "02 Digital Forensics Evidence Management System/frontend"
npm install
npm run dev
```

## Quick Start

1. **Start the app** via `RUN_ME.bat` (Windows) or manual commands above
2. **Open your browser** to <http://localhost:3000>
3. **Log in** with default credentials:
   - **Username:** `admin`
   - **Password:** `Admin@123`
4. **Explore the dashboard** with statistics and recent activity
5. **Create a case**, register evidence, record custody events, verify hashes
6. **Browse the audit log** to see every action tracked

## Roles & Permissions

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| **ADMINISTRATOR** | Full system access | All permissions |
| **CASE INVESTIGATOR** | Manages cases and evidence | Create/edit cases, register evidence, hash verification |
| **FORENSIC ANALYST** | Analyzes evidence | View cases, hash computation, analysis notes |
| **EVIDENCE CUSTODIAN** | Physical evidence handling | Register evidence, custody events |
| **AUDITOR** | Read-only oversight | View all data, generate reports |

Permission checks happen at the **service/database layer**, not just the UI. Hiding UI buttons is a convenience; the system enforces permissions regardless.

## API Documentation

Once the backend is running, visit:
- **Swagger UI:** <http://localhost:8000/docs>
- **ReDoc:** <http://localhost:8000/redoc>

## Web App Features

### Dashboard
- Real-time statistics: cases, evidence, custody events, audit entries
- Recent cases and recent activity feed
- Permission-gated navigation

### Cases
- Search by title, case number, or description
- Filter by status (Open, Under Investigation, Closed, Archived) and priority
- Sort and paginate large lists
- Create new cases from any page (with `case.create` permission)
- Quick close/archive actions

### Evidence
- Search and filter
- Inline MD5 and SHA-256 display with copy-to-clipboard
- Hash status badges (Active, Verified, Corrupted, Released)
- File size and metadata
- Register new evidence with automatic hash computation

### Chain of Custody
- Vertical timeline view of all custody events
- Filter by evidence item
- Record new events (handoff, secure storage, release)
- Color-coded actions

### Audit Log
- Filter by user, action, date range
- 17+ action types tracked
- Append-only history
- Full description and entity references

### Reports
- Generate case summary, evidence, custody, and audit reports
- JSON output (downloadable)
- Timestamped and attributed

### User Management (admin)
- View all users with roles and permissions
- Create new users with role assignment
- Disable/enable user accounts
- 5 default roles available

## Running the Demo

The automated CLI demo creates a complete end-to-end workflow:
```bash
python demo/demo_flow.py
```

This creates a demo case, registers sample evidence, records custody events, and verifies hashes — all without the web UI.

## Testing

```bash
# Backend tests (service layer)
python -m pytest tests/

# API tests
cd backend && python -m pytest tests/test_api*.py
```

The test suite covers:
- Password hashing (PBKDF2)
- RBAC permission checks
- User registration and authentication
- Hash computation (MD5, SHA-256)
- Hash verification (match and mismatch)
- Case creation
- Evidence registration
- Custody events
- Audit logging
- API endpoints with FastAPI TestClient

## Database

The SQLite database is stored in `data/forensics_framework.db` (auto-created on first run).

### Tables
- `users`, `roles`, `permissions`, `role_permissions`, `user_roles`, `sessions`
- `cases`, `case_users`
- `evidence`, `evidence_hashes`
- `custody_events`, `analysis_notes`
- `audit_logs`, `system_settings`

## Security Notes

- **Passwords** are hashed with PBKDF2-HMAC-SHA256 (210,000 iterations, 16-byte salt)
- **JWT tokens** (HS256) expire after 7 days
- **Original hashes** are NEVER overwritten during verification
- **Audit logs** are append-only from the UI
- **Custody events** cannot be silently edited; corrections require a new event
- **All SQL queries** use parameterized statements (no string concatenation)
- **Foreign keys** are enabled
- **RBAC** enforced at the service layer, not just UI

## Limitations

This application is designed for **educational and portfolio use**. It does NOT:
- Acquire disk images (use FTK Imager, dd, etc.)
- Use hardware write blockers
- Provide legal chain-of-custody certification
- Comply with court admissibility standards (e.g., Daubert, Frye)
- Support enterprise features (LDAP, multi-tenancy, etc.)

For real forensic work, use validated professional tools.

## License

This project is released under the MIT License. See LICENSE for details.

## Acknowledgments

- NIST SP 800-132 (PBKDF2 recommendation)
- NIST FIPS 180-4 (SHA-256)
- RFC 1321 (MD5)
- Common digital forensics principles and best practices
- Next.js, React, FastAPI, shadcn/ui, Radix UI, Tailwind CSS communities

## #### ####  #########  ###############  ##########  ############  ##### ####

## 38 API endpoints across 7 routers:

Auth (4 routes): login, logout, me, refresh
Cases (9 routes): CRUD, close, archive, assign, case users/evidence
Evidence (9 routes): CRUD, verify, hash, notes, custody
Custody (3 routes): list, create
Audit (2 routes): logs, count
Users (7 routes): CRUD, disable/enable, reset password
Reports (1 route): generate case reports
Verified: login returns JWT token with admin permissions, dashboard stats work.

## Frontend (Next.js 16 + Tailwind CSS 4) — ✅ Built
Pages built:

/login — premium dark-themed login with branding and features
/dashboard — stats cards, recent cases, audit activity feed
/cases — searchable, filterable table with create dialog
/evidence — evidence table with inline hash display + copy-to-clipboard
/custody — vertical timeline view of all custody events
/audit — filterable audit log (by user, action, date)
/users — user management with role badges and disable/enable
/reports — report generation with JSON download
Components: Button, Input, Card, Badge, Table, Label, Dialog, Select, Dropdown, Sidebar, Topbar, AuthContext

## Windows Launcher — ✅ Updated
RUN_ME.bat sets up venv, installs deps, initializes DB, and starts both servers in separate windows.

## To Run

cd "02 Digital Forensics Evidence Management System"
RUN_ME.bat
Or manually:


# Backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r backend/requirements.txt
cd backend && python main.py

# Frontend (separate terminal)
cd frontend && npm install && npm run dev

Login: admin / Admin@123