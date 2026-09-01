import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '../components/Card';
import { Table } from '../components/Table';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { Modal } from '../components/Modal';
import { Loader } from '../components/Loader';
import { EmptyState } from '../components/EmptyState';
import { ErrorMessage } from '../components/ErrorMessage';
import { getStudents, createStudent, updateStudent, deactivateStudent } from '../services/studentService';
import { getFaceStatus } from '../services/faceService';
import { GraduationCap, Plus, Search, Trash2, Edit3, Camera, CheckCircle2 } from 'lucide-react';

export const StudentsPage = () => {
  const navigate = useNavigate();
  const [students, setStudents] = useState([]);
  const [faceStatuses, setFaceStatuses] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    student_id: '',
    roll_number: '',
    department: 'Information Technology',
    semester: 5,
    section: 'A',
    admission_year: 2023,
    phone: '',
  });

  const fetchStudents = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getStudents({ search });
      setStudents(data);

      // Fetch face registration status for each student
      const statusMap = {};
      await Promise.all(
        data.map(async (st) => {
          try {
            const stFace = await getFaceStatus(st.id);
            statusMap[st.id] = stFace;
          } catch (e) {
            statusMap[st.id] = { registered: false, sample_count: 0 };
          }
        })
      );
      setFaceStatuses(statusMap);
    } catch (err) {
      setError(err.message || 'Failed to load student profiles.');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  const openCreateModal = () => {
    setEditingStudent(null);
    setFormData({
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      student_id: '',
      roll_number: '',
      department: 'Information Technology',
      semester: 5,
      section: 'A',
      admission_year: 2023,
      phone: '',
    });
    setFormError('');
    setIsModalOpen(true);
  };

  const openEditModal = (student) => {
    setEditingStudent(student);
    setFormData({
      email: student.user?.email || '',
      password: '',
      first_name: student.user?.first_name || '',
      last_name: student.user?.last_name || '',
      student_id: student.student_id,
      roll_number: student.roll_number,
      department: student.department,
      semester: student.semester,
      section: student.section,
      admission_year: student.admission_year,
      phone: student.user?.phone || '',
    });
    setFormError('');
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);

    try {
      if (editingStudent) {
        await updateStudent(editingStudent.id, {
          first_name: formData.first_name,
          last_name: formData.last_name,
          phone: formData.phone,
          department: formData.department,
          semester: Number(formData.semester),
          section: formData.section,
          admission_year: Number(formData.admission_year),
        });
      } else {
        await createStudent({
          ...formData,
          semester: Number(formData.semester),
          admission_year: Number(formData.admission_year),
        });
      }
      setIsModalOpen(false);
      fetchStudents();
    } catch (err) {
      setFormError(err.message || 'Failed to save student profile.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to deactivate this student account?')) return;
    try {
      await deactivateStudent(id);
      fetchStudents();
    } catch (err) {
      alert(err.message || 'Failed to deactivate student.');
    }
  };

  const tableHeaders = [
    'Student ID',
    'Roll No',
    'Name',
    'Email',
    'Dept & Class',
    'Face Biometrics',
    'Status',
    'Actions',
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Student Management"
        subtitle="Manage student identities, enrollment details, and AI face biometrics"
        actions={
          <Button variant="primary" size="sm" icon={Plus} onClick={openCreateModal}>
            Add New Student
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-center justify-between w-full gap-4">
            <CardTitle>Enrolled Students ({students.length})</CardTitle>
            <div className="w-full sm:w-72">
              <Input
                placeholder="Search by student ID, roll, name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                icon={Search}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Loader message="Loading student records..." />
          ) : error ? (
            <ErrorMessage message={error} onRetry={fetchStudents} />
          ) : students.length === 0 ? (
            <EmptyState
              title="No Students Found"
              description="No student profiles match your search criteria."
              icon={GraduationCap}
              action={
                <Button variant="primary" size="sm" icon={Plus} onClick={openCreateModal}>
                  Create First Student
                </Button>
              }
            />
          ) : (
            <Table
              headers={tableHeaders}
              data={students}
              renderRow={(st, idx) => {
                const fStat = faceStatuses[st.id] || {};
                return (
                  <tr key={st.id || idx} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs font-semibold text-indigo-700">{st.student_id}</td>
                    <td className="px-6 py-4 text-xs font-semibold text-gray-800">{st.roll_number}</td>
                    <td className="px-6 py-4 font-medium text-gray-900">
                      {st.user?.first_name} {st.user?.last_name}
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-600">{st.user?.email}</td>
                    <td className="px-6 py-4 text-xs text-gray-600">
                      {st.department} (Sem {st.semester}-{st.section})
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full border ${
                          fStat.registered
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {fStat.registered ? (
                          <>
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Registered ({fStat.sample_count} Samples)
                          </>
                        ) : (
                          '⚠ Not Registered'
                        )}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          st.is_active
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        {st.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          icon={Camera}
                          onClick={() => navigate(`/admin/students/${st.id}/register-face`)}
                        >
                          Register Face
                        </Button>
                        <Button variant="ghost" size="sm" icon={Edit3} onClick={() => openEditModal(st)}>
                          Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-rose-600 hover:bg-rose-50"
                          icon={Trash2}
                          onClick={() => handleDelete(st.id)}
                        >
                          Deactivate
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              }}
            />
          )}
        </CardContent>
      </Card>

      {/* Create / Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingStudent ? 'Edit Student Profile' : 'Add New Student'}
      >
        <form onSubmit={handleFormSubmit} className="space-y-4">
          {formError && <ErrorMessage title="Form Error" message={formError} />}

          {!editingStudent && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Email Address *"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
              <Input
                label="Password *"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
              />
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="First Name *"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              required
            />
            <Input
              label="Last Name *"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Student ID *"
              value={formData.student_id}
              onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
              disabled={!!editingStudent}
              placeholder="e.g. STU-001"
              required
            />
            <Input
              label="Roll Number *"
              value={formData.roll_number}
              onChange={(e) => setFormData({ ...formData, roll_number: e.target.value })}
              placeholder="e.g. 21IT001"
              required
            />
          </div>

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

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitting}>
              {editingStudent ? 'Save Changes' : 'Create Student'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default StudentsPage;
