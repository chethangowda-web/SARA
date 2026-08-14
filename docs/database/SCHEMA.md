# Database Schema

## PostgreSQL Configuration

```sql
-- Required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
```

## Enum Types

```sql
CREATE TYPE user_role AS ENUM ('CITIZEN', 'OFFICER', 'SUPERVISOR', 'ADMIN');
CREATE TYPE priority_level AS ENUM ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW');
CREATE TYPE assignment_type AS ENUM ('AUTO', 'MANUAL', 'ESCALATION');
CREATE TYPE evidence_type AS ENUM ('PHOTO', 'DOCUMENT', 'WORK_ORDER', 'OTHER');
CREATE TYPE feedback_type AS ENUM ('VERIFICATION', 'SATISFACTION', 'COMMENT');
CREATE TYPE escalation_status AS ENUM ('PENDING', 'REVIEWED', 'RESOLVED', 'OVERRIDDEN');
CREATE TYPE escalation_action AS ENUM ('SEND_REMINDER', 'ESCALATE');
```

## Table Definitions

```sql
-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role user_role NOT NULL,
    department_id UUID REFERENCES departments(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- DEPARTMENTS
-- ============================================================
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    parent_department_id UUID REFERENCES departments(id),
    sla_policy_id UUID REFERENCES sla_policies(id),
    escalation_policy_id UUID REFERENCES escalation_policies(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- GRIEVANCES
-- ============================================================
CREATE TABLE grievances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_number VARCHAR(50) UNIQUE NOT NULL,
    source_system VARCHAR(100) NOT NULL DEFAULT 'sara_direct',
    external_id VARCHAR(255),
    citizen_id UUID NOT NULL REFERENCES users(id),
    description TEXT NOT NULL,
    category VARCHAR(100),
    category_confidence FLOAT,
    original_category VARCHAR(100),
    priority priority_level,
    priority_score INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'SUBMITTED',
    department_id UUID REFERENCES departments(id),
    assigned_officer_id UUID REFERENCES users(id),
    location_text TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    sla_deadline TIMESTAMPTZ,
    risk_score INTEGER DEFAULT 0,
    risk_level VARCHAR(20),
    is_escalated BOOLEAN NOT NULL DEFAULT false,
    escalation_level INTEGER NOT NULL DEFAULT 0,
    resolution_notes TEXT,
    ai_summary TEXT,
    embedding vector(384),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    reopened_count INTEGER NOT NULL DEFAULT 0
);

-- ============================================================
-- GRIEVANCE EVENTS (Append-only)
-- ============================================================
CREATE TABLE grievance_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grievance_id UUID NOT NULL REFERENCES grievances(id),
    event_type VARCHAR(50) NOT NULL,
    from_state VARCHAR(50),
    to_state VARCHAR(50),
    actor_id UUID REFERENCES users(id),
    actor_role VARCHAR(20),
    metadata JSONB NOT NULL DEFAULT '{}',
    remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Prevent UPDATE/DELETE on events
CREATE RULE no_update_events AS ON UPDATE TO grievance_events DO INSTEAD NOTHING;
CREATE RULE no_delete_events AS ON DELETE TO grievance_events DO INSTEAD NOTHING;

-- ============================================================
-- ASSIGNMENTS
-- ============================================================
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grievance_id UUID NOT NULL REFERENCES grievances(id),
    officer_id UUID NOT NULL REFERENCES users(id),
    assigned_by UUID REFERENCES users(id),
    assignment_type assignment_type NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    unassigned_at TIMESTAMPTZ
);

-- ============================================================
-- EVIDENCE
-- ============================================================
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grievance_id UUID NOT NULL REFERENCES grievances(id),
    uploaded_by UUID NOT NULL REFERENCES users(id),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    evidence_type evidence_type NOT NULL,
    description TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- FEEDBACK
-- ============================================================
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grievance_id UUID NOT NULL REFERENCES grievances(id),
    citizen_id UUID NOT NULL REFERENCES users(id),
    feedback_type feedback_type NOT NULL,
    is_satisfied BOOLEAN,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- ESCALATIONS
-- ============================================================
CREATE TABLE escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grievance_id UUID NOT NULL REFERENCES grievances(id),
    escalation_level INTEGER NOT NULL,
    trigger_reason VARCHAR(100) NOT NULL,
    escalated_to UUID NOT NULL REFERENCES users(id),
    escalated_from UUID REFERENCES users(id),
    risk_score_at_escalation INTEGER NOT NULL,
    risk_explanation JSONB NOT NULL,
    status escalation_status NOT NULL DEFAULT 'PENDING',
    reviewed_at TIMESTAMPTZ,
    reviewer_notes TEXT,
    dossier_id UUID REFERENCES accountability_dossiers(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- ACCOUNTABILITY DOSSIERS
-- ============================================================
CREATE TABLE accountability_dossiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grievance_id UUID NOT NULL REFERENCES grievances(id),
    escalation_id UUID REFERENCES escalations(id),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    content JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);

-- ============================================================
-- RISK SCORES
-- ============================================================
CREATE TABLE risk_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grievance_id UUID NOT NULL REFERENCES grievances(id),
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    level VARCHAR(20) NOT NULL,
    factors JSONB NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- SLA POLICIES
-- ============================================================
CREATE TABLE sla_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- SLA RULES
-- ============================================================
CREATE TABLE sla_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sla_policy_id UUID NOT NULL REFERENCES sla_policies(id) ON DELETE CASCADE,
    priority priority_level NOT NULL,
    resolution_deadline_hours INTEGER NOT NULL,
    acknowledgment_deadline_hours FLOAT NOT NULL,
    first_update_deadline_hours FLOAT NOT NULL,
    warning_threshold_percent INTEGER NOT NULL DEFAULT 50,
    UNIQUE (sla_policy_id, priority)
);

-- ============================================================
-- ESCALATION POLICIES
-- ============================================================
CREATE TABLE escalation_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- ESCALATION LEVELS
-- ============================================================
CREATE TABLE escalation_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES escalation_policies(id) ON DELETE CASCADE,
    level INTEGER NOT NULL,
    trigger_event VARCHAR(50) NOT NULL,
    action escalation_action NOT NULL,
    target_role VARCHAR(50) NOT NULL,
    generate_dossier BOOLEAN NOT NULL DEFAULT false,
    cooldown_minutes INTEGER NOT NULL DEFAULT 0,
    condition_expression TEXT,
    UNIQUE (policy_id, level)
);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    grievance_id UUID REFERENCES grievances(id),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    read_at TIMESTAMPTZ
);

-- ============================================================
-- AUDIT LOGS (Append-only)
-- ============================================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES users(id),
    actor_role VARCHAR(20),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    previous_state JSONB,
    new_state JSONB,
    reason TEXT,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Prevent UPDATE/DELETE on audit logs
CREATE RULE no_update_audit AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE no_delete_audit AS ON DELETE TO audit_logs DO INSTEAD NOTHING;

-- ============================================================
-- INTEGRATIONS
-- ============================================================
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_system VARCHAR(100) UNIQUE NOT NULL,
    adapter_type VARCHAR(100) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    status_mapping JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    sync_enabled BOOLEAN NOT NULL DEFAULT false,
    sync_interval_minutes INTEGER NOT NULL DEFAULT 60,
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Indexes

```sql
-- Grievance queries
CREATE INDEX idx_grievances_status ON grievances(status);
CREATE INDEX idx_grievances_department ON grievances(department_id);
CREATE INDEX idx_grievances_officer ON grievances(assigned_officer_id);
CREATE INDEX idx_grievances_citizen ON grievances(citizen_id);
CREATE INDEX idx_grievances_priority ON grievances(priority);
CREATE INDEX idx_grievances_risk ON grievances(risk_score DESC);
CREATE INDEX idx_grievances_sla_active ON grievances(sla_deadline)
    WHERE status NOT IN ('CLOSED');
