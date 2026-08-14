# SARA — Smart Accountability & Resolution Assistant

SARA is an AI-powered public grievance accountability and resolution escalation layer. It is built as a complementary layer to interoperable public grievance systems like CPGRAMS.

## Core Features (Roadmap)
- **7-State Grievance Lifecycle**: SUBMITTED, ASSIGNED, IN_PROGRESS, RESOLUTION_SUBMITTED, VERIFICATION, CLOSED, REOPENED.
- **Accountability Risk Scoring**: Deterministic multi-factor scoring engine (0-100).
- **Resolution Integrity Loop**: Pre-closure evidence validation and direct citizen verification (YES/NO).
- **Policy-driven Escalation Engine**: Automated reminders and accountability dossier compilation for supervisor oversight.
- **AI-powered Advisory Services**: Categorization, priority evaluation, semantic duplicate detection (HNSW).

---

## Prerequisites
- Docker & Docker Compose (v2.x recommended)
- Node.js (v18+ recommended)
- Python 3.11+ (local development)

---

## Environment Setup
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Configure settings inside `.env` if necessary.

---

## Local Deployment (Docker Compose)
To spin up all services including Postgres, Redis, the Backend server, and the Celery Worker, run:
```bash
docker-compose up --build -d
```

### Stop Services
```bash
docker-compose down
```

---

## Service Ports
- **FastAPI Backend API**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Frontend Development Server**: [http://localhost:5173](http://localhost:5173)
- **PostgreSQL Database**: `localhost:5432`

---

## Manual Backend Startup
If you want to run the backend locally outside of Docker:
1. Initialize virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```
3. Run migrations:
   ```bash
   alembic upgrade head
   ```
4. Run FastAPI app:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## Manual Frontend Startup
If you want to run the frontend locally:
1. Go to directory and install packages:
   ```bash
   cd frontend
   npm install
   ```
2. Run development server:
   ```bash
   npm run dev
   ```
3. Build for production:
   ```bash
   npm run build
   ```

---

## Running Verification Tests
To run backend unit and integration tests locally:
```bash
cd backend
pytest -v
```
