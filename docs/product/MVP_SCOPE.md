# MVP Scope

## MVP Objective

Demonstrate the complete SARA accountability lifecycle end-to-end, proving that SARA is a credible, differentiated layer on top of existing grievance systems.

> The MVP must prove one thing clearly: **SARA can detect when a grievance is failing, explain why, escalate through policy, verify resolution through evidence, and maintain a complete audit trail — all in a way that existing systems do not.**

## What the MVP Must Prove

| # | Capability | Proof |
|---|---|---|
| 1 | Citizen submits grievance | Working submission form with description, location, optional media |
| 2 | AI classifies it | Category + confidence score displayed |
| 3 | AI determines priority/risk | Priority level + risk score with explanation |
| 4 | System routes it | Correct department assigned via routing rules |
| 5 | Officer receives it | Officer dashboard shows assigned case with AI summary |
| 6 | SLA starts | Countdown timer visible, SLA deadline set by policy |
| 7 | Officer activity is monitored | Risk score updates based on inactivity |
| 8 | SARA detects delay/risk | Risk score increases, timeline shows detection events |
| 9 | Reminder is generated | Officer receives reminder notification |
| 10 | Escalation occurs according to policy | Supervisor receives escalation with accountability dossier |
| 11 | Officer submits resolution evidence | Evidence upload (photos/docs) with resolution notes |
| 12 | Citizen verifies/rejects | Citizen sees evidence and confirms or rejects |
| 13 | Complaint closes or reopens | State transitions correctly based on citizen response |
| 14 | Complete audit trail exists | Every event logged with timestamp, actor, state change |
| 15 | Supervisor can inspect accountability dossier | Structured dossier with complete case intelligence |

## MVP Scope — IN

### Core Backend
- [x] FastAPI project structure with modular architecture
- [x] PostgreSQL database with schema migrations
- [x] JWT-based authentication with RBAC (4 roles)
- [x] RESTful API for all core operations
- [x] Background task processing (Celery + Redis)

### Grievance Lifecycle
- [x] Grievance CRUD (create, read, update, list, detail)
- [x] 7-state grievance lifecycle + governance/SLA/escalation events
- [x] Immutable event log for every state transition
- [x] Assignment workflow (auto-routing + manual reassignment)

### AI Engine
- [x] Text classification (category prediction with confidence)
- [x] Priority assessment (multi-signal urgency scoring)
- [x] Risk score computation (Accountability Risk Score 0–100 with explanation)
- [x] Basic summarization (complaint summary for officer view)
- [x] Semantic duplicate detection (vector similarity for complaint clustering)

### Governance Engine
- [x] Configurable SLA policies (per department/priority)
- [x] SLA monitoring with warning/breach detection
- [x] Configurable escalation policies (rules-based, not AI-based)
- [x] Automated reminder system
- [x] Escalation trigger engine

### Resolution Verification
- [x] Evidence upload (image/document with metadata)
- [x] VERIFICATION workflow state
- [x] Citizen confirmation/rejection workflow
- [x] Rejection → REOPENED state transition

### Accountability
- [x] Accountability dossier generation (structured case report)
- [x] Complete audit trail (immutable, append-only)
- [x] Explainable risk scores (factor-by-factor breakdown)

### Dashboards (React + TypeScript)
- [x] Citizen dashboard: submit, track, verify/reject
- [x] Officer dashboard: queue, AI summary, SLA countdown, evidence upload
- [x] Supervisor dashboard: escalations, dossiers, department overview
- [x] Admin dashboard: user/department/policy management (basic)

### Security
- [x] Input validation and sanitization
- [x] RBAC authorization on all endpoints
- [x] Secure file upload
- [x] Prompt injection protection (input sanitization before AI)
- [x] Secrets management (environment variables)

### Demo
- [x] Synthetic dataset (realistic Indian grievance scenarios)
- [x] Primary demo scenario: exposed wire near school (end-to-end)
- [x] Time Simulation: secure fast-forward mode for demo/admin only (preserves audit integrity)

## MVP Scope — OUT (Post-MVP)

