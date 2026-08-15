import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import StatCard from '../components/ui/StatCard';
import Button from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import StatusBadge from '../components/ui/StatusBadge';
import PriorityBadge from '../components/ui/PriorityBadge';
import SearchBar from '../components/ui/SearchBar';
import Modal from '../components/ui/Modal';
import SubmitGrievanceWizard from '../components/grievances/SubmitGrievanceWizard';
import EmptyState from '../components/ui/EmptyState';
import { formatApiError } from '../api/client';
import { fetchCitizenDashboard } from '../api/grievances';
import type { CitizenDashboardData, Grievance } from '../types';
import { useAuth } from '../context/AuthContext';
import {
  FilePlus,
  FileText,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Eye,
  Filter,
} from 'lucide-react';

export function CitizenDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [data, setData] = useState<CitizenDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Submit Wizard Modal
  const [wizardOpen, setWizardOpen] = useState(false);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchCitizenDashboard();
      setData(res);
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const grievancesList: Grievance[] = data?.recent_grievances || [];

  const filteredGrievances = grievancesList.filter((g) => {
    const matchesSearch =
      g.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (g.location && g.location.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus = statusFilter === 'ALL' || g.current_state === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <AppLayout title="Citizen Dashboard" breadcrumb="Overview">
      <div className="space-y-6">
        {/* Welcome Header & Action Banner */}
        <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-blue-950/60 via-slate-900 to-emerald-950/40 border border-slate-800/80 shadow-2xl flex flex-wrap items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-950 border border-blue-800 text-blue-400 text-xs font-bold uppercase tracking-wider">
              Citizen Portal
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Welcome back, {user?.full_name || 'Citizen'}
            </h1>
            <p className="text-sm text-slate-400 leading-relaxed">
              Track your submitted complaints in real-time, view SLA resolution progress, and verify completed resolutions.
            </p>
          </div>

          <Button
            variant="primary"
            size="lg"
            onClick={() => setWizardOpen(true)}
            icon={<FilePlus className="w-5 h-5" />}
          >
            Report a Grievance
          </Button>
        </div>

        {error && (
          <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-xs font-semibold rounded-xl flex items-center justify-between">
            <span>{error}</span>
            <button onClick={loadDashboard} className="underline font-bold text-red-200">
              Retry
            </button>
          </div>
        )}

        {/* Dashboard Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Grievances"
            value={loading ? '...' : data?.total_grievances || 0}
            colorScheme="blue"
            icon={<FileText className="w-5 h-5" />}
            subtitle="Lifetime complaints"
          />
          <StatCard
            title="Active Cases"
            value={loading ? '...' : data?.in_progress || 0}
            colorScheme="amber"
            icon={<Clock className="w-5 h-5" />}
            subtitle="Under investigation"
          />
          <StatCard
            title="Awaiting Verification"
            value={loading ? '...' : data?.awaiting_verification || 0}
            colorScheme="purple"
            icon={<AlertTriangle className="w-5 h-5" />}
            subtitle="Action required"
          />
          <StatCard
            title="Resolved / Closed"
            value={loading ? '...' : data?.closed || 0}
            colorScheme="emerald"
            icon={<CheckCircle2 className="w-5 h-5" />}
            subtitle="Verified complete"
          />
        </div>

        {/* Grievance List Container */}
        <Card>
          <CardHeader className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <CardTitle>
              <FileText className="w-5 h-5 text-blue-400" />
              Your Grievances Overview
            </CardTitle>

            <div className="flex flex-wrap items-center gap-3">
              <SearchBar
                value={searchQuery}
                onChange={setSearchQuery}
                placeholder="Search title, ID, location..."
              />

              <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-transparent focus:outline-none cursor-pointer text-xs"
                >
                  <option value="ALL">All States</option>
                  <option value="SUBMITTED">Submitted</option>
                  <option value="IN_PROGRESS">In Progress</option>
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
                <div className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
              </div>
            ) : filteredGrievances.length === 0 ? (
              <EmptyState
                icon={<FileText className="w-10 h-10 text-slate-500" />}
                title="No grievances found"
                description={
                  searchQuery || statusFilter !== 'ALL'
                    ? 'No complaints match your current search and status filters.'
                    : 'You have not submitted any grievances yet. Click "Report a Grievance" above to log your first issue.'
                }
                action={
                  <Button variant="primary" size="sm" onClick={() => setWizardOpen(true)} icon={<FilePlus className="w-4 h-4" />}>
                    Report a Grievance
                  </Button>
                }
              />
            ) : (
              <div className="space-y-3">
                {filteredGrievances.map((g) => (
                  <div
                    key={g.id}
                    onClick={() => navigate(`/grievances/${g.id}`)}
                    className="p-5 bg-slate-950/60 border border-slate-800 hover:border-blue-500/50 rounded-2xl transition cursor-pointer flex flex-wrap items-center justify-between gap-4 group"
                  >
                    <div className="space-y-1.5 max-w-xl">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-mono font-bold text-blue-400 bg-blue-950/60 px-2 py-0.5 rounded border border-blue-800/50">
                          {g.id.substring(0, 8)}
                        </span>
                        <StatusBadge state={g.current_state} size="sm" />
                        <PriorityBadge priority={g.priority} size="sm" />
                      </div>

                      <h3 className="text-base font-bold text-slate-100 group-hover:text-blue-300 transition">
                        {g.title}
                      </h3>

                      <div className="flex items-center gap-4 text-xs text-slate-400 font-medium">
                        <span>Submitted: {new Date(g.created_at).toLocaleDateString()}</span>
                        {g.location && <span>• {g.location}</span>}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <Button variant="secondary" size="sm" icon={<Eye className="w-3.5 h-3.5" />}>
                        View Details
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Submit Grievance Multi-Step Wizard Modal */}
        <Modal
          isOpen={wizardOpen}
          onClose={() => {
            setWizardOpen(false);
            loadDashboard();
          }}
          title="Submit New Grievance"
          maxWidth="2xl"
        >
          <SubmitGrievanceWizard
            onClose={() => {
              setWizardOpen(false);
              loadDashboard();
            }}
          />
        </Modal>
      </div>
    </AppLayout>
  );
}

export default CitizenDashboard;
