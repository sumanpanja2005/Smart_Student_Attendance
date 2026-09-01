import React, { useState, useEffect, useCallback } from 'react';
import { PageHeader } from '../components/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '../components/Card';
import { Table } from '../components/Table';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { Modal } from '../components/Modal';
import { Loader } from '../components/Loader';
import { EmptyState } from '../components/EmptyState';
import { ErrorMessage } from '../components/ErrorMessage';
import { getTeachers, createTeacher, updateTeacher, deactivateTeacher } from '../services/teacherService';
import { UserCheck, Plus, Search, UserX, Edit3 } from 'lucide-react';

export const TeachersPage = () => {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState(null);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    employee_id: '',
    department: 'Information Technology',
    designation: 'Assistant Professor',
  });

  const fetchTeachers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getTeachers({ search });
      setTeachers(data);
    } catch (err) {
      setError(err.message || 'Failed to load teachers directory.');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetchTeachers();
  }, [fetchTeachers]);

  const openCreateModal = () => {
    setEditingTeacher(null);
    setFormData({
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      phone: '',
      employee_id: '',
      department: 'Information Technology',
      designation: 'Assistant Professor',
    });
    setFormError('');
    setIsModalOpen(true);
  };

  const openEditModal = (teacher) => {
    setEditingTeacher(teacher);
    setFormData({
      email: teacher.user?.email || '',
      password: '',
      first_name: teacher.user?.first_name || '',
      last_name: teacher.user?.last_name || '',
      phone: teacher.user?.phone || '',
      employee_id: teacher.employee_id,
      department: teacher.department,
      designation: teacher.designation,
    });
    setFormError('');
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);

    try {
      if (editingTeacher) {
        await updateTeacher(editingTeacher.id, {
          first_name: formData.first_name,
          last_name: formData.last_name,
          phone: formData.phone,
          department: formData.department,
          designation: formData.designation,
        });
      } else {
        await createTeacher(formData);
      }
      setIsModalOpen(false);
      fetchTeachers();
    } catch (err) {
      setFormError(err.message || 'Failed to save teacher record.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeactivate = async (id) => {
    if (!window.confirm('Are you sure you want to deactivate this teacher?')) return;
    try {
      await deactivateTeacher(id);
      fetchTeachers();
    } catch (err) {
      alert(err.message || 'Failed to deactivate teacher.');
    }
  };

  const tableHeaders = ['Employee ID', 'Name', 'Email', 'Department', 'Designation', 'Status', 'Actions'];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Teacher Management"
        subtitle="Create, update, and manage faculty accounts and departmental designations"
        actions={
          <Button variant="primary" size="sm" icon={Plus} onClick={openCreateModal}>
            Add New Teacher
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-center justify-between w-full gap-4">
            <CardTitle>Faculty Directory ({teachers.length})</CardTitle>
            <div className="w-full sm:w-72">
              <Input
                placeholder="Search by name, employee ID, email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                icon={Search}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Loader message="Loading faculty records..." />
          ) : error ? (
            <ErrorMessage message={error} onRetry={fetchTeachers} />
          ) : teachers.length === 0 ? (
            <EmptyState
              title="No Teachers Found"
              description="No faculty records match your search criteria."
              icon={UserCheck}
              action={
                <Button variant="primary" size="sm" icon={Plus} onClick={openCreateModal}>
                  Create First Teacher
                </Button>
              }
            />
          ) : (
            <Table
              headers={tableHeaders}
              data={teachers}
              renderRow={(t, idx) => (
                <tr key={t.id || idx} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs font-semibold text-emerald-700">{t.employee_id}</td>
                  <td className="px-6 py-4 font-medium text-gray-900">
                    {t.user?.first_name} {t.user?.last_name}
                  </td>
                  <td className="px-6 py-4 text-gray-500 text-xs">{t.user?.email}</td>
                  <td className="px-6 py-4 text-xs text-gray-600">{t.department}</td>
                  <td className="px-6 py-4 text-xs font-medium text-gray-700">{t.designation}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        t.is_active
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}
                    >
                      {t.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" icon={Edit3} onClick={() => openEditModal(t)}>
                        Edit
                      </Button>
                      {t.is_active && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-rose-600 hover:bg-rose-50"
                          icon={UserX}
                          onClick={() => handleDeactivate(t.id)}
                        >
                          Deactivate
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            />
          )}
        </CardContent>
      </Card>

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingTeacher ? 'Edit Teacher Profile' : 'Create New Teacher Account'}
      >
        <form onSubmit={handleFormSubmit} className="space-y-4">
          {formError && <ErrorMessage title="Form Error" message={formError} />}

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
              label="Email Address *"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              disabled={!!editingTeacher}
              required
            />
            {!editingTeacher && (
              <Input
                label="Password *"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
              />
            )}
            <Input
              label="Phone Number"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Employee ID *"
              value={formData.employee_id}
              onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
              disabled={!!editingTeacher}
              placeholder="e.g. EMP-2024-102"
              required
            />
            <Input
              label="Designation *"
              value={formData.designation}
              onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
              placeholder="e.g. Associate Professor"
              required
            />
          </div>

          <Input
            label="Department *"
            value={formData.department}
            onChange={(e) => setFormData({ ...formData, department: e.target.value })}
            required
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitting}>
              {editingTeacher ? 'Save Changes' : 'Create Teacher'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default TeachersPage;
