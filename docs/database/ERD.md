# Database — Entity Relationship Diagram

## Full ERD

```mermaid
erDiagram
    USERS {
        uuid id PK
        varchar email UK
        varchar password_hash
        varchar full_name
        varchar phone
        enum role
        uuid department_id FK
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    DEPARTMENTS {
        uuid id PK
        varchar name UK
        varchar code UK
        text description
        uuid parent_department_id FK
        uuid sla_policy_id FK
        uuid escalation_policy_id FK
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    GRIEVANCES {
        uuid id PK
        varchar reference_number UK
        varchar source_system
        varchar external_id
        uuid citizen_id FK
        text description
        varchar category
        float category_confidence
        enum priority
        int priority_score
        varchar status
        uuid department_id FK
        uuid assigned_officer_id FK
        text location_text
        decimal latitude
        decimal longitude
        timestamptz sla_deadline
        int risk_score
        varchar risk_level
        boolean is_escalated
        int escalation_level
        text resolution_notes
        text ai_summary
        vector embedding
        timestamptz created_at
        timestamptz updated_at
        timestamptz acknowledged_at
        timestamptz resolved_at
        timestamptz closed_at
        int reopened_count
    }

    GRIEVANCE_EVENTS {
        uuid id PK
        uuid grievance_id FK
        varchar event_type
        varchar from_state
        varchar to_state
        uuid actor_id FK
        varchar actor_role
        jsonb metadata
        text remarks
        timestamptz created_at
    }

    ASSIGNMENTS {
        uuid id PK
        uuid grievance_id FK
        uuid officer_id FK
        uuid assigned_by FK
        enum assignment_type
        boolean is_active
        timestamptz assigned_at
        timestamptz unassigned_at
    }

    EVIDENCE {
        uuid id PK
        uuid grievance_id FK
        uuid uploaded_by FK
        varchar file_name
        varchar file_path
        varchar file_type
        bigint file_size_bytes
        enum evidence_type
        text description
        jsonb metadata
        timestamptz created_at
    }

    FEEDBACK {
        uuid id PK
        uuid grievance_id FK
        uuid citizen_id FK
        enum feedback_type
        boolean is_satisfied
        int rating
        text comments
        timestamptz created_at
    }

    ESCALATIONS {
        uuid id PK
        uuid grievance_id FK
        int escalation_level
        varchar trigger_reason
        uuid escalated_to FK
        uuid escalated_from FK
        int risk_score_at_escalation
        jsonb risk_explanation
        enum status
        timestamptz reviewed_at
        text reviewer_notes
        uuid dossier_id FK
        timestamptz created_at
    }

    ACCOUNTABILITY_DOSSIERS {
        uuid id PK
        uuid grievance_id FK
        uuid escalation_id FK
        timestamptz generated_at
        jsonb content
        int version
    }

    RISK_SCORES {
        uuid id PK
        uuid grievance_id FK
        int score
        varchar level
        jsonb factors
        timestamptz computed_at
    }

    SLA_POLICIES {
        uuid id PK
        varchar name
        text description
        boolean is_default
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    SLA_RULES {
        uuid id PK
        uuid sla_policy_id FK
        enum priority
        int resolution_deadline_hours
        float acknowledgment_deadline_hours
        float first_update_deadline_hours
        int warning_threshold_percent
    }

    ESCALATION_POLICIES {
        uuid id PK
        varchar name
        text description
        boolean is_default
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    ESCALATION_LEVELS {
        uuid id PK
        uuid policy_id FK
        int level
        varchar trigger_event
        enum action
        varchar target_role
        boolean generate_dossier
        int cooldown_minutes
        text condition_expression
    }

    NOTIFICATIONS {
        uuid id PK
        uuid user_id FK
        uuid grievance_id FK
        varchar type
        varchar title
        text message
        boolean is_read
        timestamptz created_at
        timestamptz read_at
    }

    AUDIT_LOGS {
        uuid id PK
        uuid actor_id FK
        varchar actor_role
        varchar action
        varchar resource_type
        uuid resource_id
        jsonb previous_state
        jsonb new_state
        text reason
        inet ip_address
        timestamptz created_at
    }

    INTEGRATIONS {
        uuid id PK
        varchar source_system UK
        varchar adapter_type
        jsonb config
        jsonb status_mapping
        boolean is_active
        boolean sync_enabled
        int sync_interval_minutes
        timestamptz last_sync_at
        timestamptz created_at
        timestamptz updated_at
    }

    %% Relationships
    USERS }o--|| DEPARTMENTS : "belongs to"
    GRIEVANCES }o--|| USERS : "submitted by (citizen)"
    GRIEVANCES }o--o| USERS : "assigned to (officer)"
    GRIEVANCES }o--o| DEPARTMENTS : "handled by"
    GRIEVANCE_EVENTS }o--|| GRIEVANCES : "belongs to"
    GRIEVANCE_EVENTS }o--o| USERS : "performed by"
    ASSIGNMENTS }o--|| GRIEVANCES : "for"
    ASSIGNMENTS }o--|| USERS : "officer"
    EVIDENCE }o--|| GRIEVANCES : "attached to"
    EVIDENCE }o--|| USERS : "uploaded by"
    FEEDBACK }o--|| GRIEVANCES : "for"
    FEEDBACK }o--|| USERS : "from citizen"
    ESCALATIONS }o--|| GRIEVANCES : "for"
    ESCALATIONS }o--|| USERS : "escalated to"
    ESCALATIONS }o--o| ACCOUNTABILITY_DOSSIERS : "has dossier"
    ACCOUNTABILITY_DOSSIERS }o--|| GRIEVANCES : "for"
    RISK_SCORES }o--|| GRIEVANCES : "for"
    SLA_RULES }o--|| SLA_POLICIES : "part of"
    ESCALATION_LEVELS }o--|| ESCALATION_POLICIES : "part of"
    DEPARTMENTS }o--o| SLA_POLICIES : "uses"
    DEPARTMENTS }o--o| ESCALATION_POLICIES : "uses"
    NOTIFICATIONS }o--|| USERS : "for"
    NOTIFICATIONS }o--o| GRIEVANCES : "about"
    AUDIT_LOGS }o--o| USERS : "by"
```

## Relationship Summary

| Parent | Child | Relationship | Cardinality |
|---|---|---|---|
| users | grievances | Citizen submits | 1:N |
| users | assignments | Officer assigned | 1:N |
| users | notifications | Receives | 1:N |
| departments | users | Officers belong to | 1:N |
| departments | grievances | Handles | 1:N |
| departments | sla_policies | Uses | N:1 |
| departments | escalation_policies | Uses | N:1 |
| grievances | grievance_events | Has events | 1:N |
| grievances | assignments | Has assignments | 1:N |
| grievances | evidence | Has evidence | 1:N |
| grievances | feedback | Has feedback | 1:N |
| grievances | escalations | Has escalations | 1:N |
| grievances | risk_scores | Has score history | 1:N |
| grievances | accountability_dossiers | Has dossiers | 1:N |
| sla_policies | sla_rules | Contains | 1:N |
| escalation_policies | escalation_levels | Contains | 1:N |
| escalations | accountability_dossiers | Generates | 1:1 |
