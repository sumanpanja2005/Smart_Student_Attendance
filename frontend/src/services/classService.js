import api from './api';

export const getClasses = async (params = {}) => {
  const response = await api.get('/classes', { params });
  return response.data;
};

export const getClassById = async (id) => {
  const response = await api.get(`/classes/${id}`);
  return response.data;
};

export const createClass = async (classData) => {
  const response = await api.post('/classes', classData);
  return response.data;
};

export const updateClass = async (id, classData) => {
  const response = await api.put(`/classes/${id}`, classData);
  return response.data;
};

export const deleteClass = async (id) => {
  const response = await api.delete(`/classes/${id}`);
  return response.data;
};

export const assignStudentToClass = async (classId, studentId) => {
  const response = await api.post(`/classes/${classId}/students/${studentId}`);
  return response.data;
};

export const removeStudentFromClass = async (classId, studentId) => {
  const response = await api.delete(`/classes/${classId}/students/${studentId}`);
  return response.data;
};

export const assignTeacherToClass = async (classId, teacherId) => {
  const response = await api.post(`/classes/${classId}/teachers/${teacherId}`);
  return response.data;
};

export const removeTeacherFromClass = async (classId, teacherId) => {
  const response = await api.delete(`/classes/${classId}/teachers/${teacherId}`);
  return response.data;
};

export const assignSubjectToClass = async (classId, subjectId) => {
  const response = await api.post(`/classes/${classId}/subjects/${subjectId}`);
  return response.data;
};

export const removeSubjectFromClass = async (classId, subjectId) => {
  const response = await api.delete(`/classes/${classId}/subjects/${subjectId}`);
  return response.data;
};
