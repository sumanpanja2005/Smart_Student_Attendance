import api from './api';

/**
 * Fetches application and database health status from GET /api/health
 */
export const getHealthStatus = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    return {
      status: 'error',
      message: error.message || 'API server unreachable',
      database: 'disconnected',
    };
  }
};