CREATE INDEX idx_grievances_created ON grievances(created_at DESC);
CREATE INDEX idx_grievances_source ON grievances(source_system, external_id);

-- Vector similarity search
CREATE INDEX idx_grievances_embedding ON grievances
    USING hnsw (embedding vector_cosine_ops);

-- Event queries
CREATE INDEX idx_events_grievance_time ON grievance_events(grievance_id, created_at);
CREATE INDEX idx_events_type ON grievance_events(event_type);

-- Assignment queries
CREATE INDEX idx_assignments_officer_active ON assignments(officer_id)
    WHERE is_active = true;
CREATE INDEX idx_assignments_grievance ON assignments(grievance_id);

-- Notification queries
CREATE INDEX idx_notifications_user_unread ON notifications(user_id)
    WHERE is_read = false;
CREATE INDEX idx_notifications_user_time ON notifications(user_id, created_at DESC);

-- Audit queries
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_actor_time ON audit_logs(actor_id, created_at DESC);
CREATE INDEX idx_audit_time ON audit_logs(created_at DESC);

-- Risk score queries
CREATE INDEX idx_risk_scores_grievance ON risk_scores(grievance_id, computed_at DESC);

-- Escalation queries
CREATE INDEX idx_escalations_grievance ON escalations(grievance_id);
CREATE INDEX idx_escalations_status ON escalations(status) WHERE status = 'PENDING';
```

## Notes

1. **Circular FK dependency**: `departments` references `sla_policies` and `escalation_policies`. These policy tables must be created before `departments`. In practice, use `ALTER TABLE` to add FKs after all tables exist, or handle via Alembic migrations.

2. **Append-only enforcement**: PostgreSQL `RULE` is used to prevent UPDATE/DELETE on `grievance_events` and `audit_logs`. Application code should also enforce this at the ORM level.

3. **pgvector**: The `embedding` column uses `vector(384)` matching the output dimension of `all-MiniLM-L6-v2`. The HNSW index provides efficient approximate nearest neighbor search without requiring a large initial dataset.

4. **Reference number generation**: `reference_number` follows the format `GRV-YYYY-NNNN`. This should be generated by a PostgreSQL sequence or application logic with uniqueness enforced by the UNIQUE constraint.
