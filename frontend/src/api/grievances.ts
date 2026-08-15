import { apiFetch } from './client';
import type {
  Grievance,
  GrievanceEvent,
  Evidence,
  Comment,
  Notification,
  CitizenDashboardData,
  OfficerDashboardData,
  SupervisorDashboardData,
  AdminDashboardData,
  AnalyticsOverview,
  AnalyticsDepartment,
  AnalyticsTrend,
  AnalyticsAnomaly,
  AnalyticsInsight
} from '../types';

export interface GrievanceUploadEvidenceParams {
  id: string;
  file: File;
  description?: string;
}

export interface GrievanceAddCommentParams {
  id: string;
  comment: string;
}

// -----------------------------------------------------------------------------
// DASHBOARDS API
// -----------------------------------------------------------------------------

export async function fetchCitizenDashboard() {
  return apiFetch<CitizenDashboardData>('/citizen/dashboard');
}

export async function fetchOfficerDashboard() {
  return apiFetch<OfficerDashboardData>('/officer/dashboard');
}

export async function fetchSupervisorDashboard() {
  return apiFetch<SupervisorDashboardData>('/supervisor/dashboard');
}

export async function fetchAdminDashboard() {
  return apiFetch<AdminDashboardData>('/admin/dashboard');
}

// -----------------------------------------------------------------------------
// GRIEVANCE CRUD & TRANSITIONS
// -----------------------------------------------------------------------------

export async function fetchGrievances(limit = 50, offset = 0) {
  return apiFetch<Grievance[]>(`/grievances?limit=${limit}&offset=${offset}`);
}

export async function fetchGrievanceById(id: string) {
  return apiFetch<Grievance>(`/grievances/${id}`);
}

export async function fetchGrievanceTimeline(id: string) {
  return apiFetch<GrievanceEvent[]>(`/grievances/${id}/timeline`);
}

export async function submitGrievance(data: { title: string; description: string; location?: string }) {
  return apiFetch<Grievance>('/grievances', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function verifyGrievanceResolution(id: string, accept: boolean, reason?: string) {
  return apiFetch<Grievance>(`/grievances/${id}/verify`, {
    method: 'POST',
    body: JSON.stringify({
      action: accept ? 'ACCEPT' : 'REJECT',
      reason: reason || undefined,
    }),
  });
}

export async function acknowledgeGrievance(id: string) {
  return apiFetch<Grievance>(`/grievances/${id}/acknowledge`, { method: 'POST' });
}

export async function startGrievanceWork(id: string) {
  return apiFetch<Grievance>(`/grievances/${id}/start`, { method: 'POST' });
}

export async function resolveGrievance(id: string, resolutionNotes: string) {
  return apiFetch<Grievance>(`/grievances/${id}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ resolution_notes: resolutionNotes }),
  });
}

export async function assignOfficerToGrievance(id: string, officerId: string) {
  return apiFetch<Grievance>(`/grievances/${id}/assign`, {
    method: 'POST',
    body: JSON.stringify({ officer_id: officerId }),
  });
}

export async function routeGrievanceToDepartment(id: string, departmentId: string) {
  return apiFetch<Grievance>(`/grievances/${id}/route`, {
    method: 'POST',
    body: JSON.stringify({ department_id: departmentId }),
  });
}

export async function fetchDepartments() {
  return apiFetch<any[]>('/admin/departments');
}

export async function listDepartmentGrievances(limit = 50, offset = 0) {
  return apiFetch<Grievance[]>(`/grievances/department/list?limit=${limit}&offset=${offset}`);
}

// -----------------------------------------------------------------------------
// EVIDENCE API
// -----------------------------------------------------------------------------

export async function uploadEvidence({ id, file, description }: GrievanceUploadEvidenceParams) {
  const formData = new FormData();
  formData.append('file', file);
  if (description) {
    formData.append('description', description);
  }

  return apiFetch<Evidence>(`/grievances/${id}/evidence`, {
    method: 'POST',
    body: formData,
  });
}

export async function fetchEvidenceList(id: string) {
  return apiFetch<Evidence[]>(`/grievances/${id}/evidence`);
}

export async function deleteEvidence(grievanceId: string, evidenceId: string) {
  return apiFetch<{ status: string }>(`/grievances/${grievanceId}/evidence/${evidenceId}`, {
    method: 'DELETE',
  });
}

// -----------------------------------------------------------------------------
// COMMENTS API
// -----------------------------------------------------------------------------

export async function addComment({ id, comment }: GrievanceAddCommentParams) {
  return apiFetch<Comment>(`/grievances/${id}/comments`, {
    method: 'POST',
    body: JSON.stringify({ comment }),
  });
}

export async function fetchComments(id: string) {
  return apiFetch<Comment[]>(`/grievances/${id}/comments`);
}

// -----------------------------------------------------------------------------
// NOTIFICATIONS API
// -----------------------------------------------------------------------------

export async function fetchNotifications() {
  return apiFetch<Notification[]>('/notifications');
}

export async function markNotificationRead(id: string) {
  return apiFetch<Notification>(`/notifications/${id}/read`, { method: 'PATCH' });
}

export async function markAllNotificationsRead() {
  return apiFetch<{ message: string }>('/notifications/read-all', { method: 'POST' });
}

// -----------------------------------------------------------------------------
// ANALYTICS API
// -----------------------------------------------------------------------------

export async function fetchAnalyticsOverview() {
  return apiFetch<AnalyticsOverview>('/analytics/overview');
}

export async function fetchAnalyticsDepartments() {
  return apiFetch<AnalyticsDepartment[]>('/analytics/departments');
}

export async function fetchAnalyticsTrends(departmentId?: string) {
  const url = departmentId ? `/analytics/trends?department_id=${departmentId}` : '/analytics/trends';
  return apiFetch<AnalyticsTrend[]>(url);
}

export async function fetchAnalyticsAnomalies(departmentId?: string) {
  const url = departmentId ? `/analytics/anomalies?department_id=${departmentId}` : '/analytics/anomalies';
  return apiFetch<AnalyticsAnomaly[]>(url);
}

export async function fetchAnalyticsInsights(departmentId?: string) {
  const url = departmentId ? `/analytics/insights?department_id=${departmentId}` : '/analytics/insights';
  return apiFetch<AnalyticsInsight>(url);
}
