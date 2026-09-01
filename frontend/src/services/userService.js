import api from './api';

export const getUsers = async (params = {}) => {
  const response = await api.get('/users', { params });
  return response.data;
};

export const getUserById = async (id) => {
  const response = await api.get(`/users/${id}`);
  return response.data;
};

export const updateUser = async (id, data) => {
  const response = await api.put(`/users/${id}`, data);
  return response.data;
};

export const updateUserStatus = async (id, isActive) => {
  const response = await api.patch(`/users/${id}/status`, { is_active: isActive });
  return response.data;
};
