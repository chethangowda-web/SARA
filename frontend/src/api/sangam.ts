import { apiFetch } from './client';

export interface NeedCluster {
  id: string;
  title: string;
  category: string;
  department_id?: string;
  department_name?: string;
  location_name: string;
  latitude?: number;
  longitude?: number;
  complaint_count: number;
  unique_citizen_count: number;
  severity_score: number;
  persistence_score: number;
  unresolved_count: number;
  reopened_count: number;
  first_reported_at?: string;
  last_reported_at?: string;
  priority_score: number;
  priority_breakdown?: {
    complaint_volume_score: number;
    severity_score: number;
    persistence_score: number;
    unresolved_score: number;
    reopened_score: number;
    raw_complaint_count: number;
  };
  status: string;
  created_at: string;
  updated_at: string;
}

export interface GovernmentProject {
  id: string;
  project_code: string;
  name: string;
  description?: string;
  department_id?: string;
  department_name?: string;
  category: string;
  location: string;
  latitude?: number;
  longitude?: number;
  allocated_amount: number;
  spent_amount: number;
  start_date?: string;
  expected_end_date?: string;
  actual_end_date?: string;
  status: string;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface InvestmentMatch {
  id: string;
  need_cluster_id: string;
  government_project_id: string;
  match_score: number;
  match_reason: string;
  created_at: string;
  government_project?: GovernmentProject;
}

export interface IntelligenceAlert {
  id: string;
  type: string;
  severity: string;
  need_cluster_id?: string;
  government_project_id?: string;
  title: string;
  description: string;
  evidence_json?: Record<string, any>;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface SangamOverview {
  total_active_needs: number;
  active_hotspots_count: number;
  unserved_gaps_count: number;
  outcome_mismatches_count: number;
  high_priority_count: number;
  total_matched_investment: number;
  recent_alerts: IntelligenceAlert[];
  top_priority_clusters: NeedCluster[];
}

export interface EvidenceDrawerData {
  need_cluster: NeedCluster;
  contributing_grievances: Array<{
    id: string;
    tracking_number: string;
    title: string;
    description: string;
    category: string;
    current_state: string;
    created_at: string;
    location: string;
    citizen_name?: string;
  }>;
  matched_projects: InvestmentMatch[];
  associated_alerts: IntelligenceAlert[];
  detection_reasoning: string;
}

export const sangamApi = {
  getOverview: async (): Promise<SangamOverview> => {
    return apiFetch<SangamOverview>('/sangam/overview');
  },

  getNeedClusters: async (): Promise<NeedCluster[]> => {
    return apiFetch<NeedCluster[]>('/sangam/needs');
  },

  getNeedCluster: async (id: string): Promise<NeedCluster> => {
    return apiFetch<NeedCluster>(`/sangam/needs/${id}`);
  },

  getEvidenceDrawerData: async (id: string): Promise<EvidenceDrawerData> => {
    return apiFetch<EvidenceDrawerData>(`/sangam/needs/${id}/evidence`);
  },

  getHotspots: async (): Promise<NeedCluster[]> => {
    return apiFetch<NeedCluster[]>('/sangam/hotspots');
  },

  getGapsAndMismatches: async (): Promise<IntelligenceAlert[]> => {
    return apiFetch<IntelligenceAlert[]>('/sangam/gaps');
  },

  getAlerts: async (): Promise<IntelligenceAlert[]> => {
    return apiFetch<IntelligenceAlert[]>('/sangam/alerts');
  },

  getPriorities: async (): Promise<NeedCluster[]> => {
    return apiFetch<NeedCluster[]>('/sangam/priorities');
  },

  getProjects: async (): Promise<GovernmentProject[]> => {
    return apiFetch<GovernmentProject[]>('/sangam/projects');
  },

  createProject: async (data: Partial<GovernmentProject>): Promise<GovernmentProject> => {
    return apiFetch<GovernmentProject>('/sangam/projects', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  updateProject: async (id: string, data: Partial<GovernmentProject>): Promise<GovernmentProject> => {
    return apiFetch<GovernmentProject>(`/sangam/projects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }
};
