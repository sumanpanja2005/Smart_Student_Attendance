import api from './api';

export const reportService = {
  generateStudentReport: async (data) => {
    const response = await api.post('/reports/student', data);
    return response.data;
  },

  generateClassReport: async (data) => {
    const response = await api.post('/reports/class', data);
    return response.data;
  },

  generateSubjectReport: async (data) => {
    const response = await api.post('/reports/subject', data);
    return response.data;
  },

  generateAnalyticsReport: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.student_id) query.append('student_id', params.student_id);
    if (params.class_id) query.append('class_id', params.class_id);

    const url = `/reports/analytics${query.toString() ? `?${query.toString()}` : ''}`;
    const response = await api.post(url);
    return response.data;
  },

  downloadReportFile: async (reportId, fileName = 'report.pdf') => {
    const response = await api.get(`/reports/${reportId}`, {
      responseType: 'blob',
    });

    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

export default reportService;
