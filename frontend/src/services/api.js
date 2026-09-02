import axios from 'axios';
import { getToken, removeToken } from '../utils/token';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request Interceptor: Automatically attach Authorization Bearer token
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Centralized error handling & automatic 401 token cleanup
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url = error.config?.url || '';
    
    // Automatically handle 401 Unauthorized by clearing token & emitting event
    // Prevent infinite loops: never dispatch auth:unauthorized for login or logout requests
    if (status === 401 && !url.includes('/auth/login') && !url.includes('/auth/logout')) {
      const hadToken = getToken();
      removeToken();
      if (hadToken) {
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
      }
    }

    const formattedError = {
      message: error.response?.data?.detail || error.response?.data?.message || error.message || 'Server error',
      status: status || 500,
      details: error.response?.data,
    };
    return Promise.reject(formattedError);
  }
);

export default api;
