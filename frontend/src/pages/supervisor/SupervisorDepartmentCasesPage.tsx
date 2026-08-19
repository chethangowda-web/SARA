import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '../../layouts/AppLayout';
import Button from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import StatusBadge from '../../components/ui/StatusBadge';
import PriorityBadge from '../../components/ui/PriorityBadge';
import RiskBadge from '../../components/ui/RiskBadge';
import SearchBar from '../../components/ui/SearchBar';
import EmptyState from '../../components/ui/EmptyState';
import Modal from '../../components/ui/Modal';
import { formatApiError } from '../../api/client';
import { listDepartmentGrievances, assignOfficerToGrievance, fetchSupervisorDashboard, fetchOfficers, type OfficerSummary } from '../../api/grievances';
import type { Grievance, SupervisorDashboardData } from '../../types';
import { Building2, Eye, UserPlus, Filter } from 'lucide-react';

export function SupervisorDepartmentCasesPage() {
  const navigate = useNavigate();
  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [supData, setSupData] = useState<SupervisorDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [selectedGrievanceId, setSelectedGrievanceId] = useState<string | null>(null);
  const [officerId, setOfficerId] = useState('');
  const [officers, setOfficers] = useState<OfficerSummary[]>([]);
  const [officersLoading, setOfficersLoading] = useState(false);
  const [assigning, setAssigning] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [gList, sData] = await Promise.all([
        listDepartmentGrievances(100, 0),
        fetchSupervisorDashboard().catch(() => null),
      ]);
      setGrievances(gList || []);
      setSupData(sData);
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGrievanceId || !officerId.trim()) return;
    try {
      setAssigning(true);
      await assignOfficerToGrievance(selectedGrievanceId, officerId.trim());
      setAssignModalOpen(false);
      setSelectedGrievanceId(null);
      setOfficerId('');
      await loadData();
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setAssigning(false);
    }
  };

  const openAssignModal = async (grievanceId: string) => {
    setSelectedGrievanceId(grievanceId);
    setOfficerId('');
    setAssignModalOpen(true);
    setOfficersLoading(true);
    try {
      setOfficers((await fetchOfficers()) || []);
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setOfficersLoading(false);
    }
  };

  const filteredGrievances = grievances.filter((g) => {
    const matchesSearch =
      g.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || g.current_state === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <AppLayout title="Department Cases" breadcrumb="Supervisor Workspace">
      <div className="space-y-6">
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">Department Grievance Registry</h1>
            <p className="text-xs text-slate-400 mt-1">
              Full list of active and historic complaints assigned to your department domain.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-xs font-semibold rounded-xl flex items-center justify-between">
            <span>{error}</span>
            <Button size="sm" onClick={loadData}>Retry</Button>
          </div>
        )}

        <Card>
          <CardHeader className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <CardTitle>
              <Building2 className="w-5 h-5 text-amber-400" />
              Department Cases ({filteredGrievances.length})
            </CardTitle>

            <div className="flex flex-wrap items-center gap-3">
              <SearchBar
                value={searchQuery}
                onChange={setSearchQuery}
                placeholder="Search case ID, title..."
              />
              <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-transparent focus:outline-none cursor-pointer text-xs"
                >
                  <option value="ALL">All States</option>
                  <option value="ROUTED">Routed</option>
                  <option value="ASSIGNED">Assigned</option>
<option value="IN_PROGRESS">In Progress</option>
                  <option value="RESOLUTION_SUBMITTED">Pending Review</option>
                  <option value="VERIFICATION">Verification</option>
                  <option value="CLOSED">Closed</option>
                  <option value="REOPENED">Reopened</option>
                </select>
              </div>
            </div>
          </CardHeader>

          <CardContent>
            {loading ? (
              <div className="space-y-4 py-4">
                <div className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
                <div className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
              </div>
            ) : filteredGrievances.length === 0 ? (
              <EmptyState
                icon={<Building2 className="w-10 h-10 text-slate-500" />}
                title="No department cases found"
                description="No grievances match the current department filters."
              />
            ) : (
              <div className="space-y-3">
                {filteredGrievances.map((g) => (
                  <div
                    key={g.id}
                    className="p-4 bg-slate-950/60 border border-slate-800 hover:border-amber-500/50 rounded-2xl transition flex flex-wrap items-center justify-between gap-4"
                  >
                    <div className="space-y-1.5 max-w-xl">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-mono font-bold text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/50">
                          {g.id.substring(0, 8)}
                        </span>
                        <StatusBadge state={g.current_state} size="sm" />
                        <PriorityBadge priority={g.priority} size="sm" />
                        {g.risk_score !== undefined && <RiskBadge score={g.risk_score} size="sm" />}
                      </div>
                      <h3 className="text-base font-bold text-slate-100">{g.title}</h3>
                      <div className="text-xs text-slate-400">
                        Location: {g.location || 'Not specified'} • Submitted: {new Date(g.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/grievances/${g.id}`)}
                        icon={<Eye className="w-3.5 h-3.5" />}
                      >
                        Details
                      </Button>
{(g.current_state === 'ROUTED' || g.current_state === 'REOPENED') && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => openAssignModal(g.id)}
                          icon={<UserPlus className="w-3.5 h-3.5" />}
                        >
                          Assign Officer
                        </Button>
                      )}
                      {g.current_state === 'RESOLUTION_SUBMITTED' && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => navigate(`/grievances/${g.id}`)}
                          icon={<Eye className="w-3.5 h-3.5" />}
                        >
                          Review Resolution
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Modal
          isOpen={assignModalOpen}
          onClose={() => setAssignModalOpen(false)}
          title="Assign Grievance to Officer"
          maxWidth="md"
        >
<form onSubmit={handleAssignSubmit} className="space-y-4">
            <p className="text-xs text-slate-300">
              Select an officer from your department to assign to this grievance. Workload-aware ranking shown below.
            </p>

            {supData?.officer_workload && Object.keys(supData.officer_workload).length > 0 && (
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1 text-xs">
                <span className="font-bold text-slate-300 block">Available Officer Workloads:</span>
                {Object.entries(supData.officer_workload).map(([name, count]) => (
                  <div key={name} className="flex justify-between text-slate-400">
                    <span>{name}</span>
                    <span className="font-mono text-amber-400 font-bold">{count} active cases</span>
                  </div>
                ))}
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Assign Officer *
              </label>
              {officersLoading ? (
                <div className="h-10 bg-slate-800/40 rounded-xl animate-pulse" />
              ) : (
                <select
                  required
                  value={officerId}
                  onChange={(e) => setOfficerId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-100 cursor-pointer"
                >
                  <option value="" disabled>
                    Select an officer...
                  </option>
                  {officers.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.full_name} ({o.email})
                    </option>
                  ))}
                </select>
              )}
              {!officersLoading && officers.length === 0 && (
                <p className="text-[11px] text-red-400 mt-1">No active officers found in this department.</p>
              )}
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setAssignModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" loading={assigning}>
                Confirm Assignment
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </AppLayout>
  );
}

export default SupervisorDepartmentCasesPage;
