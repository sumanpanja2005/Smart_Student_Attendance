import React, { useState, useEffect, useCallback } from 'react';
import { PageHeader } from '../components/PageHeader';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../components/Card';
import { Table } from '../components/Table';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { Modal } from '../components/Modal';
import { Loader } from '../components/Loader';
import { EmptyState } from '../components/EmptyState';
import { ErrorMessage } from '../components/ErrorMessage';
import {
  getClasses,
  getClassById,
  createClass,
  updateClass,
  deleteClass,
  assignStudentToClass,
  removeStudentFromClass,
  assignTeacherToClass,
  removeTeacherFromClass,
  assignSubjectToClass,
  removeSubjectFromClass,
} from '../services/classService';
import { getStudents } from '../services/studentService';
import { getTeachers } from '../services/teacherService';
import { getSubjects } from '../services/subjectService';
import { Layers, Plus, Eye, Trash2, UserPlus, BookPlus, UserCheck, GraduationCap, BookOpen, X } from 'lucide-react';

export const ClassesPage = () => {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Class Detail Modal
  const [selectedClass, setSelectedClass] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Available pools for assignments
  const [allStudents, setAllStudents] = useState([]);
  const [allTeachers, setAllTeachers] = useState([]);
  const [allSubjects, setAllSubjects] = useState([]);

  // Assignment selection states
  const [assignStudentId, setAssignStudentId] = useState('');
  const [assignTeacherId, setAssignTeacherId] = useState('');
  const [assignSubjectId, setAssignSubjectId] = useState('');

  // Create Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    class_name: 'B.Tech IT-3A',
    department: 'Information Technology',
    semester: 5,
    section: 'A',
    academic_year: '2025-2026',
  });

  const fetchClasses = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getClasses();
      setClasses(data);
    } catch (err) {
      setError(err.message || 'Failed to load class sections.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClasses();
  }, [fetchClasses]);

  const loadAllPools = async () => {
    try {
      const [st, tc, sb] = await Promise.all([getStudents(), getTeachers(), getSubjects()]);
      setAllStudents(st);
      setAllTeachers(tc);
      setAllSubjects(sb);
    } catch (err) {
      console.error('Failed to load assignment options:', err);
    }
  };

  const openDetailModal = async (classItem) => {
    setDetailLoading(true);
    setSelectedClass(null);
    await loadAllPools();
    try {
      const fullDetail = await getClassById(classItem.id);
      setSelectedClass(fullDetail);
    } catch (err) {
      alert(err.message || 'Failed to load class details.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    try {
      await createClass({
        ...formData,
        semester: Number(formData.semester),
      });
      setIsCreateOpen(false);
      fetchClasses();
    } catch (err) {
      setFormError(err.message || 'Failed to create class section.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteClass = async (id) => {
    if (!window.confirm('Are you sure you want to delete this class section?')) return;
    try {
      await deleteClass(id);
      if (selectedClass?.id === id) setSelectedClass(null);
      fetchClasses();
    } catch (err) {
      alert(err.message || 'Failed to delete class section.');
    }
  };

  // Assignment Handlers
  const handleAssignStudent = async () => {
    if (!assignStudentId || !selectedClass) return;
    try {
      await assignStudentToClass(selectedClass.id, assignStudentId);
      setAssignStudentId('');
      openDetailModal(selectedClass);
      fetchClasses();
    } catch (err) {
      alert(err.message || 'Failed to assign student.');
    }
  };

  const handleRemoveStudent = async (studentId) => {
    if (!selectedClass) return;
    try {
      await removeStudentFromClass(selectedClass.id, studentId);
      openDetailModal(selectedClass);
      fetchClasses();
    } catch (err) {
      alert(err.message || 'Failed to remove student.');
    }
  };

  const handleAssignTeacher = async () => {
    if (!assignTeacherId || !selectedClass) return;
    try {
      await assignTeacherToClass(selectedClass.id, assignTeacherId);
      setAssignTeacherId('');
      openDetailModal(selectedClass);
      fetchClasses();
    } catch (err) {
      alert(err.message || 'Failed to assign teacher.');
    }
  };

  const handleRemoveTeacher = async (teacherId) => {
    if (!selectedClass) return;
    try {
      await removeTeacherFromClass(selectedClass.id, teacherId);
      openDetailModal(selectedClass);
      fetchClasses();
    } catch (err) {
      alert(err.message || 'Failed to remove teacher.');
    }
  };

  const handleAssignSubject = async () => {
    if (!assignSubjectId || !selectedClass) return;
    try {
      await assignSubjectToClass(selectedClass.id, assignSubjectId);
      setAssignSubjectId('');
      openDetailModal(selectedClass);
      fetchClasses();
    } catch (err) {
      alert(err.message || 'Failed to assign subject.');
    }
  };

  const handleRemoveSubject = async (subjectId) => {
    if (!selectedClass) return;
    try {
      await removeSubjectFromClass(selectedClass.id, subjectId);
      openDetailModal(selectedClass);
      fetchClasses();
    } catch (err) {
      alert(err.message || 'Failed to remove subject.');
    }
  };

  const tableHeaders = ['Class Name', 'Department', 'Semester & Section', 'Academic Year', 'Enrolled Students', 'Teachers', 'Subjects', 'Actions'];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Classroom & Academic Relationships"
        subtitle="Manage class groups and assign students, teachers, and subjects"
        actions={
          <Button variant="primary" size="sm" icon={Plus} onClick={() => setIsCreateOpen(true)}>
            Create New Class
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Class Sections ({classes.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Loader message="Loading class sections..." />
          ) : error ? (
            <ErrorMessage message={error} onRetry={fetchClasses} />
          ) : classes.length === 0 ? (
            <EmptyState
              title="No Class Sections Found"
              description="Create your first class section to assign students, teachers, and subjects."
              icon={Layers}
              action={
                <Button variant="primary" size="sm" icon={Plus} onClick={() => setIsCreateOpen(true)}>
                  Create First Class
                </Button>
              }
            />
          ) : (
            <Table
              headers={tableHeaders}
              data={classes}
              renderRow={(cls, idx) => (
                <tr key={cls.id || idx} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4 font-bold text-gray-900">{cls.class_name}</td>
                  <td className="px-6 py-4 text-xs text-gray-600">{cls.department}</td>
                  <td className="px-6 py-4 text-xs text-gray-700">Sem {cls.semester} - Section {cls.section}</td>
                  <td className="px-6 py-4 text-xs font-mono text-gray-600">{cls.academic_year}</td>
                  <td className="px-6 py-4 text-xs font-semibold text-indigo-700">{cls.student_ids?.length || 0} Students</td>
                  <td className="px-6 py-4 text-xs font-semibold text-emerald-700">{cls.teacher_ids?.length || 0} Teachers</td>
                  <td className="px-6 py-4 text-xs font-semibold text-blue-700">{cls.subject_ids?.length || 0} Subjects</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" icon={Eye} onClick={() => openDetailModal(cls)}>
                        Manage Assignments
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-rose-600 hover:bg-rose-50"
                        icon={Trash2}
                        onClick={() => handleDeleteClass(cls.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              )}
            />
          )}
        </CardContent>
      </Card>

      {/* Class Detail & Relationship Assignment Modal */}
      <Modal
        isOpen={!!selectedClass || detailLoading}
        onClose={() => setSelectedClass(null)}
        title={selectedClass ? `Class Relationships: ${selectedClass.class_name}` : 'Loading details...'}
        size="xl"
      >
        {detailLoading || !selectedClass ? (
          <Loader message="Loading class assignment details..." />
        ) : (
          <div className="space-y-6">
            {/* Header summary */}
            <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 flex flex-wrap items-center justify-between text-xs gap-3">
              <div>
                <span className="text-gray-500 font-medium">Department:</span>{' '}
                <span className="font-bold text-gray-900">{selectedClass.department}</span>
              </div>
              <div>
                <span className="text-gray-500 font-medium">Semester & Section:</span>{' '}
                <span className="font-bold text-gray-900">Sem {selectedClass.semester} ({selectedClass.section})</span>
              </div>
              <div>
                <span className="text-gray-500 font-medium">Academic Year:</span>{' '}
                <span className="font-bold text-gray-900">{selectedClass.academic_year}</span>
              </div>
            </div>

            {/* ASSIGNED TEACHERS */}
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b pb-2">
                <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <UserCheck className="w-4 h-4 text-emerald-600" /> Assigned Faculty ({selectedClass.teachers?.length || 0})
                </h4>
              </div>
              <div className="flex gap-2">
                <select
                  value={assignTeacherId}
                  onChange={(e) => setAssignTeacherId(e.target.value)}
                  className="block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  <option value="">-- Select Teacher to Assign --</option>
                  {allTeachers.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.employee_id} - {t.user?.first_name} {t.user?.last_name} ({t.department})
                    </option>
                  ))}
                </select>
                <Button variant="secondary" size="sm" icon={UserPlus} onClick={handleAssignTeacher}>
                  Assign
                </Button>
              </div>
              <div className="flex flex-wrap gap-2 pt-1">
                {selectedClass.teachers?.map((t) => (
                  <span key={t.id} className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full text-xs font-medium">
                    {t.user?.first_name} {t.user?.last_name} ({t.designation})
                    <button onClick={() => handleRemoveTeacher(t.id)} className="hover:text-rose-600">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* ASSIGNED SUBJECTS */}
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b pb-2">
                <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-blue-600" /> Assigned Subjects ({selectedClass.subjects?.length || 0})
                </h4>
              </div>
              <div className="flex gap-2">
                <select
                  value={assignSubjectId}
                  onChange={(e) => setAssignSubjectId(e.target.value)}
                  className="block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="">-- Select Subject to Assign --</option>
                  {allSubjects.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.subject_code} - {sub.subject_name} ({sub.credits} Credits)
                    </option>
                  ))}
                </select>
                <Button variant="secondary" size="sm" icon={BookPlus} onClick={handleAssignSubject}>
                  Assign
                </Button>
              </div>
              <div className="flex flex-wrap gap-2 pt-1">
                {selectedClass.subjects?.map((sub) => (
                  <span key={sub.id} className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 text-blue-800 border border-blue-200 rounded-full text-xs font-medium">
                    {sub.subject_code}: {sub.subject_name}
                    <button onClick={() => handleRemoveSubject(sub.id)} className="hover:text-rose-600">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* ASSIGNED STUDENTS */}
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b pb-2">
                <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-indigo-600" /> Enrolled Students ({selectedClass.students?.length || 0})
                </h4>
              </div>
              <div className="flex gap-2">
                <select
                  value={assignStudentId}
                  onChange={(e) => setAssignStudentId(e.target.value)}
                  className="block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs bg-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  <option value="">-- Select Student to Assign --</option>
                  {allStudents.map((st) => (
                    <option key={st.id} value={st.id}>
                      {st.student_id} - {st.user?.first_name} {st.user?.last_name} (Roll: {st.roll_number})
                    </option>
                  ))}
                </select>
                <Button variant="primary" size="sm" icon={Plus} onClick={handleAssignStudent}>
                  Assign
                </Button>
              </div>
              <div className="max-h-48 overflow-y-auto divide-y border rounded-lg">
                {selectedClass.students?.length === 0 ? (
                  <p className="p-4 text-xs text-gray-400 text-center">No students currently enrolled in this class.</p>
                ) : (
                  selectedClass.students?.map((st) => (
                    <div key={st.id} className="flex items-center justify-between px-4 py-2 text-xs hover:bg-gray-50">
                      <div>
                        <span className="font-semibold text-gray-900">{st.user?.first_name} {st.user?.last_name}</span>
                        <span className="text-gray-500 ml-2">({st.student_id} | Roll: {st.roll_number})</span>
                      </div>
                      <button
                        onClick={() => handleRemoveStudent(st.id)}
                        className="text-rose-600 hover:text-rose-800 text-xs font-semibold"
                      >
                        Remove
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Create Class Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New Class Section"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          {formError && <ErrorMessage title="Form Error" message={formError} />}

          <Input
            label="Class Name *"
            value={formData.class_name}
            onChange={(e) => setFormData({ ...formData, class_name: e.target.value })}
            placeholder="e.g. B.Tech IT-3A"
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              label="Department *"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              required
            />
            <Input
              label="Semester *"
              type="number"
              min="1"
              max="10"
              value={formData.semester}
              onChange={(e) => setFormData({ ...formData, semester: e.target.value })}
              required
            />
            <Input
              label="Section *"
              value={formData.section}
              onChange={(e) => setFormData({ ...formData, section: e.target.value })}
              required
            />
          </div>

          <Input
            label="Academic Year *"
            value={formData.academic_year}
            onChange={(e) => setFormData({ ...formData, academic_year: e.target.value })}
            placeholder="e.g. 2025-2026"
            required
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitting}>
              Create Class Section
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ClassesPage;
