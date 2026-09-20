# 🚕 Traveo — AI-Powered Shared Ride Platform

> **Not a college project. Not a demo. Not an MVP shortcut.**
> 
> Traveo is a production-grade, AI-powered shared ride platform where **passenger matching happens first, then driver assignment follows.**

---

## 🏗️ Architecture

```
traveo/
├── apps/
│   ├── passenger-app/    # React Native (Expo)
│   └── driver-app/       # React Native (Expo)
├── backend/              # FastAPI (Python 3.11+)
│   ├── app/
│   │   ├── core/         # Config, DB, Security, Logging
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response
│   │   ├── authentication/ # Auth module (Router → Service → Repository)
│   │   ├── middleware/    # Request ID, logging, security headers
│   │   ├── dependencies/  # FastAPI DI (auth, DB session, RBAC)
│   │   └── exceptions/   # Domain exception hierarchy
│   ├── alembic/          # Database migrations
│   └── Dockerfile
├── admin-panel/          # React + Vite + TypeScript (Phase 4)
├── shared/               # Cross-module constants
├── docker/               # Docker Compose
├── nginx/                # Reverse proxy config
├── docs/                 # Architecture documentation
├── scripts/              # Utilities
└── .github/workflows/    # CI/CD
```

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy (async), Pydantic v2 |
| Database | Supabase (PostgreSQL) |
| Cache | Redis |
| Auth | JWT (access + refresh tokens) |
| Payments | Razorpay |
| Maps | Google Maps Platform |
| Notifications | Firebase Cloud Messaging |
| Mobile Apps | React Native (Expo) |
| Admin Panel | React + Vite + TypeScript |
| Proxy | Nginx |
| CI/CD | GitHub Actions |
| Containerization | Docker |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Supabase account (or local instance)

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
cp ../.env.example ../.env
# Edit .env with your Supabase credentials

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

### Docker (Full Stack)

```bash
cd docker
docker compose up -d
```

### API Docs

Once running, visit: `http://localhost:8000/docs`

## 📐 Design Principles

1. **Clean Architecture** — Router → Service → Repository → Database
2. **SOLID** — Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion
3. **Module-by-Module** — Complete one module, test it, then move forward
4. **Configuration over Code** — All operational parameters configurable without redeployment
5. **Security First** — JWT auth, RBAC, rate limiting, security headers, structured logging

## 📋 Development Phases

| Phase | Focus | Status |
|---|---|---|
| 1 | Foundation (Repo, DB, Auth, Docker) | ✅ In Progress |
| 2 | Core Ride Flow (Booking → Matching → Driver → OTP → Ride) | ⬜ |
| 3 | Payments (Razorpay, Wallet, Fare, Ratings) | ⬜ |
| 4 | Operations (Admin Panel, Analytics, Support) | ⬜ |
| 5 | Optimization (AI, Feature Flags, Performance) | ⬜ |

## 📖 Documentation

Detailed specification: [`step_by_step_building_prompt.md`](./step_by_step_building_prompt.md)

## 📜 License

Proprietary. All rights reserved.
