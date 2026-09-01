import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/Card';
import SystemHealthCard from '../components/SystemHealthCard';
import SecurityEventBadge from '../components/SecurityEventBadge';
import {
  GraduationCap,
  UserCheck,
  BookOpen,
  Layers,
  ShieldCheck,
  ArrowRight,
  UserCog,
  Shield,
  Activity,
  AlertTriangle,
} from 'lucide-react';
import { Button } from '../components/Button';
import { getStudents } from '../services/studentService';
import { getTeachers } from '../services/teacherService';
import { getSubjects } from '../services/subjectService';
import { getClasses } from '../services/classService';
import { getUsers } from '../services/userService';
import auditService from '../services/auditService';

export const AdminDashboard = () => {
  const [counts, setCounts] = useState({
    students: 0,
    teachers: 0,
    subjects: 0,
    classes: 0,
    users: 0,
  });
  const [health, setHealth] = useState(null);
  const [securityEvents, setSecurityEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCounts = async () => {
      try {
        const [stRes, tcRes, sbRes, clRes, usRes, healthRes, secRes] = await Promise.allSettled([
          getStudents(),
          getTeachers(),
          getSubjects(),
          getClasses(),
          getUsers(),
          auditService.getSystemHealth(),
          auditService.getSecurityEvents(5),
        ]);

        setCounts({
          students: stRes.status === 'fulfilled' ? stRes.value.length : 0,
          teachers: tcRes.status === 'fulfilled' ? tcRes.value.length : 0,
          subjects: sbRes.status === 'fulfilled' ? sbRes.value.length : 0,
          classes: clRes.status === 'fulfilled' ? clRes.value.length : 0,
          users: usRes.status === 'fulfilled' ? usRes.value.length : 0,
        });

        if (healthRes.status === 'fulfilled') setHealth(healthRes.value);
        if (secRes.status === 'fulfilled') setSecurityEvents(secRes.value);
      } catch (err) {
        console.error('Failed to load dashboard metrics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCounts();
  }, []);

  const modules = [
    {
      title: 'Audit Trail & Security',
      description: 'Monitor operational system logs, user activity, and security event alerts.',
      path: '/admin/audit',
      icon: Shield,
      count: 'Live Log',
      color: 'bg-rose-50 text-rose-600',
    },
    {
      title: 'System Operational Monitoring',
      description: 'View database health, server latency, active session counters, and system metrics.',
      path: '/admin/system',
      icon: Activity,
      count: 'Metrics',
      color: 'bg-emerald-50 text-emerald-600',
    },
    {
      title: 'Student Directory',
      description: 'Manage student accounts, roll numbers, semesters, and class assignments.',
      path: '/admin/students',
      icon: GraduationCap,
      count: `${counts.students} Students`,
      color: 'bg-indigo-50 text-indigo-600',
    },
    {
      title: 'Teacher Management',
      description: 'Manage faculty profiles, employee IDs, and department designations.',
      path: '/admin/teachers',
      icon: UserCheck,
      count: `${counts.teachers} Teachers`,
      color: 'bg-blue-50 text-blue-600',
    },
    {
      title: 'Subject Curriculum',
      description: 'Define course subjects, credit values, and department semesters.',
      path: '/admin/subjects',
      icon: BookOpen,
      count: `${counts.subjects} Subjects`,
      color: 'bg-purple-50 text-purple-600',
    },
    {
      title: 'Class Sections',
      description: 'Configure class groups and assign students, teachers, and subjects.',
      path: '/admin/classes',
      icon: Layers,
      count: `${counts.classes} Classes`,
      color: 'bg-amber-50 text-amber-600',
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Admin Control Center"
        subtitle="Manage academic structure, users, security audit trail, and system metrics"
      />

      {/* System Health Widget */}
      <SystemHealthCard health={health} />

      {/* Security Events Overview Section */}
      {securityEvents.length > 0 && (
        <Card className="p-4 space-y-3 border-amber-200 bg-amber-50/20">
          <div className="flex items-center justify-between border-b border-amber-200/60 pb-2">
            <h3 className="text-xs font-bold text-amber-900 flex items-center gap-1.5 uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              Recent Security Audit Events
            </h3>
            <Link to="/admin/audit" className="text-xs font-bold text-indigo-600 hover:text-indigo-800">
              View All Audit Trail &rarr;
            </Link>
          </div>
          <div className="divide-y divide-amber-100 text-xs">
            {securityEvents.map((evt) => (
              <div key={evt.id} className="py-2 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 truncate">
                  <SecurityEventBadge severity={evt.severity} />
                  <span className="font-semibold text-slate-700 truncate">{evt.message}</span>
                </div>
                <span className="text-[10px] text-slate-400 font-medium whitespace-nowrap">
                  {new Date(evt.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 flex items-center gap-3">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium">Total Students</p>
            <p className="text-2xl font-bold text-gray-900">{loading ? '...' : counts.students}</p>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <UserCheck className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium">Total Teachers</p>
            <p className="text-2xl font-bold text-gray-900">{loading ? '...' : counts.teachers}</p>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium">Total Subjects</p>
            <p className="text-2xl font-bold text-gray-900">{loading ? '...' : counts.subjects}</p>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium">Total Classes</p>
            <p className="text-2xl font-bold text-gray-900">{loading ? '...' : counts.classes}</p>
          </div>
        </Card>
      </div>

      {/* Module Navigation Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {modules.map((m, idx) => {
          const Icon = m.icon;
          return (
            <Card key={idx} className="hover:shadow-md transition-shadow flex flex-col justify-between">
              <CardHeader>
                <div className="flex items-center justify-between w-full">
                  <div className={`p-3 rounded-xl ${m.color}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-gray-100 text-gray-700">
                    {m.count}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="py-2">
                <CardTitle className="text-lg">{m.title}</CardTitle>
                <CardDescription className="mt-1.5 leading-relaxed">{m.description}</CardDescription>
              </CardContent>
              <div className="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex justify-end">
                <Link to={m.path}>
                  <Button variant="outline" size="sm" icon={ArrowRight}>
                    Manage
                  </Button>
                </Link>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default AdminDashboard;
