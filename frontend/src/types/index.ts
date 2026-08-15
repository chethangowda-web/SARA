export type UserRole = "CITIZEN" | "OFFICER" | "SUPERVISOR" | "ADMIN";

export type GrievanceState =
  | "SUBMITTED"
  | "CLASSIFIED"
  | "ROUTED"
  | "ASSIGNED"
  | "ACKNOWLEDGED"
  | "IN_PROGRESS"
  | "RESOLUTION_SUBMITTED"
  | "VERIFICATION"
  | "CLOSED"
  | "REOPENED";

export type Priority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  department_id: string | null;
  department_name?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  name: string;
  code?: string;
  description?: string;
  created_at?: string;
}

export interface Grievance {
  id: string;
  title: string;
  description: string;
  location: string;
  category?: string | null;
  classification_confidence?: number | null;
  priority?: Priority | null;
  priority_score?: number | null;
  priority_signals?: Record<string, any> | null;
  priority_explanation?: string | null;
  summary?: string | null;
  duplicate_info?: Record<string, any> | null;
  risk_score?: number | null;
  current_state: GrievanceState;
  citizen_id: string;
  department_id?: string | null;
  created_at: string;
  updated_at: string;
  submitted_at?: string | null;
  assigned_at?: string | null;
  resolved_at?: string | null;
  closed_at?: string | null;
  escalated?: boolean | null;
  escalation_level?: number | null;
  sla_hours?: number | null;
  expected_resolution?: string | null;
  citizen?: Partial<User> | null;
  department?: Partial<Department> | null;
}

export interface GrievanceEvent {
  id: string;
  grievance_id: string;
  actor_id?: string | null;
  actor_role?: string | null;
  event_type: string;
  from_state?: GrievanceState | null;
  to_state: GrievanceState;
  reason?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
}

export interface Evidence {
  id: string;
  grievance_id: string;
  file_name: string;
  file_type?: string | null;
  file_size?: number | null;
  description?: string | null;
  uploaded_at: string;
  is_deleted?: boolean;
}

export interface Comment {
  id: string;
  grievance_id: string;
  author_id?: string | null;
  author_role?: string | null;
  comment: string;
  created_at: string;
}

export interface Notification {
  id: string;
  grievance_id?: string | null;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export interface CitizenDashboardData {
  total_grievances: number;
  submitted: number;
  in_progress: number;
  awaiting_verification: number;
  closed: number;
  reopened: number;
  unread_notifications: number;
  recent_grievances: Grievance[];
}

export interface OfficerDashboardData {
  assigned_grievances: number;
  pending_acknowledgement: number;
  in_progress: number;
  resolution_pending_verification: number;
  overdue_grievances: number;
  high_risk_grievances: number;
  unread_notifications: number;
}

export interface SupervisorDashboardData {
  total_active_grievances: number;
  overdue_grievances: number;
  high_risk_grievances: number;
  escalated_grievances: number;
  unassigned_routed_grievances: number;
  pending_verification: number;
  reopened_grievances: number;
  officer_workload: Record<string, number>;
}

export interface AdminDashboardData {
  total_grievances: number;
  grievances_by_department: Record<string, number>;
  grievances_by_state: Record<string, number>;
  sla_breaches: number;
  sla_warnings: number;
  escalated_grievances: number;
  average_resolution_time_hours: number;
  reopened_grievances: number;
  risk_distribution: Record<string, number>;
  officer_workload: Record<string, number>;
}

export interface AnalyticsOverview {
  total_grievances: number;
  open_grievances: number;
  closed_grievances: number;
  reopened_grievances?: number;
  sla_compliance_percent: number;
  sla_warnings: number;
  sla_breaches: number;
  average_resolution_hours: number;
  average_assignment_hours: number;
  average_acknowledgement_hours: number;
  escalated_grievances: number;
  critical_high_risk: number;
}

export interface AnalyticsDepartment {
  department_id: string;
  department_name: string;
  open_grievances: number;
  closed_grievances: number;
  total_grievances: number;
  sla_compliance_percent: number;
  average_resolution_hours: number;
  average_assignment_hours?: number;
  average_acknowledgement_hours?: number;
  escalation_count: number;
  risk_distribution?: Record<string, number>;
  reopened_grievances?: number;
}

export interface TrendPoint {
  timestamp: string;
  value: number;
}

export interface AnalyticsTrend {
  metric: string;
  points: TrendPoint[];
}

export interface AnalyticsAnomaly {
  id: string;
  anomaly_type: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  metric_name?: string;
  observed_value: string | number;
  expected_value: string | number;
  explanation: string;
  detected_at: string;
}

export interface AnalyticsInsight {
  provider: string;
  insights: string[];
  generated_at: string;
  is_fallback?: boolean;
}

export interface AIAnalysisResult {
  category: string;
  priority: Priority;
  confidence: number;
  summary: string;
}
