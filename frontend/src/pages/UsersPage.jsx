import React, { useState, useEffect, useCallback } from 'react';
import { PageHeader } from '../components/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '../components/Card';
import { Table } from '../components/Table';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { Loader } from '../components/Loader';
import { EmptyState } from '../components/EmptyState';
import { ErrorMessage } from '../components/ErrorMessage';
import { getUsers, updateUserStatus } from '../services/userService';
import { formatDate } from '../utils/formatters';
import { UserCog, Search, CheckCircle, XCircle } from 'lucide-react';

export const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getUsers({ search, role: roleFilter || undefined });
      setUsers(data);
    } catch (err) {
      setError(err.message || 'Failed to load system user accounts.');
    } finally {
      setLoading(false);
    }
  }, [search, roleFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleToggleStatus = async (user) => {
    const actionStr = user.is_active ? 'deactivate' : 'activate';
    if (!window.confirm(`Are you sure you want to ${actionStr} account ${user.email}?`)) return;

    try {
      await updateUserStatus(user.id, !user.is_active);
      fetchUsers();
    } catch (err) {
      alert(err.message || `Failed to ${actionStr} user account.`);
    }
  };

  const roleColors = {
    ADMIN: 'bg-purple-100 text-purple-800 border-purple-200',
    TEACHER: 'bg-blue-100 text-blue-800 border-blue-200',
    STUDENT: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  };

  const tableHeaders = ['Email', 'Full Name', 'Phone', 'Role', 'Status', 'Registered', 'Actions'];

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Users Management"
        subtitle="Review platform user accounts, roles, and authentication status"
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-center justify-between w-full gap-4">
            <CardTitle>User Accounts ({users.length})</CardTitle>
            <div className="flex items-center gap-3 w-full sm:w-auto">
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="rounded-lg border border-gray-300 px-3 py-2 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Roles</option>
                <option value="ADMIN">ADMIN</option>
                <option value="TEACHER">TEACHER</option>
                <option value="STUDENT">STUDENT</option>
              </select>

              <div className="w-full sm:w-64">
                <Input
                  placeholder="Search email, name..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  icon={Search}
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Loader message="Loading user accounts..." />
          ) : error ? (
            <ErrorMessage message={error} onRetry={fetchUsers} />
          ) : users.length === 0 ? (
            <EmptyState
              title="No Users Found"
              description="No user accounts match your search criteria."
              icon={UserCog}
            />
          ) : (
            <Table
              headers={tableHeaders}
              data={users}
              renderRow={(u, idx) => (
                <tr key={u.id || idx} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4 font-medium text-gray-900">{u.email}</td>
                  <td className="px-6 py-4 text-xs font-semibold text-gray-800">
                    {u.first_name} {u.last_name}
                  </td>
                  <td className="px-6 py-4 text-xs text-gray-500">{u.phone || 'N/A'}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-block text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full border ${
                        roleColors[u.role] || 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {u.role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        u.is_active
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}
                    >
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-xs text-gray-500">{formatDate(u.created_at)}</td>
                  <td className="px-6 py-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      className={u.is_active ? 'text-rose-600 hover:bg-rose-50' : 'text-emerald-600 hover:bg-emerald-50'}
                      icon={u.is_active ? XCircle : CheckCircle}
                      onClick={() => handleToggleStatus(u)}
                    >
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </Button>
                  </td>
                </tr>
              )}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default UsersPage;
