import React, { useState, useEffect } from 'react';
import SystemHealthCard from '../components/SystemHealthCard';
import auditService from '../services/auditService';
import { Activity, Users, GraduationCap, Calendar, FileText, Bell, Shield } from 'lucide-react';

export const SystemMonitoringPage = () => {
  const [health, setHealth] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadMonitoring = async () => {
    setLoading(true);
    try {
      const [h, m] = await Promise.all([
        auditService.getSystemHealth(),
        auditService.getSystemMetrics(),
      ]);
      setHealth(h);
      setMetrics(m);
    } catch (err) {
      console.error('Failed to load system monitoring metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMonitoring();
    const interval = setInterval(loadMonitoring, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !health) {
    return (
      <div className="p-8 text-center text-slate-500 font-semibold animate-pulse">
        Loading System Health & Metrics...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-slate-800 tracking-tight">System Operational Monitoring</h1>
        <p className="text-xs text-slate-500 mt-1">
          Real-time system health, database latency, active user counters, and operational metrics.
        </p>
      </div>

      <SystemHealthCard health={health} />

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-indigo-600" />
              Total Users
            </span>
            <p className="text-2xl font-black text-slate-800">{metrics.total_users || 0}</p>
            <span className="text-[10px] text-slate-400 font-semibold">
              {metrics.active_users || 0} active accounts
            </span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1.5">
              <GraduationCap className="w-3.5 h-3.5 text-emerald-600" />
              Enrolled Students
            </span>
            <p className="text-2xl font-black text-slate-800">{metrics.total_students || 0}</p>
            <span className="text-[10px] text-slate-400 font-semibold">
              {metrics.total_teachers || 0} faculty members
            </span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-blue-600" />
              Open Sessions
            </span>
            <p className="text-2xl font-black text-slate-800">{metrics.open_attendance_sessions || 0}</p>
            <span className="text-[10px] text-slate-400 font-semibold">
              {metrics.total_attendance_records || 0} total records
            </span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-1">
            <span className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-purple-600" />
              Reports Generated
            </span>
            <p className="text-2xl font-black text-slate-800">{metrics.generated_report_count || 0}</p>
            <span className="text-[10px] text-slate-400 font-semibold">
              {metrics.notification_count || 0} notifications
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemMonitoringPage;
