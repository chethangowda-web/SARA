import React, { useEffect, useState } from 'react';
import AppLayout from '../../layouts/AppLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import EmptyState from '../../components/ui/EmptyState';
import Modal from '../../components/ui/Modal';
import { apiFetch, formatApiError } from '../../api/client';
import { Users, UserPlus, ShieldAlert, Building2, XCircle, Edit } from 'lucide-react';

interface StaffAuth {
  id: string;
  email: string;
  role: 'CITIZEN' | 'OFFICER' | 'SUPERVISOR' | 'ADMIN';
  department_id: string | null;
  is_active: boolean;
  created_at: string;
  revoked_at: string | null;
}

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  department_id: string | null;
  is_active: boolean;
}

interface Department {
  id: string;
  name: string;
  code: string;
}

export function AdminStaffManagement() {
  const [authorizations, setAuthorizations] = useState<StaffAuth[]>([]);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Add/Edit staff states
  const [modalOpen, setModalOpen] = useState(false);
  const [editingAuth, setEditingAuth] = useState<StaffAuth | null>(null);
  
  const [emailInput, setEmailInput] = useState('');
  const [roleInput, setRoleInput] = useState<'OFFICER' | 'SUPERVISOR' | 'ADMIN'>('OFFICER');
  const [deptInput, setDeptInput] = useState('');
  const [statusInput, setStatusInput] = useState(true);
  const [modalSubmitting, setModalSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [authsData, usersData, deptsData] = await Promise.all([
        apiFetch<StaffAuth[]>('/admin/users/staff-authorizations'),
        apiFetch<UserProfile[]>('/admin/users'),
        apiFetch<Department[]>('/admin/departments')
      ]);
      
      setAuthorizations(authsData || []);
      setUsers(usersData || []);
      setDepartments(deptsData || []);
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getDepartmentName = (id: string | null) => {
    if (!id) return 'N/A';
    const dept = departments.find((d) => d.id === id);
    return dept ? dept.name : 'N/A';
  };

  const getUserAccountStatus = (email: string) => {
    const matchedUser = users.find((u) => u.email.toLowerCase() === email.toLowerCase());
    if (!matchedUser) return <Badge variant="warning" size="sm">Unregistered</Badge>;
    return matchedUser.is_active ? 
      <Badge variant="success" size="sm">Active User</Badge> : 
      <Badge variant="danger" size="sm">Deactivated User</Badge>;
  };

  const handleOpenAddModal = () => {
    setEditingAuth(null);
    setEmailInput('');
    setRoleInput('OFFICER');
    setDeptInput('');
    setStatusInput(true);
    setModalError(null);
    setModalOpen(true);
  };

  const handleOpenEditModal = (auth: StaffAuth) => {
    setEditingAuth(auth);
    setEmailInput(auth.email);
    setRoleInput(auth.role as any);
    setDeptInput(auth.department_id || '');
    setStatusInput(auth.is_active);
    setModalError(null);
    setModalOpen(true);
  };

  const handleModalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    setModalSubmitting(true);

    try {
      const payload = {
        role: roleInput,
        department_id: roleInput === 'ADMIN' ? null : (deptInput || null),
        is_active: statusInput
      };

      if (editingAuth) {
        // Update existing auth
        await apiFetch(`/admin/users/staff-authorizations/${editingAuth.id}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        });
      } else {
        // Create new auth
        if (!emailInput.trim()) {
          setModalError('Email address is required.');
          setModalSubmitting(false);
          return;
        }
        await apiFetch('/admin/users/staff-authorizations', {
          method: 'POST',
          body: JSON.stringify({
            email: emailInput,
            ...payload
          }),
        });
      }

      setModalOpen(false);
      loadData();
    } catch (err: any) {
      setModalError(formatApiError(err));
    } finally {
      setModalSubmitting(false);
    }
  };

  const handleToggleActiveStatus = async (auth: StaffAuth) => {
    try {
      setError(null);
      await apiFetch(`/admin/users/staff-authorizations/${auth.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          is_active: !auth.is_active
        }),
      });
      loadData();
    } catch (err: any) {
      setError(formatApiError(err));
    }
  };

  // Group authorizations by role for clear portal divisions
  const officers = authorizations.filter((a) => a.role === 'OFFICER' && a.is_active);
  const supervisors = authorizations.filter((a) => a.role === 'SUPERVISOR' && a.is_active);
  const admins = authorizations.filter((a) => a.role === 'ADMIN' && a.is_active);
  const inactiveStaff = authorizations.filter((a) => !a.is_active);

  return (
    <AppLayout title="Government Staff Management" breadcrumb="SARA Command Center">
      <div className="space-y-6">
        {/* Top bar */}
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-400" />
              Government Staff Authorization Matrix
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Configure pre-authorized staff emails, assign departments, manage roles, and activate/deactivate personnel.
            </p>
          </div>
          <Button
            variant="primary"
            size="md"
            onClick={handleOpenAddModal}
            icon={<UserPlus className="w-4 h-4" />}
          >
            Authorize New Staff
          </Button>
        </div>

        {error && (
          <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-xs font-semibold rounded-xl flex items-center justify-between">
            <span>{error}</span>
            <Button size="sm" variant="secondary" onClick={loadData}>Retry</Button>
          </div>
        )}

        {loading ? (
          <div className="space-y-3 py-4">
            <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
            <div className="h-12 bg-slate-800/40 rounded-xl animate-pulse" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Officers Portal Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-purple-400">
                  <Users className="w-5 h-5 text-purple-400" />
                  Field Officers Portal ({officers.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {officers.length === 0 ? (
                  <EmptyState title="No active field officers" description="Authorized officers will populate here." />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400 uppercase text-[11px] font-semibold tracking-wider">
                          <th className="pb-3">Authorized Email</th>
                          <th className="pb-3">Assigned Department</th>
                          <th className="pb-3">Account Registration</th>
                          <th className="pb-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {officers.map((off) => (
                          <tr key={off.id} className="hover:bg-slate-800/20 transition">
                            <td className="py-3.5 font-semibold text-slate-200">{off.email}</td>
                            <td className="py-3.5 text-slate-300">
                              <span className="flex items-center gap-1.5">
                                <Building2 className="w-4 h-4 text-slate-500" />
                                {getDepartmentName(off.department_id)}
                              </span>
                            </td>
                            <td className="py-3.5">{getUserAccountStatus(off.email)}</td>
                            <td className="py-3.5 text-right space-x-2">
                              <button
                                onClick={() => handleOpenEditModal(off)}
                                className="p-1 text-blue-400 hover:text-blue-300 transition"
                                title="Edit staff record"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleToggleActiveStatus(off)}
                                className="px-2.5 py-1 bg-red-950/60 hover:bg-red-900/60 border border-red-900/40 rounded-lg text-red-400 text-xs font-bold transition"
                              >
                                Deactivate
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Supervisors Portal Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-amber-400">
                  <Building2 className="w-5 h-5 text-amber-400" />
                  Department Supervisors ({supervisors.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {supervisors.length === 0 ? (
                  <EmptyState title="No active department supervisors" description="Authorized supervisors will populate here." />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400 uppercase text-[11px] font-semibold tracking-wider">
                          <th className="pb-3">Authorized Email</th>
                          <th className="pb-3">Assigned Department</th>
                          <th className="pb-3">Account Registration</th>
                          <th className="pb-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {supervisors.map((sup) => (
                          <tr key={sup.id} className="hover:bg-slate-800/20 transition">
                            <td className="py-3.5 font-semibold text-slate-200">{sup.email}</td>
                            <td className="py-3.5 text-slate-300">
                              <span className="flex items-center gap-1.5">
                                <Building2 className="w-4 h-4 text-slate-500" />
                                {getDepartmentName(sup.department_id)}
                              </span>
                            </td>
                            <td className="py-3.5">{getUserAccountStatus(sup.email)}</td>
                            <td className="py-3.5 text-right space-x-2">
                              <button
                                onClick={() => handleOpenEditModal(sup)}
                                className="p-1 text-blue-400 hover:text-blue-300 transition"
                                title="Edit staff record"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleToggleActiveStatus(sup)}
                                className="px-2.5 py-1 bg-red-950/60 hover:bg-red-900/60 border border-red-900/40 rounded-lg text-red-400 text-xs font-bold transition"
                              >
                                Deactivate
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Administrators Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-red-400">
                  <ShieldAlert className="w-5 h-5 text-red-400" />
                  SARA Platform Administrators ({admins.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 uppercase text-[11px] font-semibold tracking-wider">
                        <th className="pb-3">Authorized Email</th>
                        <th className="pb-3">Account Registration</th>
                        <th className="pb-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {admins.map((adm) => (
                        <tr key={adm.id} className="hover:bg-slate-800/20 transition">
                          <td className="py-3.5 font-semibold text-slate-200">{adm.email}</td>
                          <td className="py-3.5">{getUserAccountStatus(adm.email)}</td>
                          <td className="py-3.5 text-right space-x-2">
                            <button
                              onClick={() => handleOpenEditModal(adm)}
                              className="p-1 text-blue-400 hover:text-blue-300 transition"
                              title="Edit staff record"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleToggleActiveStatus(adm)}
                              className="px-2.5 py-1 bg-red-950/60 hover:bg-red-900/60 border border-red-900/40 rounded-lg text-red-400 text-xs font-bold transition"
                            >
                              Deactivate
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Inactive & Pending Staff Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-slate-400">
                  <XCircle className="w-5 h-5 text-slate-500" />
                  Inactive / Revoked Staff ({inactiveStaff.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {inactiveStaff.length === 0 ? (
                  <EmptyState title="No inactive staff accounts" description="Deactivated or revoked government staff will display here." />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400 uppercase text-[11px] font-semibold tracking-wider">
                          <th className="pb-3">Email Address</th>
                          <th className="pb-3">Revoked Role</th>
                          <th className="pb-3">Account Status</th>
                          <th className="pb-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {inactiveStaff.map((inAuth) => (
                          <tr key={inAuth.id} className="hover:bg-slate-800/20 transition opacity-60">
                            <td className="py-3.5 font-semibold text-slate-200">{inAuth.email}</td>
                            <td className="py-3.5 text-slate-400">
                              <Badge variant="neutral" size="sm">{inAuth.role}</Badge>
                            </td>
                            <td className="py-3.5">{getUserAccountStatus(inAuth.email)}</td>
                            <td className="py-3.5 text-right space-x-2">
                              <button
                                onClick={() => handleToggleActiveStatus(inAuth)}
                                className="px-2.5 py-1 bg-emerald-950/60 hover:bg-emerald-900/60 border border-emerald-900/40 rounded-lg text-emerald-400 text-xs font-bold transition"
                              >
                                Reactivate
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Add / Edit Authorized Staff Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingAuth ? 'Modify Authorized Staff' : 'Authorize New Government Staff'}
        maxWidth="md"
      >
        <form onSubmit={handleModalSubmit} className="space-y-4">
          {modalError && (
            <div className="p-3.5 bg-red-950/50 border border-red-800 text-red-300 text-xs font-semibold rounded-xl">
              {modalError}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
              Official Email Address
            </label>
            <input
              type="email"
              required
              disabled={!!editingAuth}
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              placeholder="staff.name@domain.gov"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
              Portal Role Assignment
            </label>
            <select
              value={roleInput}
              onChange={(e) => setRoleInput(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-blue-500 transition"
            >
              <option value="OFFICER">Field Officer</option>
              <option value="SUPERVISOR">Department Supervisor</option>
              <option value="ADMIN">Platform Administrator</option>
            </select>
          </div>

          {roleInput !== 'ADMIN' && (
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                Assigned Department
              </label>
              <select
                value={deptInput}
                onChange={(e) => setDeptInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-blue-500 transition"
              >
                <option value="">-- Select Department --</option>
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name} ({dept.code})
                  </option>
                ))}
              </select>
            </div>
          )}

          {editingAuth && (
            <div className="flex items-center justify-between p-3.5 bg-slate-950 border border-slate-800 rounded-xl">
              <div>
                <div className="text-xs font-bold text-slate-200">Authorization Status</div>
                <div className="text-[10px] text-slate-500 mt-0.5">Toggle active authorization permission</div>
              </div>
              <input
                type="checkbox"
                checked={statusInput}
                onChange={(e) => setStatusInput(e.target.checked)}
                className="w-5 h-5 rounded border-slate-800 text-blue-600 focus:ring-blue-500"
              />
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800/80">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-4 py-2.5 text-xs text-slate-400 hover:text-slate-200 font-semibold"
            >
              Cancel
            </button>
            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={modalSubmitting}
            >
              {editingAuth ? 'Save Changes' : 'Authorize Staff'}
            </Button>
          </div>
        </form>
      </Modal>
    </AppLayout>
  );
}

export default AdminStaffManagement;
