# Functional Requirements

## FR-1: Authentication & User Management

### FR-1.1: User Registration
- **Actors**: Citizen (self-registration), Admin (create officer/supervisor)
- **Input**: Email, password, full name, phone (optional), role
- **Validation**: Email format, password strength (min 8 chars, mixed case + digit), unique email
- **Output**: User account created, JWT tokens issued
- **Acceptance criteria**:
  - Citizens can self-register
  - Officers and supervisors are created by admins only
  - Password is stored as bcrypt hash
  - Duplicate email registration returns 409

### FR-1.2: Login
- **Input**: Email, password
- **Output**: Access token (30min) + refresh token (7d)
- **Acceptance criteria**:
  - Valid credentials return tokens
  - Invalid credentials return 401
  - Account disabled returns 403

### FR-1.3: Role-Based Access
- **Roles**: CITIZEN, OFFICER, SUPERVISOR, ADMIN
- **Acceptance criteria**:
  - Each API endpoint enforces role-based access per permission matrix
  - Citizens can only access their own data
  - Officers access only their assigned grievances
  - Supervisors access their department's data
  - Admins access all data

---

## FR-2: Grievance Submission

### FR-2.1: Create Grievance
- **Actor**: Citizen
- **Input**: Description (required), location text (optional), latitude/longitude (optional), attachments (optional, max 5 files, max 10MB each)
- **Processing**: 
  1. Create grievance record with status SUBMITTED
  2. Emit GRIEVANCE_CREATED event
  3. Trigger async AI processing (classification, priority, summary, embedding)
- **Output**: Grievance ID, reference number
- **Acceptance criteria**:
  - Grievance created with status SUBMITTED
  - Reference number auto-generated (GRV-YYYY-NNNN format)
  - Event record created
  - AI processing initiated asynchronously
  - Attachments stored securely

### FR-2.2: AI Classification
- **Trigger**: GRIEVANCE_CREATED event
- **Processing**: Classify complaint text → category + confidence
- **Output**: Category, confidence score, alternative categories
- **Side effects**: State transitions SUBMITTED → CLASSIFIED, event emitted
- **Acceptance criteria**:
  - Classification completes within 5 seconds
  - Confidence score between 0 and 1
  - Top-3 categories returned
  - Low-confidence (<0.5) flagged for manual review

### FR-2.3: Priority Assessment
- **Trigger**: Post-classification
- **Processing**: Multi-factor scoring (safety, severity, population, time, location, category)
- **Output**: Priority level (CRITICAL/HIGH/MEDIUM/LOW), score (0-100), factor breakdown
- **Acceptance criteria**:
  - Priority assigned with explainable breakdown
  - Safety-related categories receive elevated baseline

### FR-2.4: Smart Routing
- **Trigger**: Post-classification + priority
- **Processing**: Map category → department using routing rules
- **Output**: Department assignment
- **Side effects**: State transitions CLASSIFIED → ROUTED, event emitted
- **Acceptance criteria**:
  - Correct department identified
  - If no mapping exists, flag for manual routing

### FR-2.5: Officer Assignment
- **Trigger**: Post-routing
- **Processing**: Assign available officer from department roster (round-robin for MVP)
- **Output**: Officer assignment, SLA deadline computation
- **Side effects**: State → ASSIGNED, SLA countdown starts, event emitted
- **Acceptance criteria**:
  - Officer assigned from correct department
  - SLA deadline computed from priority + department SLA policy
  - Officer notified

---

## FR-3: State Machine