| Feature | Reason for Exclusion |
|---|---|
| Multi-tenancy | Architecture-ready but not implemented in MVP |
| Real external system integration | Simulated adapters only; real CPGRAMS API requires NIC authorization |
| Multilingual support | Valuable but not core to accountability demo |
| Voice-based input | Valuable but not core to accountability demo |
| Maps integration | Can add later; location stored as text/coordinates |
| Email/SMS notifications | In-app notifications only for MVP |
| Advanced analytics / BI dashboards | Basic metrics only; deep analytics is post-MVP |
| Mobile-responsive design | Desktop-first for demo; responsive is post-MVP |
| Blockchain audit trail | Unnecessary complexity; append-only DB logs suffice |
| Microservices architecture | Monolithic-modular for MVP; decompose if scaling requires |
| Load testing / performance optimization | Functional correctness first |
| CI/CD pipeline | Local development + Docker for MVP |
| Kubernetes / cloud deployment | Docker Compose for MVP |
| Officer performance scoring | Risk area (AI judging humans); out of scope |
| Anomaly detection (officer behavior) | MVP focuses on case-level, not officer-level anomalies |

## Primary Demo Scenario

### Complaint

> "There is an exposed electrical wire near a school entrance. Children are passing through the area and it has been like this since yesterday."

### Expected Demo Flow (5–7 minutes)

1. **Citizen submits** complaint via web form
2. **AI classifies**: Category = Electrical Safety (0.94 confidence), Priority = CRITICAL
3. **System routes**: Electrical Department, Officer assigned
4. **SLA starts**: 4-hour countdown displayed
5. **Simulate time passing**: No officer action (secure demo fast-forward)
6. **Risk score rises**: 45 → 62 → 78 → 91
7. **Reminders generated**: Visible in officer notification log
8. **SLA breach / policy trigger**: Escalation to supervisor
9. **Supervisor sees**: Accountability dossier with complete timeline
10. **Officer submits resolution**: Uploads photo evidence
11. **Citizen rejects**: "No — the wire is still exposed"
12. **Complaint reopens**: State → REOPENED, new escalation
13. **Supervisor receives**: Updated dossier with citizen rejection
14. **Audit trail**: Every single event visible with timestamps

### Demo Impact Statement

> "In the current system, this CRITICAL safety complaint could be marked as 'resolved' without evidence and without the citizen's confirmation. SARA prevented premature closure, detected 3.5 hours of inaction, escalated to the supervisor with a complete accountability dossier, and when the citizen rejected a false resolution, automatically reopened the case. Every step is auditable."

## Technical Constraints for MVP

| Constraint | Decision | Rationale |
|---|---|---|
| Database | PostgreSQL | Relational integrity, pgvector support, production-grade |
| Backend framework | FastAPI (Python) | Async, typed, auto-docs, AI ecosystem compatibility |
| Frontend framework | React + TypeScript | Type safety, component ecosystem, SIH presentation quality |
| Styling | Tailwind CSS | Rapid prototyping, consistent design system |
| AI models | scikit-learn + sentence-transformers | Local inference, no API dependency, fast enough for demo |
| LLM (summarization) | Gemini API / local Ollama model | Placed behind an interface for provider swapping; clear input/output logging |
| Background tasks | Celery + Redis | SLA monitoring, risk score computation, reminders |
| Deployment | Docker Compose | Single-command deployment for demo |
| Auth | JWT + bcrypt | Standard, secure, stateless |

## Success Criteria for MVP

| Criteria | Metric |
|---|---|
| End-to-end demo completes | All 15 capabilities demonstrated without errors |
| AI classification accuracy | >85% on synthetic test set |
| Risk score explainability | Every score shows factor breakdown |
| SLA detection | 100% of breaches detected within 1 minute |
| Escalation accuracy | 0 false escalations in demo scenario |
| Audit completeness | Every state transition has an event record |
| Resolution verification | Citizen can confirm or reject; rejection reopens case |
| Dossier generation | Supervisor sees complete structured dossier |
| Security | No unauthenticated access to protected endpoints |
| Demo time | Complete primary scenario in 3–5 minutes |
