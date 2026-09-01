import React from 'react';
import { Inbox } from 'lucide-react';

export const EmptyState = ({
  title = 'No Data Found',
  description = 'There are no records to display at this time.',
  icon: Icon = Inbox,
  action,
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center bg-gray-50/50 rounded-xl border border-dashed border-gray-300 ${className}`}>
      <div className="p-3 bg-gray-100 rounded-full text-gray-400 mb-3">
        <Icon className="w-8 h-8" />
      </div>
      <h4 className="text-base font-semibold text-gray-800">{title}</h4>
      <p className="text-xs text-gray-500 max-w-sm mt-1 mb-4">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};

export default EmptyState;
