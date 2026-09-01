import api from './api';

export const auditService = {
  getAuditLogs: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.page) query.append('page', params.page);
    if (params.limit) query.append('limit', params.limit);
    if (params.event_type) query.append('event_type', params.event_type);
    if (params.actor_role) query.append('actor_role', params.actor_role);
    if (params.severity) query.append('severity', params.severity);
    if (params.status) query.append('status', params.status);
    if (params.start_date) query.append('start_date', params.start_date);
    if (params.end_date) query.append('end_date', params.end_date);

    const url = `/admin/audit-logs${query.toString() ? `?${query.toString()}` : ''}`;
    const response = await api.get(url);
    return response.data;
  },

  getAuditLog: async (auditId) => {
    const response = await api.get(`/admin/audit-logs/${auditId}`);
    return response.data;
  },

  getAuditSummary: async () => {
    const response = await api.get('/admin/audit-summary');
    return response.data;
  },

  getSecurityEvents: async (limit = 50) => {
    const response = await api.get(`/admin/security-events?limit=${limit}`);
    return response.data;
  },

  getSystemHealth: async () => {
    const response = await api.get('/admin/system/health');
    return response.data;
  },

  getSystemMetrics: async () => {
    const response = await api.get('/admin/system/metrics');
    return response.data;
  },

  cleanRetention: async (retentionDays = 365) => {
    const response = await api.delete(`/admin/audit-logs/retention?retention_days=${retentionDays}`);
    return response.data;
  },
};

export default auditService;
