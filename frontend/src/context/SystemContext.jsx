import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getHealthStatus } from '../services/healthService';

const SystemContext = createContext();

export const SystemProvider = ({ children }) => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkHealth = useCallback(async () => {
    setLoading(true);
    const data = await getHealthStatus();
    setHealthData(data);
    setLoading(false);
  }, []);

  useEffect(() => {
    checkHealth();
    // Refresh health status every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const isBackendConnected = healthData?.status === 'ok';
  const dbStatus = healthData?.database || 'disconnected';

  return (
    <SystemContext.Provider
      value={{
        healthData,
        loading,
        isBackendConnected,
        dbStatus,
        refreshHealth: checkHealth,
      }}
    >
      {children}
    </SystemContext.Provider>
  );
};

export const useSystem = () => {
  const context = useContext(SystemContext);
  if (!context) {
    throw new Error('useSystem must be used within a SystemProvider');
  }
  return context;
};
