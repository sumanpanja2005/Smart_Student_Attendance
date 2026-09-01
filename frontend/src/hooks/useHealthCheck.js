import { useSystem } from '../context/SystemContext';

export const useHealthCheck = () => {
  const { healthData, loading, isBackendConnected, dbStatus, refreshHealth } = useSystem();

  return {
    healthData,
    loading,
    isBackendConnected,
    dbStatus,
    refreshHealth,
  };
};

export default useHealthCheck;
