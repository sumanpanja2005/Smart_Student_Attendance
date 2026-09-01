import React from 'react';
import { Filter, RefreshCw } from 'lucide-react';

const AuditLogFilters = ({ filters, onChange, onReset }) => {
  return (
    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3 text-xs">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <span className="font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <Filter className="w-4 h-4 text-indigo-600" />
          Filter Audit Trail Events
        </span>
        <button
          onClick={onReset}
          className="text-indigo-600 hover:text-indigo-800 font-semibold text-[11px] flex items-center gap-1"
        >
          <RefreshCw className="w-3 h-3" />
          Reset Filters
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label className="block font-bold text-slate-600 mb-1">Event Category</label>
          <select
            value={filters.event_type || ''}
            onChange={(e) => onChange('event_type', e.target.value)}
            className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Event Categories</option>
            <option value="AUTH_LOGIN">AUTH_LOGIN</option>
            <option value="AUTH_LOGIN_FAILED">AUTH_LOGIN_FAILED</option>
            <option value="AUTH_LOGOUT">AUTH_LOGOUT</option>
            <option value="USER_CREATED">USER_CREATED</option>
            <option value="FACE_REGISTERED">FACE_REGISTERED</option>
            <option value="FACE_RECOGNITION_ATTEMPT">FACE_RECOGNITION_ATTEMPT</option>
            <option value="ATTENDANCE_SESSION_CREATED">ATTENDANCE_SESSION_CREATED</option>
            <option value="ATTENDANCE_SESSION_CLOSED">ATTENDANCE_SESSION_CLOSED</option>
            <option value="ATTENDANCE_MARKED_FACE">ATTENDANCE_MARKED_FACE</option>
            <option value="ANALYTICS_ACCESSED">ANALYTICS_ACCESSED</option>
            <option value="REPORT_GENERATED">REPORT_GENERATED</option>
          </select>
        </div>

        <div>
          <label className="block font-bold text-slate-600 mb-1">Actor Role</label>
          <select
            value={filters.actor_role || ''}
            onChange={(e) => onChange('actor_role', e.target.value)}
            className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Roles</option>
            <option value="ADMIN">ADMIN</option>
            <option value="TEACHER">TEACHER</option>
            <option value="STUDENT">STUDENT</option>
          </select>
        </div>

        <div>
          <label className="block font-bold text-slate-600 mb-1">Severity</label>
          <select
            value={filters.severity || ''}
            onChange={(e) => onChange('severity', e.target.value)}
            className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Severities</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </div>

        <div>
          <label className="block font-bold text-slate-600 mb-1">Status</label>
          <select
            value={filters.status || ''}
            onChange={(e) => onChange('status', e.target.value)}
            className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="SUCCESS">SUCCESS</option>
            <option value="FAILED">FAILED</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default AuditLogFilters;
