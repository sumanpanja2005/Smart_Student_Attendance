import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { loginUser, getCurrentUser, logoutUser } from '../services/authService';
import { getToken, setToken, removeToken } from '../utils/token';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setTokenState] = useState(getToken());
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(async () => {
    const storedToken = getToken();
    removeToken();
    setTokenState(null);
    setUser(null);
    if (storedToken) {
      try {
        await logoutUser();
      } catch (err) {
        // Ignore network/authorization errors on logout
      }
    }
  }, []);

  // Hydrate user profile on initial load if token exists
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = getToken();
      if (!storedToken) {
        setIsLoading(false);
        return;
      }
      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (error) {
        console.warn('Failed to restore authentication session:', error.message);
        logout();
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [logout]);

  // Handle automatic 401 unauthorized events from Axios interceptor
  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, [logout]);

  const login = async (email, password) => {
    setIsLoading(true);
    try {
      const data = await loginUser(email, password);
      setToken(data.access_token);
      setTokenState(data.access_token);
      setUser(data.user);
      setIsLoading(false);
      return data.user;
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        logout,
        refreshUser: async () => {
          const u = await getCurrentUser();
          setUser(u);
        },
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
