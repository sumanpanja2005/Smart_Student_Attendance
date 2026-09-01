import React from 'react';
import SecurityEventBadge from './SecurityEventBadge';
import { ChevronLeft, ChevronRight, FileText, User } from 'lucide-react';

const AuditLogTable = ({ logs = [], totalCount = 0, page = 1, limit = 50, onPageChange }) => {
  const totalPages = Math.ceil(totalCount / limit) || 1;

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs space-y-4 p-4">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider">
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">Actor</th>
              <th className="py-3 px-4">Event & Action</th>
              <th className="py-3 px-4">Resource</th>
              <th className="py-3 px-4">Severity</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-medium">
            {logs.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-400 text-xs">
                  No audit trail records match the selected filter criteria.
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 text-slate-500 whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      <span className="font-bold text-slate-800">{log.actor_role || 'SYSTEM'}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 font-bold text-indigo-700">{log.event_type}</td>
                  <td className="py-3 px-4 text-slate-600">{log.resource_type}</td>
                  <td className="py-3 px-4">
                    <SecurityEventBadge severity={log.severity} />
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`font-bold ${
                        log.status === 'SUCCESS' ? 'text-emerald-600' : 'text-rose-600'
                      }`}
                    >
                      {log.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-600 max-w-xs truncate" title={log.message}>
                    {log.message}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-600">
          <span>
            Page <strong className="text-slate-800">{page}</strong> of <strong>{totalPages}</strong> ({totalCount} total events)
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="p-1.5 rounded-lg border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="p-1.5 rounded-lg border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition-all"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogTable;
