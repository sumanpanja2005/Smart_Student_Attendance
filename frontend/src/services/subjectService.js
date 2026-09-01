import api from './api';

export const getSubjects = async (params = {}) => {
  const response = await api.get('/subjects', { params });
  return response.data;
};

export const getSubjectById = async (id) => {
  const response = await api.get(`/subjects/${id}`);
  return response.data;
};

export const createSubject = async (subjectData) => {
  const response = await api.post('/subjects', subjectData);
  return response.data;
};

export const updateSubject = async (id, subjectData) => {
  const response = await api.put(`/subjects/${id}`, subjectData);
  return response.data;
};

export const deleteSubject = async (id) => {
  const response = await api.delete(`/subjects/${id}`);
  return response.data;
};
