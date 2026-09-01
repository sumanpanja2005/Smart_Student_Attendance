import React from 'react';
import { Check, CheckCheck, Trash2, Bell, AlertTriangle, AlertOctagon, Info } from 'lucide-react';

const NotificationPanel = ({ notifications = [], onMarkRead, onMarkAllRead, onDelete }) => {
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return <AlertOctagon className="w-5 h-5 text-rose-600" />;
      case 'WARNING':
      case 'HIGH':
        return <AlertTriangle className="w-5 h-5 text-amber-600" />;
      default:
        return <Info className="w-5 h-5 text-indigo-600" />;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs space-y-4 p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
          <Bell className="w-5 h-5 text-indigo-600" />
          Notification Workspace
        </h3>

        {notifications.length > 0 && onMarkAllRead && (
          <button
            onClick={onMarkAllRead}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 self-start sm:self-auto"
          >
            <CheckCheck className="w-4 h-4 text-indigo-600" />
            Mark All as Read
          </button>
        )}
      </div>

      {notifications.length === 0 ? (
        <div className="p-12 text-center text-slate-400 text-sm">
          <Bell className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          No notifications found in your inbox.
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={`p-4 rounded-xl border transition-all flex items-start gap-4 ${
                n.is_read ? 'bg-slate-50/50 border-slate-200/80' : 'bg-indigo-50/30 border-indigo-200/80 shadow-xs'
              }`}
            >
              <div className="p-2 bg-white rounded-xl border border-slate-200 shadow-2xs shrink-0">
                {getSeverityIcon(n.severity)}
              </div>

              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-bold text-slate-800">{n.title}</h4>
                  {!n.is_read && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-indigo-600 text-white">
                      New
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{n.message}</p>
                <span className="block text-[11px] text-slate-400 font-medium pt-1">
                  {new Date(n.created_at).toLocaleString()}
                </span>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                {!n.is_read && onMarkRead && (
                  <button
                    onClick={() => onMarkRead(n.id)}
                    className="p-1.5 hover:bg-white rounded-lg text-slate-400 hover:text-indigo-600 transition-colors border border-transparent hover:border-slate-200"
                    title="Mark as read"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={() => onDelete(n.id)}
                    className="p-1.5 hover:bg-rose-50 rounded-lg text-slate-400 hover:text-rose-600 transition-colors border border-transparent hover:border-rose-200"
                    title="Delete notification"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NotificationPanel;
