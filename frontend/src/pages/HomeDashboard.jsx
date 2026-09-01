import React from 'react';
import { PageHeader } from '../components/PageHeader';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../components/Card';
import { Button } from '../components/Button';
import { useSystem } from '../context/SystemContext';
import { Server, Database, Activity, Cpu, Layers, CheckCircle, RefreshCw } from 'lucide-react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export const HomeDashboard = () => {
  const { healthData, isBackendConnected, dbStatus, loading, refreshHealth } = useSystem();

  // Preview chart data to confirm Chart.js setup works
  const sampleLineData = {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'],
    datasets: [
      {
        label: 'System Attendance Rate (Preview)',
        data: [85, 88, 92, 89, 94],
        borderColor: 'rgb(79, 70, 229)',
        backgroundColor: 'rgba(79, 70, 229, 0.1)',
        tension: 0.3,
        fill: true,
      },
    ],
  };

  const sampleBarData = {
    labels: ['Computer Science', 'Information Tech', 'Electronics', 'Mechanical'],
    datasets: [
      {
        label: 'Enrolled Students (Preview)',
        data: [120, 150, 90, 110],
        backgroundColor: 'rgba(99, 102, 241, 0.8)',
        borderRadius: 6,
      },
    ],
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Smart Attendance & Student Analytics"
        subtitle="Step 1 Foundation Overview & Integration Diagnostics"
        actions={
          <Button variant="outline" size="sm" onClick={refreshHealth} isLoading={loading} icon={RefreshCw}>
            Re-test Health API
          </Button>
        }
      />

      {/* Integration Verification Card */}
      <Card className="border-indigo-100 bg-gradient-to-r from-indigo-50/40 via-white to-slate-50">
        <CardHeader>
          <div>
            <CardTitle>System Integration Status</CardTitle>
            <CardDescription>Live communication state between React, Axios, FastAPI, and MongoDB Atlas</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Frontend Status */}
            <div className="p-4 rounded-xl bg-white border border-gray-200 shadow-2xs flex items-center gap-3">
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase">Frontend (React)</p>
                <p className="text-sm font-bold text-emerald-600 flex items-center gap-1 mt-0.5">
                  <CheckCircle className="w-4 h-4" /> Operational
                </p>
              </div>
            </div>

            {/* Backend FastAPI Status */}
            <div className="p-4 rounded-xl bg-white border border-gray-200 shadow-2xs flex items-center gap-3">
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
                <Server className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase">Backend API (FastAPI)</p>
                <p className={`text-sm font-bold flex items-center gap-1 mt-0.5 ${isBackendConnected ? 'text-emerald-600' : 'text-rose-600'}`}>
                  {isBackendConnected ? 'Connected (200 OK)' : 'Unreachable'}
                </p>
              </div>
            </div>

            {/* MongoDB Atlas Status */}
            <div className="p-4 rounded-xl bg-white border border-gray-200 shadow-2xs flex items-center gap-3">
              <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase">Database (MongoDB)</p>
                <p
                  className={`text-sm font-bold flex items-center gap-1 mt-0.5 ${
                    dbStatus === 'connected'
                      ? 'text-emerald-600'
                      : dbStatus === 'not_configured'
                      ? 'text-amber-600'
                      : 'text-rose-600'
                  }`}
                >
                  {dbStatus === 'connected'
                    ? 'Connected'
                    : dbStatus === 'not_configured'
                    ? 'Not Configured'
                    : 'Disconnected'}
                </p>
              </div>
            </div>
          </div>

          {/* Raw API Payload Response */}
          <div className="mt-4 p-3 bg-slate-900 text-slate-200 rounded-lg font-mono text-xs overflow-x-auto">
            <span className="text-slate-400 block mb-1"># GET /api/health Response:</span>
            {healthData ? JSON.stringify(healthData, null, 2) : 'Fetching system health payload...'}
          </div>
        </CardContent>
      </Card>

      {/* Analytics Preview Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Attendance Trend Preview</CardTitle>
            <CardDescription>Chart.js line chart integration test</CardDescription>
          </CardHeader>
          <CardContent>
            <Line data={sampleLineData} options={{ responsive: true, maintainAspectRatio: true }} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Department Distribution Preview</CardTitle>
            <CardDescription>Chart.js bar chart integration test</CardDescription>
          </CardHeader>
          <CardContent>
            <Bar data={sampleBarData} options={{ responsive: true, maintainAspectRatio: true }} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default HomeDashboard;
