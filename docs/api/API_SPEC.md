# API Specification

## Base URL

```
/api/v1
```

## Authentication

All endpoints except `/auth/register` and `/auth/login` require a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

## Standard Response Format

### Success
```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO-8601"
  }
}
```

### Error
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [ ... ]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO-8601"
  }
}
```

### Pagination
```json
{
  "status": "success",
  "data": [ ... ],
  "meta": {
    "total": 150,
    "page": 1,
    "per_page": 20,
    "total_pages": 8
  }
}
```

---

## Auth Endpoints

### POST /auth/register
Create a new citizen account.

| Field | Type | Required | Notes |
|---|---|---|---|
| email | string | ✅ | Valid email format |
| password | string | ✅ | Min 8 chars, mixed case + digit |
| full_name | string | ✅ | Max 255 chars |
| phone | string | ❌ | |

**Response**: 201 Created → `{ user, access_token, refresh_token }`
**Errors**: 409 (duplicate email), 422 (validation)

### POST /auth/login
**Body**: `{ email, password }`
**Response**: 200 → `{ user, access_token, refresh_token }`
**Errors**: 401 (invalid credentials), 403 (disabled account)

### POST /auth/refresh
**Body**: `{ refresh_token }`
**Response**: 200 → `{ access_token, refresh_token }`

### GET /auth/me
**Auth**: Any authenticated user
**Response**: 200 → `{ user }`

---

## Grievance Endpoints

### POST /grievances
Create a new grievance.

**Auth**: CITIZEN
**Body** (multipart/form-data):
| Field | Type | Required | Notes |
|---|---|---|---|
| description | string | ✅ | Max 5000 chars |
| location_text | string | ❌ | |
| latitude | float | ❌ | |
| longitude | float | ❌ | |
| files | File[] | ❌ | Max 5, max 10MB each, MIME whitelist |

**Response**: 201 → `{ grievance }` (with status SUBMITTED, reference_number)

### GET /grievances
List grievances (filtered by role).

**Auth**: All roles (scoped)
**Query params**:
| Param | Type | Default | Notes |
|---|---|---|---|
| page | int | 1 | |
| per_page | int | 20 | Max 100 |
| status | string | - | Filter by status |
| priority | string | - | Filter by priority |
| department_id | uuid | - | Filter by department (SUPERVISOR, ADMIN) |
| risk_level | string | - | Filter by risk level |
| sort_by | string | created_at | Options: created_at, risk_score, sla_deadline, priority |
| sort_order | string | desc | asc or desc |

**Scoping**:
- CITIZEN: own grievances only
- OFFICER: assigned grievances only
- SUPERVISOR: department grievances
- ADMIN: all grievances

**Response**: 200 → `{ grievances[], meta }`

### GET /grievances/{id}
Get grievance detail.

**Auth**: Scoped (own/assigned/dept/all)
**Response**: 200 → `{ grievance, events[], evidence[], feedback[], risk_score }`
**Errors**: 404 (not found or unauthorized)

### PATCH /grievances/{id}/status
Update grievance status (state machine transition).

**Auth**: Role-dependent (see state machine)
**Body**:
```json
{
  "status": "ACKNOWLEDGED",
  "remarks": "Will inspect site tomorrow morning"
}
```
**Response**: 200 → `{ grievance }` (updated)
**Errors**: 400 (invalid transition), 403 (unauthorized role)

### POST /grievances/{id}/evidence
Upload evidence for a grievance.

**Auth**: OFFICER (assigned), CITIZEN (own, for supporting docs)
**Body** (multipart/form-data):
| Field | Type | Required |
|---|---|---|
| file | File | ✅ |
| evidence_type | string | ✅ (PHOTO/DOCUMENT/WORK_ORDER/OTHER) |
| description | string | ❌ |

**Response**: 201 → `{ evidence }`

### POST /grievances/{id}/resolve
Submit resolution.

**Auth**: OFFICER (assigned)
**Body**:
```json
{
  "resolution_notes": "Repair completed. Wire insulated and secured.",
  "evidence_ids": ["uuid1", "uuid2"]
}
```
**Validation**: At least 1 evidence file must exist
**Response**: 200 → `{ grievance }` (status → RESOLUTION_SUBMITTED → VERIFICATION)

### POST /grievances/{id}/verify
Citizen verification of resolution.

**Auth**: CITIZEN (own grievance, status must be VERIFICATION)
**Body**:
```json
{
  "is_satisfied": false,
  "comments": "The wire is still exposed",
  "rating": 1
}
```
**Response**: 200 → `{ grievance }` (status → CLOSED or REOPENED)

### POST /grievances/{id}/reassign
Reassign grievance to different officer.

**Auth**: SUPERVISOR, ADMIN
**Body**: `{ officer_id, reason }`
**Response**: 200 → `{ grievance }`

### GET /grievances/{id}/timeline
Get complete event timeline.

**Auth**: Scoped
**Response**: 200 → `{ events[] }` (chronological)

### GET /grievances/{id}/dossier
Get accountability dossier.

**Auth**: SUPERVISOR, ADMIN
**Response**: 200 → `{ dossier }`

### GET /grievances/{id}/duplicates
Get potential duplicate complaints.

**Auth**: OFFICER, SUPERVISOR, ADMIN
**Response**: 200 → `{ duplicates[] }` (with similarity scores)

---

## Dashboard / Analytics Endpoints

### GET /dashboard/citizen
**Auth**: CITIZEN
**Response**: `{ total, active, resolved, pending_verification, recent[] }`

### GET /dashboard/officer
**Auth**: OFFICER
**Response**: `{ assigned_count, high_risk[], sla_warning[], pending_acknowledgment[], stats }`

### GET /dashboard/supervisor
**Auth**: SUPERVISOR
**Response**: `{ escalated[], overdue[], high_risk[], department_stats, sla_breach_count }`

### GET /dashboard/admin
**Auth**: ADMIN
**Response**: `{ total_grievances, by_status, by_department, by_priority, system_health }`

---

## Policy Endpoints

### GET /policies/sla
List SLA policies.
**Auth**: ADMIN

### POST /policies/sla
Create SLA policy.
**Auth**: ADMIN
**Body**: `{ name, description, rules[] }`

### PUT /policies/sla/{id}
Update SLA policy.
**Auth**: ADMIN

### GET /policies/escalation
List escalation policies.
**Auth**: ADMIN

### POST /policies/escalation
Create escalation policy.
**Auth**: ADMIN
**Body**: `{ name, description, levels[] }`

### PUT /policies/escalation/{id}
Update escalation policy.
**Auth**: ADMIN

---

## Department Endpoints

### GET /departments
**Auth**: ADMIN, SUPERVISOR
**Response**: `{ departments[] }`

### POST /departments
**Auth**: ADMIN
**Body**: `{ name, code, description, sla_policy_id, escalation_policy_id }`

### PUT /departments/{id}
**Auth**: ADMIN

---

## User Management Endpoints

### GET /users
**Auth**: ADMIN
**Query**: `{ role, department_id, is_active, page, per_page }`

### POST /users
Create officer/supervisor account.
**Auth**: ADMIN
**Body**: `{ email, password, full_name, role, department_id }`

### PUT /users/{id}
**Auth**: ADMIN

### PATCH /users/{id}/status
Enable/disable user.
**Auth**: ADMIN
**Body**: `{ is_active }`

---

## Notification Endpoints

### GET /notifications
**Auth**: Any authenticated user (own notifications)
**Query**: `{ is_read, page, per_page }`

### GET /notifications/unread-count
**Auth**: Any authenticated user

### PATCH /notifications/{id}/read
Mark notification as read.
**Auth**: Owner only

### PATCH /notifications/read-all
Mark all notifications as read.
**Auth**: Owner only

---

## Audit Endpoints

### GET /audit-logs
**Auth**: SUPERVISOR (department), ADMIN (all)
**Query**: `{ resource_type, resource_id, actor_id, action, start_date, end_date, page, per_page }`

---

## System Endpoints

### GET /health
**Auth**: None (public)
**Response**: `{ status: "healthy", services: { database, redis, celery } }`

---

## Error Codes

| Code | HTTP Status | Description |
|---|---|---|
| VALIDATION_ERROR | 422 | Request body validation failed |
| UNAUTHORIZED | 401 | Missing or invalid authentication |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found (or unauthorized access) |
| CONFLICT | 409 | Duplicate resource (e.g., email) |
| INVALID_TRANSITION | 400 | Invalid state machine transition |
| EVIDENCE_REQUIRED | 400 | Resolution requires evidence |
| FILE_TOO_LARGE | 400 | Upload exceeds size limit |
| FILE_TYPE_INVALID | 400 | Upload MIME type not allowed |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Unexpected server error |
