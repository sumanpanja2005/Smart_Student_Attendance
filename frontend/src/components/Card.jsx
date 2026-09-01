import React from 'react';

export const Card = ({ children, className = '', ...props }) => {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-xs overflow-hidden ${className}`} {...props}>
      {children}
    </div>
  );
};

export const CardHeader = ({ children, className = '' }) => {
  return (
    <div className={`px-6 py-4 border-b border-gray-100 flex items-center justify-between ${className}`}>
      {children}
    </div>
  );
};

export const CardTitle = ({ children, className = '' }) => {
  return <h3 className={`text-base font-semibold text-gray-900 ${className}`}>{children}</h3>;
};

export const CardDescription = ({ children, className = '' }) => {
  return <p className={`text-xs text-gray-500 mt-0.5 ${className}`}>{children}</p>;
};

export const CardContent = ({ children, className = '' }) => {
  return <div className={`p-6 ${className}`}>{children}</div>;
};

export const CardFooter = ({ children, className = '' }) => {
  return (
    <div className={`px-6 py-3 bg-gray-50 border-t border-gray-100 flex items-center justify-between ${className}`}>
      {children}
    </div>
  );
};

export default Card;
