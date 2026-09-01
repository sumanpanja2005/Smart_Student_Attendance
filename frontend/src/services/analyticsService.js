import api from './api';

export const analyticsService = {
  // Student self endpoints
  getMyAnalytics: async () => {
    const response = await api.get('/analytics/student/me');
    return response.data;
  },

  getMyTrend: async (periodType = 'daily') => {
    const response = await api.get(`/analytics/student/me/trend?period_type=${periodType}`);
    return response.data;
  },

  getMySubjectAnalytics: async () => {
    const response = await api.get('/analytics/student/me/subjects');
    return response.data;
  },

  // Admin / Teacher endpoints
  getStudentAnalytics: async (studentId) => {
    const response = await api.get(`/analytics/students/${studentId}`);
    return response.data;
  },

  getClassAnalytics: async (classId) => {
    const response = await api.get(`/analytics/classes/${classId}`);
    return response.data;
  },

  getSubjectAnalytics: async (classId, subjectId) => {
    const response = await api.get(`/analytics/classes/${classId}/subjects/${subjectId}`);
    return response.data;
  },

  getRiskStudents: async (riskLevel = '') => {
    const url = riskLevel ? `/analytics/risk-students?risk_level=${riskLevel}` : '/analytics/risk-students';
    const response = await api.get(url);
    return response.data;
  },

  getAnalyticsDashboard: async () => {
    const response = await api.get('/analytics/dashboard');
    return response.data;
  },
};

export default analyticsService;
