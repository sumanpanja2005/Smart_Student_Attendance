import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/Card';
import { Loader } from '../components/Loader';
import { ErrorMessage } from '../components/ErrorMessage';
import { EmptyState } from '../components/EmptyState';
import { getMyStudentProfile } from '../services/studentService';
import { getClassById } from '../services/classService';
import { useAuth } from '../context/AuthContext';
import { GraduationCap, BookOpen, Layers, Award, AlertCircle } from 'lucide-react';

export const StudentDashboard = () => {
  const { user } = useAuth();
  const [studentProfile, setStudentProfile] = useState(null);
  const [classDetail, setClassDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadStudentData = async () => {
      setLoading(true);
      setError('');
      try {
        const profile = await getMyStudentProfile();
        setStudentProfile(profile);

        if (profile.class_id) {
          const cls = await getClassById(profile.class_id);
          setClassDetail(cls);
        }
      } catch (err) {
        setError(err.message || 'Failed to load student portal data.');
      } finally {
        setLoading(false);
      }
    };

    loadStudentData();
  }, []);

  if (loading) {
    return <Loader message="Loading student portal..." />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Student Academic Portal: Welcome, ${user?.first_name} ${user?.last_name}`}
        subtitle="View your enrolled class section and subject curriculum"
      />

      {/* Student Profile Card */}
      <Card className="bg-gradient-to-r from-indigo-50/50 via-white to-slate-50 border-indigo-100">
        <CardContent className="p-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-gray-500 font-medium block">Student ID:</span>
              <span className="text-base font-bold font-mono text-indigo-700">{studentProfile?.student_id}</span>
            </div>
            <div>
              <span className="text-gray-500 font-medium block">Roll Number:</span>
              <span className="text-base font-semibold text-gray-900">{studentProfile?.roll_number}</span>
            </div>
            <div>
              <span className="text-gray-500 font-medium block">Department:</span>
              <span className="text-base font-semibold text-gray-900">{studentProfile?.department}</span>
            </div>
            <div>
              <span className="text-gray-500 font-medium block">Semester & Section:</span>
              <span className="text-base font-semibold text-gray-900">
                Sem {studentProfile?.semester} ({studentProfile?.section})
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Class Section & Subjects */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>My Class Section</CardTitle>
            <CardDescription>Academic class group allocation</CardDescription>
          </CardHeader>
          <CardContent>
            {classDetail ? (
              <div className="p-4 rounded-xl bg-indigo-50/40 border border-indigo-100 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-bold text-indigo-900">{classDetail.class_name}</h4>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-800">
                    {classDetail.academic_year}
                  </span>
                </div>
                <p className="text-xs text-gray-600">{classDetail.department} • Semester {classDetail.semester} Section {classDetail.section}</p>
                <div className="pt-2 text-xs text-gray-700 flex items-center gap-4 border-t border-indigo-100">
                  <span>Classmates: <strong>{classDetail.students?.length || 0}</strong></span>
                  <span>Teachers: <strong>{classDetail.teachers?.length || 0}</strong></span>
                </div>
              </div>
            ) : (
              <EmptyState
                title="Not Assigned to a Class"
                description="Your student account has not been assigned to a class section yet."
                icon={Layers}
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Enrolled Subjects ({classDetail?.subjects?.length || 0})</CardTitle>
            <CardDescription>Courses associated with your class section</CardDescription>
          </CardHeader>
          <CardContent>
            {!classDetail || !classDetail.subjects || classDetail.subjects.length === 0 ? (
              <EmptyState
                title="No Subjects Enrolled"
                description="No course subjects have been assigned to your class section yet."
                icon={BookOpen}
              />
            ) : (
              <div className="space-y-2">
                {classDetail.subjects.map((sub) => (
                  <div key={sub.id} className="p-3 rounded-lg border border-gray-200 bg-white flex items-center justify-between text-xs">
                    <div>
                      <span className="font-bold font-mono text-indigo-600 mr-2">{sub.subject_code}</span>
                      <span className="font-semibold text-gray-900">{sub.subject_name}</span>
                    </div>
                    <span className="font-semibold text-gray-500">{sub.credits} Credits</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StudentDashboard;
