import React, { useState, useEffect } from 'react';
import AuditLogTable from '../components/AuditLogTable';
import AuditLogFilters from '../components/AuditLogFilters';
import auditService from '../services/auditService';
import { ShieldCheck, Activity, Trash2, AlertOctagon } from 'lucide-react';

export const AdminAuditPage = () => {
  const [logs, setLogs] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  const [filters, setFilters] = useState({
    event_type: '',
    actor_role: '',
    severity: '',
    status: '',
  });

  const loadLogs = async (currentPage = 1, currentFilters = filters) => {
    setLoading(true);
    try {
      const [res, sum] = await Promise.all([
        auditService.getAuditLogs({ page: currentPage, limit: 50, ...currentFilters }),
        auditService.getAuditSummary(),
      ]);
      setLogs(res.audit_logs || []);
      setTotalCount(res.total_count || 0);
      setSummary(sum);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs(page, filters);
  }, [page]);

  const handleFilterChange = (key, value) => {
    const updated = { ...filters, [key]: value };
    setFilters(updated);
    setPage(1);
    loadLogs(1, updated);
  };

  const handleResetFilters = () => {
    const empty = { event_type: '', actor_role: '', severity: '', status: '' };
    setFilters(empty);
    setPage(1);
    loadLogs(1, empty);
  };

  const handleCleanRetention = async () => {
    if (window.confirm('Delete audit records older than 365 days based on retention policy?')) {
      try {
        await auditService.cleanRetention(365);
        loadLogs(page, filters);
      } catch (err) {
        console.error('Failed to execute retention cleanup:', err);
      }
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-800 tracking-tight">Audit Trail & Security Log</h1>
          <p className="text-xs text-slate-500 mt-1">
            Centralized operational audit trail, user activity monitoring, and security event log.
          </p>
        </div>

        <button
          onClick={handleCleanRetention}
          className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 self-start sm:self-auto"
        >
          <Trash2 className="w-4 h-4 text-slate-500" />
          Apply 365-Day Retention Cleanup
        </button>
      </div>

      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase">Total Audit Events</span>
            <p className="text-xl font-black text-indigo-600">{summary.total_audit_events || 0}</p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase">Auth Events</span>
            <p className="text-xl font-black text-emerald-600">{summary.auth_events_count || 0}</p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase">Attendance Events</span>
            <p className="text-xl font-black text-blue-600">{summary.attendance_events_count || 0}</p>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase">Security Flags</span>
            <p className="text-xl font-black text-rose-600">{summary.security_events_count || 0}</p>
          </div>
        </div>
      )}

      <AuditLogFilters filters={filters} onChange={handleFilterChange} onReset={handleResetFilters} />

      <AuditLogTable
        logs={logs}
        totalCount={totalCount}
        page={page}
        limit={50}
        onPageChange={(p) => setPage(p)}
      />
    </div>
  );
};

export default AdminAuditPage;
