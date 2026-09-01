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
import { getSubjects, createSubject, updateSubject, deleteSubject } from '../services/subjectService';
import { BookOpen, Plus, Search, Trash2, Edit3 } from 'lucide-react';

export const SubjectsPage = () => {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSubject, setEditingSubject] = useState(null);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    subject_code: '',
    subject_name: '',
    department: 'Information Technology',
    semester: 5,
    credits: 4,
    description: '',
  });

  const fetchSubjects = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getSubjects({ search });
      setSubjects(data);
    } catch (err) {
      setError(err.message || 'Failed to load subjects curriculum.');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetchSubjects();
  }, [fetchSubjects]);

  const openCreateModal = () => {
    setEditingSubject(null);
    setFormData({
      subject_code: '',
      subject_name: '',
      department: 'Information Technology',
      semester: 5,
      credits: 4,
      description: '',
    });
    setFormError('');
    setIsModalOpen(true);
  };

  const openEditModal = (subject) => {
    setEditingSubject(subject);
    setFormData({
      subject_code: subject.subject_code,
      subject_name: subject.subject_name,
      department: subject.department,
      semester: subject.semester,
      credits: subject.credits,
      description: subject.description || '',
    });
    setFormError('');
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);

    try {
      const payload = {
        ...formData,
        semester: Number(formData.semester),
        credits: Number(formData.credits),
      };

      if (editingSubject) {
        await updateSubject(editingSubject.id, payload);
      } else {
        await createSubject(payload);
      }
      setIsModalOpen(false);
      fetchSubjects();
    } catch (err) {
      setFormError(err.message || 'Failed to save subject.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this subject?')) return;
    try {
      await deleteSubject(id);
      fetchSubjects();
    } catch (err) {
      alert(err.message || 'Failed to delete subject.');
    }
  };

  const tableHeaders = ['Subject Code', 'Subject Name', 'Department', 'Semester', 'Credits', 'Actions'];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Subject Curriculum"
        subtitle="Manage academic courses, subject codes, credit values, and semester distributions"
        actions={
          <Button variant="primary" size="sm" icon={Plus} onClick={openCreateModal}>
            Add New Subject
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-center justify-between w-full gap-4">
            <CardTitle>Subject Offerings ({subjects.length})</CardTitle>
            <div className="w-full sm:w-72">
              <Input
                placeholder="Search by code, subject name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                icon={Search}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Loader message="Loading subject offerings..." />
          ) : error ? (
            <ErrorMessage message={error} onRetry={fetchSubjects} />
          ) : subjects.length === 0 ? (
            <EmptyState
              title="No Subjects Found"
              description="No subjects match your search criteria."
              icon={BookOpen}
              action={
                <Button variant="primary" size="sm" icon={Plus} onClick={openCreateModal}>
                  Create First Subject
                </Button>
              }
            />
          ) : (
            <Table
              headers={tableHeaders}
              data={subjects}
              renderRow={(sub, idx) => (
                <tr key={sub.id || idx} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs font-semibold text-blue-700">{sub.subject_code}</td>
                  <td className="px-6 py-4 font-medium text-gray-900">{sub.subject_name}</td>
                  <td className="px-6 py-4 text-xs text-gray-600">{sub.department}</td>
                  <td className="px-6 py-4 text-xs text-gray-700">Semester {sub.semester}</td>
                  <td className="px-6 py-4 text-xs font-semibold text-gray-800">{sub.credits} Credits</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" icon={Edit3} onClick={() => openEditModal(sub)}>
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-rose-600 hover:bg-rose-50"
                        icon={Trash2}
                        onClick={() => handleDelete(sub.id)}
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

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingSubject ? 'Edit Subject Details' : 'Add New Subject'}
      >
        <form onSubmit={handleFormSubmit} className="space-y-4">
          {formError && <ErrorMessage title="Form Error" message={formError} />}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Subject Code *"
              value={formData.subject_code}
              onChange={(e) => setFormData({ ...formData, subject_code: e.target.value })}
              disabled={!!editingSubject}
              placeholder="e.g. IT-501"
              required
            />
            <Input
              label="Subject Name *"
              value={formData.subject_name}
              onChange={(e) => setFormData({ ...formData, subject_name: e.target.value })}
              placeholder="e.g. Database Management Systems"
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
              label="Credits *"
              type="number"
              min="1"
              max="10"
              value={formData.credits}
              onChange={(e) => setFormData({ ...formData, credits: e.target.value })}
              required
            />
          </div>

          <Input
            label="Description (Optional)"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Brief course overview..."
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={submitting}>
              {editingSubject ? 'Save Changes' : 'Create Subject'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default SubjectsPage;
