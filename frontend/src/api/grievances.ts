import { apiFetch } from './client';

export interface GrievanceUploadEvidenceParams {
  id: string;
  file: File;
  description?: string;
}

export interface GrievanceAddCommentParams {
  id: string;
  comment: string;
}

export interface NotificationResponse {
  id: string;
  user_id: string;
  grievance_id: string | null;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

// -----------------------------------------------------------------------------
// DASHBOARDS API
// -----------------------------------------------------------------------------

export async function fetchCitizenDashboard() {
  return apiFetch('/citizen/dashboard');
}

export async function fetchOfficerDashboard() {
  return apiFetch('/officer/dashboard');
}

export async function fetchSupervisorDashboard() {
  return apiFetch('/supervisor/dashboard');
}

export async function fetchAdminDashboard() {
  return apiFetch('/admin/dashboard');
}

// -----------------------------------------------------------------------------
// ANALYTICS API
// -----------------------------------------------------------------------------

export async function fetchAnalyticsOverview() {
  return apiFetch('/analytics/overview');
}

export async function fetchAnalyticsDepartments() {
  return apiFetch('/analytics/departments');
}

export async function fetchAnalyticsTrends(departmentId?: string) {
  const url = departmentId ? `/analytics/trends?department_id=${departmentId}` : '/analytics/trends';
  return apiFetch(url);
}

export async function fetchAnalyticsAnomalies(departmentId?: string) {
  const url = departmentId ? `/analytics/anomalies?department_id=${departmentId}` : '/analytics/anomalies';
  return apiFetch(url);
}

export async function fetchAnalyticsInsights(departmentId?: string) {
  const url = departmentId ? `/analytics/insights?department_id=${departmentId}` : '/analytics/insights';
  return apiFetch(url);
}

export const uploadEvidence = async ({ id, file, description }: GrievanceUploadEvidenceParams) => {
  const formData = new FormData();
  formData.append('file', file);
  if (description) {
    formData.append('description', description);
  }

  return apiFetch(`/grievances/${id}/evidence`, {
    method: 'POST',
    body: formData as any,
    headers: {
      // We will fix client.ts to omit 'Content-Type' if body is FormData.
    }
  });
};

export const addComment = (params: GrievanceAddCommentParams) => 
  apiFetch(`/grievances/${params.id}/comments`, {
    method: 'POST',
    body: JSON.stringify({ comment: params.comment })
  });

export const fetchComments = (id: string) => 
  apiFetch(`/grievances/${id}/comments`);

export const fetchNotifications = () => 
  apiFetch<NotificationResponse[]>('/notifications');

export const markNotificationRead = (id: string) => 
  apiFetch(`/notifications/${id}/read`, { method: 'PATCH' });

export const markAllNotificationsRead = () => 
  apiFetch('/notifications/read-all', { method: 'POST' });
