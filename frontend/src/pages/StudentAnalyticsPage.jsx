import React, { useState, useEffect } from 'react';
import { BarChart3, AlertCircle, RefreshCw } from 'lucide-react';
import analyticsService from '../services/analyticsService';
import AnalyticsSummaryCards from '../components/AnalyticsSummaryCards';
import AttendanceTrendChart from '../components/AttendanceTrendChart';
import AttendanceRiskBadge from '../components/AttendanceRiskBadge';
import SubjectAnalyticsCard from '../components/SubjectAnalyticsCard';

const StudentAnalyticsPage = () => {
  const [data, setData] = useState(null);
  const [trendPoints, setTrendPoints] = useState([]);
  const [periodType, setPeriodType] = useState('daily');
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  const fetchAnalytics = async (pType = periodType) => {
    setLoading(true);
    setErrorMsg('');
    try {
      const [analyticsData, trendData] = await Promise.all([
        analyticsService.getMyAnalytics(),
        analyticsService.getMyTrend(pType),
      ]);
      setData(analyticsData);
      setTrendPoints(trendData?.points || []);
    } catch (err) {
      console.error('Failed to load student analytics:', err);
      const msg = err.message || err.response?.data?.detail || 'Failed to load attendance analytics.';
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics(periodType);
  }, [periodType]);

  if (loading && !data) {
    return (
      <div className="p-12 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
        <RefreshCw className="w-5 h-5 animate-spin text-indigo-600" />
        Calculating student attendance analytics...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-indigo-600" />
            My Attendance Analytics
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Personal academic attendance statistics, trends, and risk analysis.
          </p>
        </div>

        <button
          onClick={() => fetchAnalytics(periodType)}
          className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors flex items-center gap-2 self-start sm:self-auto"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh Stats
        </button>
      </div>

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-4 rounded-xl text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
          {errorMsg}
        </div>
      )}

      {/* Summary Cards */}
      {data && (
        <AnalyticsSummaryCards
          attendancePercentage={data.overall_attendance_percentage}
          present={data.present_count}
          absent={data.absent_count}
          late={data.late_count}
          eligibleSessions={data.eligible_session_count}
          riskLevel={data.risk_level}
        />
      )}

      {/* Main Grid: Risk Badge + Trend Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Badge Column */}
        <div className="lg:col-span-1">
          {data && (
            <AttendanceRiskBadge
              riskLevel={data.risk_level}
              riskScore={data.risk_score}
              riskFactors={data.risk_factors}
            />
          )}
        </div>

        {/* Trend Chart Column */}
        <div className="lg:col-span-2">
          <AttendanceTrendChart
            points={trendPoints}
            periodType={periodType}
            onPeriodChange={(newType) => setPeriodType(newType)}
          />
        </div>
      </div>

      {/* Subject-Wise Analytics Breakdown */}
      <div>
        <h3 className="text-base font-bold text-slate-800 mb-3 flex items-center gap-2">
          Subject-Wise Attendance Breakdown
        </h3>
        {data?.subject_summaries && data.subject_summaries.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.subject_summaries.map((sub, idx) => (
              <SubjectAnalyticsCard key={idx} subject={sub} />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 p-6 text-center text-slate-500 text-sm">
            No subject attendance statistics available yet.
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentAnalyticsPage;
