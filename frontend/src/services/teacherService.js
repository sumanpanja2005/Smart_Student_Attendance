import api from './api';

export const getTeachers = async (params = {}) => {
  const response = await api.get('/teachers', { params });
  return response.data;
};

export const getTeacherById = async (id) => {
  const response = await api.get(`/teachers/${id}`);
  return response.data;
};

export const getMyTeacherProfile = async () => {
  const response = await api.get('/teachers/me');
  return response.data;
};

export const createTeacher = async (teacherData) => {
  const response = await api.post('/teachers', teacherData);
  return response.data;
};

export const updateTeacher = async (id, teacherData) => {
  const response = await api.put(`/teachers/${id}`, teacherData);
  return response.data;
};

export const deactivateTeacher = async (id) => {
  const response = await api.delete(`/teachers/${id}`);
  return response.data;
};
