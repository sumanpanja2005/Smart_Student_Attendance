import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { SystemProvider } from './context/SystemContext';
import { AuthProvider } from './context/AuthContext';
import AppRoutes from './routes/AppRoutes';

export const App = () => {
  return (
    <BrowserRouter>
      <SystemProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </SystemProvider>
    </BrowserRouter>
  );
};

export default App;
