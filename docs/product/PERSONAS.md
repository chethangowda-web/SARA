# User Personas

## Persona 1: Citizen (Rajesh Kumar)

### Demographics
- **Name**: Rajesh Kumar (representative citizen persona)
- **Age**: 28–55
- **Digital literacy**: Variable — from basic smartphone user to proficient web user
- **Language**: Hindi, regional language, or English
- **Access**: Smartphone (primary), shared computer, or Common Service Centre

### Context
Rajesh has an everyday problem that a government department should fix — an open drain, a pothole, a broken streetlight, an exposed electrical wire. He has tried complaining informally and nothing happened. He turns to the formal grievance system.

### Goals
1. Submit a complaint quickly with minimal friction
2. Know that someone is actually working on it
3. See exactly who is responsible and when to expect resolution
4. Be asked whether the problem was actually fixed before the complaint is closed
5. Have recourse if the resolution claim is false

### Pain Points
1. **Black hole**: Complaint submitted but no visibility into what's happening
2. **Premature closure**: "Your complaint has been resolved" — but the pothole is still there
3. **No voice**: Can't reject a false resolution or escalate inaction
4. **Bureaucratic opacity**: Doesn't know who is responsible or why it's delayed
5. **Language barriers**: System assumes fluency in English or Hindi

### SARA Value for Rajesh
- Clear timeline with SLA countdown
- Proactive notifications on progress
- Active resolution verification: "Has this actually been fixed?" with YES/NO
- Rejection triggers reopening and escalation
- Transparent status showing responsible department and officer role

---

## Persona 2: Officer (Priya Sharma, Grievance Redressal Officer)

### Demographics
- **Name**: Priya Sharma (representative officer persona)
- **Age**: 30–50
- **Role**: Grievance Redressal Officer (GRO) in a municipal or department office
- **Digital literacy**: Proficient
- **Workload**: 50–200 active grievances

### Context
Priya is a mid-level government officer assigned to resolve complaints in her department. She receives grievances through CPGRAMS or a department portal. She is overworked, under-resourced, and sometimes receives misclassified complaints that aren't even her department's responsibility.

### Goals
1. Quickly understand what each complaint is about
2. Know which ones are urgent and why
3. Track her SLA obligations
4. Focus on the highest-risk cases first
5. Upload evidence of resolution
6. Not get unfairly penalized for systemic issues beyond her control

### Pain Points
1. **Information overload**: Too many complaints, no intelligent prioritization
2. **Misclassification**: Receives complaints that belong to another department
3. **Manual tracking**: Must manually track which cases are approaching SLA
4. **No AI assistance**: Must read every complaint in full to understand it
5. **Accountability without tools**: Held accountable but given basic tools

### SARA Value for Priya
- AI-generated summary of each complaint
- Priority ranking with risk scores
- SLA countdown with visual urgency indicators
- Clear "what to do next" recommendations
- Evidence upload workflow
- Alert when a case is about to breach SLA
- Classification confidence score (flag potential misroutes)

---

## Persona 3: Supervisor (Dr. Anand Mehta, Director-level)

### Demographics
- **Name**: Dr. Anand Mehta (representative supervisor persona)
- **Age**: 45–60
- **Role**: Director / Senior Authority overseeing multiple departments or officers
- **Digital literacy**: Moderate to high
- **Focus**: Strategic oversight, not individual case handling

### Context
Dr. Mehta oversees 15 GROs across 4 departments. He receives escalated cases but currently must manually review case histories. He needs to identify systemic issues and hold officers accountable — but the tools give him aggregate statistics, not actionable case-level intelligence.

### Goals
1. Quickly identify the highest-risk and most overdue cases
2. Understand exactly why a case was escalated
3. See the complete history of a grievance at a glance
4. Identify patterns: which departments, officers, or issue types are problematic
5. Make informed decisions on escalated cases
6. Generate reports for higher authorities

### Pain Points
1. **Information reconstruction**: Must manually piece together case context
2. **Aggregate blindness**: Has department-level KPIs but not case-level intelligence
3. **Delayed awareness**: Learns about problematic cases after SLA breaches
4. **Lack of structured dossiers**: No single view that answers "why was this escalated and what happened?"
5. **Limited predictive insight**: Can't identify cases that will become problems

### SARA Value for Dr. Mehta
- Accountability dossiers for every escalated case
- Dashboard showing high-risk, overdue, and escalated cases
- Department/officer performance analytics
- SLA breach trends and pattern analysis
- Proactive alerts before situations deteriorate
- Repeat complaint cluster identification

---

## Persona 4: System Administrator (Vikram Patel)

### Demographics
- **Name**: Vikram Patel (representative admin persona)
- **Age**: 25–45
- **Role**: Technical administrator responsible for system configuration
- **Digital literacy**: High (technical background)

### Context
Vikram manages the SARA deployment for his organization. He configures departments, SLA policies, escalation rules, user roles, and integrations with external systems.

### Goals
1. Easily configure departments, officers, and roles
2. Set and modify SLA policies per department/category
3. Configure escalation rules and thresholds
4. Manage integrations with external grievance systems
5. Monitor system health and audit logs
6. Ensure security and access control

### Pain Points
1. Hardcoded policies that require developer intervention to change
2. Lack of integration flexibility
3. Poor audit visibility
4. Complex deployment and maintenance

### SARA Value for Vikram
- Admin dashboard with full RBAC management
- Configurable SLA and escalation policies via UI
- Integration adapter management
- System health monitoring
- Comprehensive audit logs
- Docker-based deployment
