# Non-Functional Requirements

## NFR-1: Performance

| Metric | Requirement | Acceptance Criteria |
|---|---|---|
| API response time (P95) | < 500ms for standard CRUD | Measured on demo hardware |
| AI classification latency | < 5 seconds | From submission to classification complete |
| Risk score computation | < 2 seconds per grievance | Background task metric |
| Dossier generation | < 3 seconds | From request to structured output |
| SLA monitoring cycle | < 60 seconds full scan | All active grievances checked |
| Dashboard page load | < 2 seconds | Initial load with data |
| Concurrent users (MVP) | 10 simultaneous | Demo scenario |
| Database query time (P95) | < 100ms | With proper indexing |

## NFR-2: Reliability

| Metric | Requirement |
|---|---|
| API uptime (demo) | 99% during demonstration |
| Data durability | No data loss on normal shutdown |
| Background task recovery | Celery tasks resume after worker restart |
| Error handling | All errors return structured JSON responses |
| Graceful degradation | If AI service fails, grievance is created with manual classification flag |

## NFR-3: Security

See [SECURITY.md](file:///d:/SARA/docs/architecture/SECURITY.md) for detailed architecture.

| Requirement | Priority |
|---|---|
| JWT-based authentication | 🔴 Mandatory |
| RBAC on all endpoints | 🔴 Mandatory |
| Input validation (Pydantic) | 🔴 Mandatory |
| Prompt injection protection | 🔴 Mandatory |
| SQL injection prevention (parameterized queries) | 🔴 Mandatory |
| XSS prevention (input sanitization) | 🔴 Mandatory |
| Secure file upload (MIME whitelist, size limits) | 🔴 Mandatory |
| Password hashing (bcrypt) | 🔴 Mandatory |
| HTTPS (TLS) | 🟠 Required for production (HTTP for local dev) |
| Rate limiting | 🟡 Recommended for MVP |
| Encryption at rest | 🟡 Post-MVP |
| CSRF protection | 🟡 Post-MVP (SPA with JWT) |

## NFR-4: Scalability

| Aspect | MVP Design | Future Design |
|---|---|---|
| Architecture | Modular monolith | Decompose to microservices if needed |
| Database | Single PostgreSQL instance | Read replicas, sharding |
| Background tasks | Single Celery worker | Multiple workers, queue partitioning |
| File storage | Local filesystem | S3-compatible object storage |
| Caching | Redis for hot data | Redis cluster |
| Multi-tenancy | Architecture-ready (tenant fields) | Full tenant isolation |

## NFR-5: Maintainability

| Requirement | Implementation |
|---|---|
| Code structure | Modular with clear separation of concerns |
| Type safety | TypeScript (frontend), Python type hints (backend) |
| API documentation | Auto-generated OpenAPI/Swagger via FastAPI |
| Database migrations | Alembic with versioned migration files |
| Configuration | Environment variables, no hardcoded values |
| Logging | Structured JSON logging with request IDs |
| Error messages | User-facing messages separate from internal errors |

## NFR-6: Usability

| Requirement | Details |
|---|---|
| Dashboard responsiveness | Functional on desktop (1280px+); responsive is post-MVP |
| Loading states | All async operations show loading indicators |
| Error states | User-friendly error messages with recovery guidance |
| Empty states | Meaningful empty states ("No grievances yet") |
| Navigation | Role-based navigation (citizen sees citizen nav, officer sees officer nav) |
| Accessibility | Basic semantic HTML; full WCAG compliance is post-MVP |

## NFR-7: Auditability

| Requirement | Details |
|---|---|
| Event logging | Every state transition creates immutable event record |
| Audit logging | Every admin/system action creates audit log entry |
| Log integrity | Append-only tables, no UPDATE/DELETE |
| Log retention | Indefinite for MVP |
| Log access | Supervisors (department), Admins (all) |

## NFR-8: Observability

| Requirement | MVP Implementation |
|---|---|
| Application logging | Python `logging` module with structured output |
| Request logging | FastAPI middleware logs method, path, status, duration |
| Background task logging | Celery task logging with task IDs |
| Health check endpoint | `GET /api/v1/health` returns system status |
| Error tracking | Structured error logs with stack traces (not exposed to users) |

## NFR-9: Deployment

| Requirement | Details |
|---|---|
| Containerization | All services Dockerized |
| Orchestration | Docker Compose for MVP |
| Single-command startup | `docker-compose up` starts entire stack |
| Environment configuration | `.env` file with all configurable parameters |
| Database initialization | Auto-migration on startup |
| Seed data | Configurable seed script for demo data |

## NFR-10: Testing

| Level | Coverage Target | Implementation |
|---|---|---|
| Unit tests | Core business logic (state machine, governance engine) | pytest |
| Integration tests | API endpoints with database | pytest + httpx |
| AI model evaluation | Classification accuracy, risk score correctness | Custom evaluation scripts |
| End-to-end test | Primary demo scenario | Script or manual |
| Security test | RBAC enforcement, input validation | Targeted test cases |
