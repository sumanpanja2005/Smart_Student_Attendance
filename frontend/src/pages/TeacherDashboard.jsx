import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/Card';
import { Loader } from '../components/Loader';
import { ErrorMessage } from '../components/ErrorMessage';
import { EmptyState } from '../components/EmptyState';
import { getMyTeacherProfile } from '../services/teacherService';
import { getClasses } from '../services/classService';
import { useAuth } from '../context/AuthContext';
import { UserCheck, Layers, BookOpen, Clock, Calendar } from 'lucide-react';

export const TeacherDashboard = () => {
  const { user } = useAuth();
  const [teacherProfile, setTeacherProfile] = useState(null);
  const [assignedClasses, setAssignedClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadTeacherData = async () => {
      setLoading(true);
      setError('');
      try {
        const profile = await getMyTeacherProfile();
        setTeacherProfile(profile);

        const classesData = await getClasses({ teacher_id: profile.id });
        setAssignedClasses(classesData);
      } catch (err) {
        setError(err.message || 'Failed to load teacher portal data.');
      } finally {
        setLoading(false);
      }
    };

    loadTeacherData();
  }, []);

  if (loading) {
    return <Loader message="Loading faculty portal..." />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Faculty Portal: Welcome, ${user?.first_name} ${user?.last_name}`}
        subtitle="View your assigned academic classes and department information"
      />

      {/* Teacher Info Card */}
      <Card className="bg-gradient-to-r from-emerald-50/50 via-white to-slate-50 border-emerald-100">
        <CardContent className="p-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-gray-500 font-medium block">Employee ID:</span>
              <span className="text-base font-bold font-mono text-emerald-700">{teacherProfile?.employee_id}</span>
            </div>
            <div>
              <span className="text-gray-500 font-medium block">Department:</span>
              <span className="text-base font-semibold text-gray-900">{teacherProfile?.department}</span>
            </div>
            <div>
              <span className="text-gray-500 font-medium block">Designation:</span>
              <span className="text-base font-semibold text-gray-900">{teacherProfile?.designation}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 flex items-center gap-3">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium">Assigned Class Sections</p>
            <p className="text-2xl font-bold text-gray-900">{assignedClasses.length}</p>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <Calendar className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium">Academic Year</p>
            <p className="text-base font-bold text-gray-900">
              {assignedClasses[0]?.academic_year || '2025-2026'}
            </p>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium">Attendance Sessions</p>
            <p className="text-xs font-semibold text-gray-500 mt-1">Active in Step 3/4</p>
          </div>
        </Card>
      </div>

      {/* Assigned Classes List */}
      <Card>
        <CardHeader>
          <CardTitle>My Assigned Classes ({assignedClasses.length})</CardTitle>
          <CardDescription>Classes allocated to your teaching schedule</CardDescription>
        </CardHeader>
        <CardContent>
          {assignedClasses.length === 0 ? (
            <EmptyState
              title="No Classes Assigned Yet"
              description="An administrator has not assigned any class sections to your faculty profile yet."
              icon={Layers}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {assignedClasses.map((cls) => (
                <div key={cls.id} className="p-4 rounded-xl border border-gray-200 bg-white hover:border-emerald-300 transition-colors space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-base font-bold text-gray-900">{cls.class_name}</h4>
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Sem {cls.semester} ({cls.section})
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">{cls.department} • {cls.academic_year}</p>
                  <div className="pt-2 flex items-center justify-between text-xs text-gray-600 border-t border-gray-100">
                    <span>Enrolled Students: <strong className="text-gray-900">{cls.student_ids?.length || 0}</strong></span>
                    <span>Subjects: <strong className="text-gray-900">{cls.subject_ids?.length || 0}</strong></span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TeacherDashboard;
