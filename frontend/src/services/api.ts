import axios, { AxiosInstance } from 'axios';
import { 
  AuthResponse, 
  Contract, 
  ContractListResponse, 
  ContractAnalysis, 
  RiskAssessment, 
  RiskListResponse,
  OrganizationRiskListResponse,
  Obligation, 
  ObligationListResponse,
  OrganizationObligationListResponse,
  ComplianceControl, 
  ComplianceTask, 
  ComplianceDashboard, 
  AuditLog,
  AuditLogListResponse,
  ContractSearchResponse,
  ExecutiveReportSummary,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('lexflow_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response interceptor to handle 401 unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Don't auto-redirect if we're on login or register
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        // Option to clear token
      }
    }
    return Promise.reject(error);
  }
);

// Auth Endpoints
export const authApi = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/auth/login', { email, password });
    return res.data;
  },
  register: async (payload: {
    full_name: string;
    email: string;
    password: string;
    organization_name: string;
  }): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/auth/register', payload);
    return res.data;
  },
  getCurrentUser: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};

// Contracts Endpoints
export const contractsApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string; contract_type?: string; status?: string }) => {
    const res = await apiClient.get<ContractListResponse>('/contracts', { params });
    return res.data;
  },
  getById: async (id: string) => {
    const res = await apiClient.get<Contract>(`/contracts/${id}`);
    return res.data;
  },
  upload: async (formData: FormData) => {
    const res = await apiClient.post<Contract>('/contracts/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },
  delete: async (id: string) => {
    const res = await apiClient.delete(`/contracts/${id}`);
    return res.data;
  },
  analyze: async (id: string) => {
    const res = await apiClient.post<ContractAnalysis>(`/contracts/${id}/analyze`);
    return res.data;
  },
  getAnalysis: async (id: string) => {
    const res = await apiClient.get<ContractAnalysis>(`/contracts/${id}/analysis`);
    return res.data;
  },
  getRisks: async (id: string, severity?: string): Promise<RiskListResponse> => {
    const res = await apiClient.get<RiskListResponse>(`/contracts/${id}/risks`, { params: { severity } });
    return res.data;
  },
  getObligations: async (id: string, status?: string): Promise<ObligationListResponse> => {
    const res = await apiClient.get<ObligationListResponse>(`/contracts/${id}/obligations`, { params: { status } });
    return res.data;
  },
  listOrganizationRisks: async (params?: { severity?: string; contract_id?: string; skip?: number; limit?: number }): Promise<OrganizationRiskListResponse> => {
    const res = await apiClient.get<OrganizationRiskListResponse>('/contracts/risks', { params });
    return res.data;
  },
  listOrganizationObligations: async (params?: { status?: string; contract_id?: string; due_date?: string; responsible_party?: string; skip?: number; limit?: number }): Promise<OrganizationObligationListResponse> => {
    const res = await apiClient.get<OrganizationObligationListResponse>('/contracts/obligations', { params });
    return res.data;
  },
  search: async (payload: { query: string; contract_id?: string; skip?: number; limit?: number }): Promise<ContractSearchResponse> => {
    const res = await apiClient.post<ContractSearchResponse>('/contracts/search', payload);
    return res.data;
  },
};

// Compliance Endpoints
export const complianceApi = {
  getDashboard: async () => {
    const res = await apiClient.get<ComplianceDashboard>('/compliance/dashboard');
    return res.data;
  },
  listControls: async (params?: { status?: string; category?: string; framework?: string; skip?: number; limit?: number }) => {
    const res = await apiClient.get<{ total: number; controls: ComplianceControl[] }>('/compliance/controls', { params });
    return res.data;
  },
  createControl: async (data: Partial<ComplianceControl>) => {
    const res = await apiClient.post<ComplianceControl>('/compliance/controls', data);
    return res.data;
  },
  updateControl: async (id: string, data: Partial<ComplianceControl>) => {
    const res = await apiClient.patch<ComplianceControl>(`/compliance/controls/${id}`, data);
    return res.data;
  },
  deleteControl: async (id: string) => {
    const res = await apiClient.delete(`/compliance/controls/${id}`);
    return res.data;
  },
  listTasks: async (params?: { status?: string; priority?: string; skip?: number; limit?: number }) => {
    const res = await apiClient.get<{ total: number; tasks: ComplianceTask[] }>('/compliance/tasks', { params });
    return res.data;
  },
  createTask: async (data: Partial<ComplianceTask>) => {
    const res = await apiClient.post<ComplianceTask>('/compliance/tasks', data);
    return res.data;
  },
  updateTask: async (id: string, data: Partial<ComplianceTask>) => {
    const res = await apiClient.patch<ComplianceTask>(`/compliance/tasks/${id}`, data);
    return res.data;
  },
  deleteTask: async (id: string) => {
    const res = await apiClient.delete(`/compliance/tasks/${id}`);
    return res.data;
  },
};

// Audit Log Endpoints
export const auditApi = {
  list: async (params?: {
    action?: string;
    entity_type?: string;
    user_id?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }): Promise<AuditLogListResponse> => {
    const res = await apiClient.get<AuditLogListResponse>('/audit', { params });
    return res.data;
  },
};

// Executive Reports & Export Endpoints
export const reportsApi = {
  getSummary: async (): Promise<ExecutiveReportSummary> => {
    const res = await apiClient.get<ExecutiveReportSummary>('/reports/summary');
    return res.data;
  },
  downloadCsv: async (type: string = 'executive'): Promise<void> => {
    const res = await apiClient.get('/reports/export/csv', {
      params: { type },
      responseType: 'blob',
    });
    const blob = new Blob([res.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `lexflow_${type}_report.csv`);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
  downloadPdf: async (): Promise<void> => {
    const res = await apiClient.get('/reports/export/pdf', {
      responseType: 'blob',
    });
    const blob = new Blob([res.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'lexflow_executive_dossier.pdf');
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
