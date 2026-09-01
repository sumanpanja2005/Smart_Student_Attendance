import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/Button';
import { Home, AlertTriangle } from 'lucide-react';

export const NotFound = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center p-6">
      <div className="p-4 bg-amber-50 text-amber-600 rounded-full mb-4">
        <AlertTriangle className="w-12 h-12" />
      </div>
      <h1 className="text-4xl font-extrabold text-gray-900 mb-2">404</h1>
      <h2 className="text-lg font-semibold text-gray-700 mb-1">Page Not Found</h2>
      <p className="text-sm text-gray-500 max-w-md mb-6">
        The route you are trying to access does not exist or has not been configured in Step 1.
      </p>
      <Link to="/">
        <Button variant="primary" icon={Home}>
          Return to Overview
        </Button>
      </Link>
    </div>
  );
};

export default NotFound;
