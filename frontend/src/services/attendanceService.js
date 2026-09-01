import api from './api';

export const attendanceService = {
  createSession: async (sessionData) => {
    const response = await api.post('/attendance/sessions', sessionData);
    return response.data;
  },

  getSessions: async (params = {}) => {
    const response = await api.get('/attendance/sessions', { params });
    return response.data;
  },

  getSession: async (sessionId) => {
    const response = await api.get(`/attendance/sessions/${sessionId}`);
    return response.data;
  },

  closeSession: async (sessionId) => {
    const response = await api.patch(`/attendance/sessions/${sessionId}/close`);
    return response.data;
  },

  cancelSession: async (sessionId) => {
    const response = await api.patch(`/attendance/sessions/${sessionId}/cancel`);
    return response.data;
  },

  markFaceAttendance: async (sessionId, imageBlob) => {
    const formData = new FormData();
    formData.append('file', imageBlob, 'frame.jpg');
    const response = await api.post(`/attendance/sessions/${sessionId}/mark-face`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  markManualAttendance: async (sessionId, manualData) => {
    const response = await api.post(`/attendance/sessions/${sessionId}/manual`, manualData);
    return response.data;
  },

  bulkMarkAttendance: async (sessionId, records) => {
    const response = await api.post(`/attendance/sessions/${sessionId}/bulk`, { records });
    return response.data;
  },

  updateAttendanceRecord: async (recordId, updateData) => {
    const response = await api.patch(`/attendance/records/${recordId}`, updateData);
    return response.data;
  },

  getSessionRecords: async (sessionId) => {
    const response = await api.get(`/attendance/sessions/${sessionId}/records`);
    return response.data;
  },

  getMyAttendanceHistory: async (params = {}) => {
    const response = await api.get('/attendance/student/me', { params });
    return response.data;
  },

  getMyAttendanceSummary: async () => {
    const response = await api.get('/attendance/student/me/summary');
    return response.data;
  },

  getMySubjectSummaries: async () => {
    const response = await api.get('/attendance/student/me/summary/subjects');
    return response.data;
  },

  getStudentAttendanceHistory: async (studentId, params = {}) => {
    const response = await api.get(`/attendance/students/${studentId}`, { params });
    return response.data;
  },

  getStudentAttendanceSummary: async (studentId) => {
    const response = await api.get(`/attendance/students/${studentId}/summary`);
    return response.data;
  },

  getStudentSubjectSummaries: async (studentId) => {
    const response = await api.get(`/attendance/students/${studentId}/summary/subjects`);
    return response.data;
  },
};
