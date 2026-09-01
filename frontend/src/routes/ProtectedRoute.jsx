import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader } from '../components/Loader';

export const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader message="Verifying authentication session..." size="lg" />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    // Redirect user to their own role dashboard if unauthorized for target route
    const roleRoutes = {
      ADMIN: '/admin',
      TEACHER: '/teacher',
      STUDENT: '/student',
    };
    const defaultRedirect = roleRoutes[user.role] || '/';
    return <Navigate to={defaultRedirect} replace />;
  }

  return children;
};

export default ProtectedRoute;