### FR-3.1: State Transitions
- **Valid transitions**: As defined in [STATE_MACHINE.md](file:///d:/SARA/docs/architecture/STATE_MACHINE.md)
- **Acceptance criteria**:
  - Only valid transitions are permitted
  - Invalid transitions return 400 with error message
  - Every transition emits event
  - Every transition updates grievance.updated_at

### FR-3.2: Guard Conditions
- **Acceptance criteria**:
  - RESOLUTION_SUBMITTED requires at least 1 evidence file
  - CLOSED (citizen path) requires citizen confirmation
  - CLOSED (supervisor override) requires documented reason

---

## FR-4: SLA & Governance

### FR-4.1: SLA Monitoring
- **Trigger**: Periodic background task (every 1–5 minutes)
- **Processing**: Check all active grievances against their SLA deadlines
- **Acceptance criteria**:
  - SLA_WARNING event emitted when warning threshold reached
  - SLA_BREACH event emitted when deadline exceeded
  - Risk score updated on each check

### FR-4.2: Reminders
- **Trigger**: SLA warning, inactivity detection, escalation policy
- **Processing**: Send in-app notification to assigned officer
- **Acceptance criteria**:
  - Reminders sent at configurable intervals
  - Max reminder count enforced before escalation
  - Each reminder logged as event

### FR-4.3: Escalation
- **Trigger**: Escalation policy evaluation (SLA breach, citizen rejection, etc.)
- **Processing**: Escalate to configured target authority, generate dossier
- **Acceptance criteria**:
  - Escalation target resolved from policy (supervisor, dept head, etc.)
  - Accountability dossier generated
  - Supervisor notified
  - Escalation event logged
  - Cooldown period enforced between escalation levels

### FR-4.4: Policy Configuration
- **Actor**: Admin
- **Acceptance criteria**:
  - CRUD for SLA policies (per department, per priority)
  - CRUD for escalation policies (levels, triggers, targets)
  - Policy changes audit-logged

---

## FR-5: Risk Score

### FR-5.1: Risk Computation
- **Trigger**: On event, periodic background task
- **Processing**: Compute Accountability Risk Score (0-100)
- **Output**: Score, level, factor breakdown
- **Acceptance criteria**:
  - Score computed from 10 weighted factors
  - Every score has factor-by-factor explanation
  - Score history preserved in risk_scores table
  - Current score reflected on grievance record

---

## FR-6: Resolution & Verification

### FR-6.1: Resolution Submission
- **Actor**: Officer
- **Input**: Resolution notes, evidence files (at least 1 required)
- **Processing**: State → RESOLUTION_SUBMITTED
- **Acceptance criteria**:
  - Minimum 1 evidence file required
  - Resolution notes required
  - Event emitted

### FR-6.2: Verification Request
- **Trigger**: RESOLUTION_SUBMITTED
- **Processing**: Auto-transition to VERIFICATION, notify citizen
- **Acceptance criteria**:
  - Citizen receives notification with evidence summary
  - Citizen can view uploaded evidence

### FR-6.3: Citizen Confirmation
- **Actor**: Citizen
- **Input**: Confirmed (boolean), comments (optional), rating (optional 1-5)
- **Processing**:
  - If confirmed: State → CLOSED, event emitted
  - If rejected: State → REOPENED, event emitted, escalation evaluated
- **Acceptance criteria**:
  - Confirmation recorded as feedback
  - CLOSED only on explicit citizen confirmation
  - Rejection triggers escalation policy evaluation
  - Feedback stored permanently

---

## FR-7: Accountability Dossier

### FR-7.1: Dossier Generation
- **Trigger**: Escalation, supervisor request
- **Content**: Complaint details, timeline, risk breakdown, warnings, evidence, feedback, recommended action
- **Acceptance criteria**:
  - Dossier contains all specified fields
  - Generated within 2 seconds
  - Versioned (regenerated on case updates)

---

## FR-8: Duplicate Detection

### FR-8.1: Semantic Similarity
- **Trigger**: New grievance created
- **Processing**: Compute embedding, search for similar complaints (>0.80 similarity)
- **Output**: List of potential duplicates with similarity scores
- **Acceptance criteria**:
  - Embedding computed and stored
  - Duplicate suggestions shown to officer
  - Threshold configurable

---

## FR-9: Dashboards

### FR-9.1: Citizen Dashboard
- Submit new grievance
- List own grievances with status, SLA
- View grievance detail with timeline
- Verify/reject resolution
- View notifications

### FR-9.2: Officer Dashboard
- View assigned grievances sorted by risk score
- View AI summary, SLA countdown, priority
- Update grievance status
- Upload evidence
- Submit resolution
- View related/duplicate complaints

### FR-9.3: Supervisor Dashboard
- View escalated cases with dossiers
- View overdue/high-risk cases
- Department performance metrics
- Approve/handle escalations
- Reassign cases

### FR-9.4: Admin Dashboard
- CRUD users, departments
- CRUD SLA and escalation policies
- View audit logs
- System health metrics

---

## FR-10: Notifications

### FR-10.1: In-App Notifications
- Stored in database, fetched via API
- Read/unread tracking
- Types: assignment, reminder, SLA warning, escalation, verification request, status update
- Acceptance criteria:
  - Notifications created for all significant events
  - Unread count available via API
  - Marking as read updates database
