# Product Requirements Document (PRD)

## 1. Product Summary

**Product**: SARA — Smart Accountability & Resolution Assistant
**Version**: 1.0 (MVP)
**Target**: Smart India Hackathon (SIH)
**Last Updated**: August 2026

SARA is an AI-powered accountability and escalation layer designed to operate alongside existing public grievance redressal systems (CPGRAMS, state portals, etc.). It adds proactive risk monitoring, evidence-aware resolution verification, policy-driven escalation, and complete audit trails to the grievance lifecycle.

## 2. Goals

| Goal | Metric |
|---|---|
| Demonstrate end-to-end accountability lifecycle | Complete primary demo in 3–5 minutes |
| AI classification of grievances | >85% accuracy on test set |
| Proactive SLA breach detection | 100% of breaches detected within 1 minute |
| Evidence-based resolution verification | Zero complaints closed without citizen confirmation |
| Explainable AI outputs | 100% of scores have factor breakdowns |
| Complete audit trail | Every state transition logged |

## 3. Users

| Role | Description | Key Goal |
|---|---|---|
| Citizen | Files and tracks grievances | "Know my complaint is being worked on and verified before closure" |
| Officer | Processes assigned grievances | "Know what to do next, prioritized by urgency" |
| Supervisor | Oversees officers and escalations | "See exactly why a case was escalated and what happened" |
| Admin | Configures system and policies | "Set SLA and escalation rules without developer intervention" |

## 4. Core Feature Set (MVP)

### F1: Grievance Submission & AI Processing
- Citizen submits complaint (text + optional location + optional files)
- AI classifies category with confidence score
- AI assesses priority with multi-factor scoring
- AI generates officer-facing summary
- Semantic duplicate detection identifies related complaints

### F2: Smart Routing & Assignment
- Department resolved from AI classification + routing rules
- Officer assigned based on department roster (round-robin MVP)
- SLA deadline computed from priority + department policy
- All assignment events logged

### F3: State Machine Lifecycle
- 7-state grievance lifecycle + governance/SLA/escalation events
- Escalation state overlay (SLA_WARNING, SLA_BREACHED, ESCALATED)
- Every transition creates immutable event record
- Guard conditions on critical transitions

### F4: SLA Monitoring & Governance
- Background periodic SLA checks
- Configurable warning/breach thresholds
- Automated reminders at configurable intervals
- Policy-driven escalation (deterministic, not AI)
- All governance decisions logged

### F5: Accountability Risk Score
- Continuous risk score (0–100) per grievance
- 10 weighted factors with explainable breakdown
- Risk levels: Low, Moderate, High, Very High, Critical
- Score triggers governance engine actions

### F6: Resolution Verification
- Officer submits resolution with evidence
- VERIFICATION state before CLOSED
- Citizen receives verification request
- Citizen confirms (→ CLOSED) or rejects (→ REOPENED)
- Rejection triggers escalation evaluation

### F7: Accountability Dossier
- Auto-generated on escalation
- Contains: timeline, risk breakdown, warnings, evidence, feedback
- Supervisor's decision-support document

### F8: Dashboards
- Citizen: track, verify, provide feedback
- Officer: queue, AI summary, SLA countdown, evidence upload
- Supervisor: escalations, dossiers, department metrics
- Admin: user/department/policy management

### F9: Notifications
- In-app notification system
- Reminders, warnings, escalations, status updates
- Read/unread tracking

### F10: Audit Trail
- Immutable event log for all actions
- Append-only audit table
- Viewable by supervisors and admins

## 5. Out of Scope (MVP)

- Multi-tenancy implementation
- Real external system integration (simulated only)
- Multilingual UI
- Voice input
- Mobile app / responsive design
- Email/SMS notifications
- Advanced analytics / BI
- CI/CD pipeline
- Kubernetes deployment
- Officer performance scoring

## 6. Success Criteria

See [MVP_SCOPE.md](file:///d:/SARA/docs/product/MVP_SCOPE.md) for detailed acceptance criteria.

## 7. Dependencies

| Dependency | Risk | Mitigation |
|---|---|---|
| PostgreSQL + pgvector | Low | Well-established, Docker image available |
| Redis | Low | Standard infrastructure |
| sentence-transformers | Low | Pre-trained models, local inference |
| Gemini API (for summarization) | Medium | Fallback to local Ollama model or truncation |
| scikit-learn | Low | Standard ML library |
| React + TypeScript | Low | Standard frontend stack |

## 8. Risks

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| AI classification accuracy insufficient | Medium | Medium | Use well-curated training data, provide confidence scores, allow manual override |
| SLA monitoring performance at scale | Low | Low | MVP operates on synthetic data; optimize for production later |
| Demo timing too long | High | Medium | Pre-seed database, implement secure fast-forward simulation mode for demo/admin only |
| CPGRAMS claims challenged | High | Low | All claims verified against authoritative sources; clearly labeled assumptions |
| Prompt injection attacks | Medium | Medium | Input sanitization, output validation, never expose raw AI to actions |
