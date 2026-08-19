import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import StatCard from '../components/ui/StatCard';
import Button from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import StatusBadge from '../components/ui/StatusBadge';
import PriorityBadge from '../components/ui/PriorityBadge';
import RiskBadge from '../components/ui/RiskBadge';
import SearchBar from '../components/ui/SearchBar';
import Modal from '../components/ui/Modal';
import EmptyState from '../components/ui/EmptyState';
import { formatApiError } from '../api/client';
import {
  fetchOfficerDashboard,
  fetchGrievances,
  acknowledgeGrievance,
  startGrievanceWork,
  resolveGrievance,
  holdGrievance,
  resumeGrievance,
  requestAbortGrievance,
} from '../api/grievances';
import type { OfficerDashboardData, Grievance } from '../types';
import { useAuth } from '../context/AuthContext';
import {
  Briefcase,
  Clock,
  AlertTriangle,
  Flame,
  Eye,
  Send,
  Play,
  Check,
  Sparkles,
} from 'lucide-react';

export function OfficerDashboard() {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState<OfficerDashboardData | null>(null);
  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [loading, setLoading] = useState(true);
  const [switchingDept, setSwitchingDept] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');

  const [resolveModalOpen, setResolveModalOpen] = useState(false);
  const [targetGrievanceId, setTargetGrievanceId] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const [holdModalOpen, setHoldModalOpen] = useState(false);
  const [abortModalOpen, setAbortModalOpen] = useState(false);
  const [holdReason, setHoldReason] = useState('');
  const [holdDate, setHoldDate] = useState('');
  const [abortReason, setAbortReason] = useState('');
  const [actionNote, setActionNote] = useState('');

  const switchDepartmentOfficer = async (email: string) => {
    try {
      setSwitchingDept(true);
      setError(null);
      await login(email, 'SARA_demo_pass_2026');
      await loadData();
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setSwitchingDept(false);
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [dashData, gList] = await Promise.all([
        fetchOfficerDashboard(),
        fetchGrievances(50, 0),
      ]);
      setStats(dashData);
      setGrievances(gList || []);
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAcknowledge = async (id: string) => {
    try {
      setActionLoading(true);
      setError(null);
      await acknowledgeGrievance(id);
      await loadData();
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartWork = async (id: string, currentState?: string) => {
    try {
      setActionLoading(true);
      setError(null);
      if (currentState === 'ASSIGNED') {
        // Valid sequence per state machine: ASSIGNED -> ACKNOWLEDGED -> IN_PROGRESS
        await acknowledgeGrievance(id);
      }
      await startGrievanceWork(id);
      await loadData();
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetGrievanceId || !resolutionNotes.trim()) return;
    try {
      setActionLoading(true);
      setError(null);
      await resolveGrievance(targetGrievanceId, resolutionNotes);
      setResolveModalOpen(false);
      setTargetGrievanceId(null);
      setResolutionNotes('');
      await loadData();
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleHoldSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetGrievanceId || !holdReason || !holdDate) return;
    try {
      setActionLoading(true);
      setError(null);
      await holdGrievance(targetGrievanceId, holdReason, new Date(holdDate).toISOString(), actionNote);
      setHoldModalOpen(false);
      setTargetGrievanceId(null);
      setHoldReason('');
      setHoldDate('');
      setActionNote('');
      await loadData();
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async (id: string) => {
    try {
      setActionLoading(true);
      setError(null);
      await resumeGrievance(id);
      await loadData();
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleAbortSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetGrievanceId || !abortReason) return;
    try {
      setActionLoading(true);
      setError(null);
      await requestAbortGrievance(targetGrievanceId, abortReason, actionNote);
      setAbortModalOpen(false);
      setTargetGrievanceId(null);
      setAbortReason('');
      setActionNote('');
      await loadData();
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const renderSlaTimer = (expectedResolution?: string | null, isEscalated?: boolean) => {
    if (!expectedResolution) {
      return <span className="text-slate-500 text-xs font-mono">24h Standard SLA</span>;
    }
    const target = new Date(expectedResolution).getTime();
    const now = Date.now();
    const diffMs = target - now;

    if (diffMs <= 0 || isEscalated) {
      const overdueHours = Math.abs(Math.round(diffMs / (1000 * 60 * 60)));
      return (
        <span className="px-2 py-0.5 rounded bg-red-950/80 text-red-400 font-mono text-xs font-bold border border-red-800">
          {overdueHours > 0 ? `${overdueHours}h overdue` : 'SLA Breached'}
        </span>
      );
    }

    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const mins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    return (
      <span className="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 font-mono text-xs font-semibold border border-emerald-800">
        {hours}h {mins}m remaining
      </span>
    );
  };

  const filteredGrievances = grievances.filter(
    (g) =>
      g.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <AppLayout title="Officer Operational Workspace" breadcrumb="Workspace">
      <div className="space-y-6">
        <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-purple-950/60 via-slate-900 to-blue-950/40 border border-slate-800/80 shadow-2xl flex flex-wrap items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-950 border border-purple-800 text-purple-300 text-xs font-bold uppercase tracking-wider">
              Authorized Officer Workspace
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Officer: {user?.full_name}
            </h1>
            <p className="text-sm text-slate-400 leading-relaxed">
              <strong className="text-purple-300 font-semibold">{stats?.department_name || user?.department_name || 'Department'}</strong>
              {' · Manage your assigned grievance pipeline, adhere to SLA countdowns, log evidence, and submit field resolutions.'}
            </p>
          </div>
        </div>

        {/* Quick Department Switcher for Demo Evaluation */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              Switch Officer Queue by Department:
            </span>
            {switchingDept && <span className="text-xs text-purple-400 font-mono animate-pulse">Switching officer session...</span>}
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              { name: '⚡ Electrical', email: 'officer@sara.gov' },
              { name: '💧 Water', email: 'water.officer@sara.gov' },
              { name: '🛣️ Roads', email: 'roads.officer01@sara.gov' },
              { name: '🧹 Sanitation', email: 'sanitation.officer@sara.gov' },
              { name: '🚮 Waste', email: 'waste.officer01@sara.gov' },
              { name: '🌊 Drainage', email: 'drainage.officer01@sara.gov' },
              { name: '💡 Street Light', email: 'streetlighting.officer01@sara.gov' },
              { name: '🏥 Health', email: 'publichealth.officer01@sara.gov' },
            ].map((d) => {
              const isActive = user?.email === d.email;
              return (
                <button
                  key={d.email}
                  disabled={switchingDept}
                  onClick={() => switchDepartmentOfficer(d.email)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition border ${
                    isActive
                      ? 'bg-purple-600 border-purple-400 text-white shadow-lg shadow-purple-900/50'
                      : 'bg-slate-950/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-800'
                  }`}
                >
                  {d.name}
                </button>
              );
            })}
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-xs font-semibold rounded-xl flex items-center justify-between">
            <span>{error}</span>
            <button onClick={loadData} className="underline font-bold text-red-200">
              Retry
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Assigned Workload"
            value={loading ? '...' : typeof stats?.assigned_grievances === 'number' ? stats.assigned_grievances : grievances.length}
            colorScheme="purple"
            icon={<Briefcase className="w-5 h-5" />}
            subtitle="Active assigned cases"
          />
          <StatCard
            title="Pending Acknowledgement"
            value={loading ? '...' : stats?.pending_acknowledgement || 0}
            colorScheme="amber"
            icon={<AlertTriangle className="w-5 h-5" />}
            subtitle="Action required"
          />
          <StatCard
            title="In Progress"
            value={loading ? '...' : stats?.in_progress || 0}
            colorScheme="blue"
            icon={<Clock className="w-5 h-5" />}
            subtitle="Under active work"
          />
          <StatCard
            title="High Risk & Overdue"
            value={loading ? '...' : (stats?.overdue_grievances || 0) + (stats?.high_risk_grievances || 0)}
            colorScheme="red"
            icon={<Flame className="w-5 h-5" />}
            subtitle="Critical SLA priority"
          />
        </div>

        <Card>
          <CardHeader className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <CardTitle>
              <Briefcase className="w-5 h-5 text-purple-400" />
              Assigned Cases Pipeline ({filteredGrievances.length})
            </CardTitle>

            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search case ID, title..."
            />
          </CardHeader>

          <CardContent>
            {loading ? (
              <div className="space-y-4 py-4">
                <div className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
                <div className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
              </div>
            ) : filteredGrievances.length === 0 ? (
              <EmptyState
                icon={<Briefcase className="w-10 h-10 text-slate-500" />}
                title="No assigned cases"
                description="You currently have no active grievances assigned to your queue."
              />
            ) : (
              <div className="space-y-4">
                {filteredGrievances.map((g) => (
                  <div
                    key={g.id}
                    className="p-5 bg-slate-950/60 border border-slate-800 hover:border-purple-500/50 rounded-2xl transition space-y-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/60 pb-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-mono font-bold text-purple-400 bg-purple-950/60 px-2.5 py-0.5 rounded border border-purple-800/50">
                          {g.id.substring(0, 8)}
                        </span>
                        <StatusBadge state={g.current_state} size="sm" />
                        <PriorityBadge priority={g.priority} size="sm" />
                        {g.risk_score !== undefined && <RiskBadge score={g.risk_score} size="sm" />}
                      </div>

                      <div>{renderSlaTimer(g.expected_resolution, g.escalated ?? false)}</div>
                    </div>

                    <div className="space-y-1">
                      <h3 className="text-base font-bold text-slate-100">{g.title}</h3>
                      <p className="text-xs text-slate-400 line-clamp-2">{g.description}</p>
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                      <div className="text-xs text-slate-500 font-mono">
                        Location: {g.location || 'Not specified'}
                      </div>

                      <div className="flex items-center gap-2 flex-wrap">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigate(`/grievances/${g.id}`)}
                          icon={<Eye className="w-3.5 h-3.5" />}
                        >
                          Details
                        </Button>

                        {g.current_state === 'ASSIGNED' && (
                          <>
                            <Button
                              variant="primary"
                              size="sm"
                              loading={actionLoading}
                              onClick={() => handleAcknowledge(g.id)}
                              icon={<Check className="w-3.5 h-3.5" />}
                            >
                              Acknowledge
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              loading={actionLoading}
                              onClick={() => handleStartWork(g.id, g.current_state)}
                              icon={<Play className="w-3.5 h-3.5" />}
                            >
                              Start Work
                            </Button>
                          </>
                        )}

                        {g.current_state === 'ACKNOWLEDGED' && (
                          <Button
                            variant="primary"
                            size="sm"
                            loading={actionLoading}
                            onClick={() => handleStartWork(g.id, g.current_state)}
                            icon={<Play className="w-3.5 h-3.5" />}
                          >
                            Start Work
                          </Button>
                        )}

                        {g.current_state === 'IN_PROGRESS' && (
                          <Button
                            variant="success"
                            size="sm"
                            onClick={() => {
                              setTargetGrievanceId(g.id);
                              setResolveModalOpen(true);
                            }}
                            icon={<Send className="w-3.5 h-3.5" />}
                          >
                            Submit Resolution
                          </Button>
                        )}
                        
                        {(g.current_state as string) === 'ON_HOLD' && (
                          <Button
                            variant="primary"
                            size="sm"
                            loading={actionLoading}
                            onClick={() => handleResume(g.id)}
                            icon={<Play className="w-3.5 h-3.5" />}
                          >
                            Resume Work
                          </Button>
                        )}

                        {['ASSIGNED', 'ACKNOWLEDGED', 'IN_PROGRESS'].includes(g.current_state) && (
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setTargetGrievanceId(g.id);
                                setHoldModalOpen(true);
                              }}
                            >
                              Hold
                            </Button>
                            <Button
                              variant="outline"
                              className="text-red-400 border-red-800 hover:bg-red-950/50"
                              size="sm"
                              onClick={() => {
                                setTargetGrievanceId(g.id);
                                setAbortModalOpen(true);
                              }}
                            >
                              Abort
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Modal
          isOpen={resolveModalOpen}
          onClose={() => setResolveModalOpen(false)}
          title="Submit Grievance Resolution"
          maxWidth="md"
        >
          <form onSubmit={handleResolveSubmit} className="space-y-4">
            <p className="text-xs text-slate-300">
              Provide comprehensive field resolution notes explaining the action taken to resolve this grievance.
            </p>
            <textarea
              required
              rows={4}
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="e.g. Replaced leaking valve and tested pressure for 30 minutes. Water flow fully restored..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100"
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setResolveModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="success" size="sm" loading={actionLoading}>
                Submit Resolution
              </Button>
            </div>
          </form>
        </Modal>

        <Modal
          isOpen={holdModalOpen}
          onClose={() => setHoldModalOpen(false)}
          title="Place Grievance on Hold"
          maxWidth="md"
        >
          <form onSubmit={handleHoldSubmit} className="space-y-4">
            <p className="text-xs text-slate-300">
              Provide a valid reason and an expected date to resume work.
            </p>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Hold Reason</label>
              <select
                required
                value={holdReason}
                onChange={(e) => setHoldReason(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100"
              >
                <option value="">Select reason...</option>
                <option value="WAITING_ON_CITIZEN">Waiting on Citizen</option>
                <option value="WAITING_ON_MATERIALS">Waiting on Materials</option>
                <option value="WEATHER_CONDITIONS">Weather Conditions</option>
                <option value="SAFETY_HAZARD">Safety Hazard</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Expected Resume Date/Time</label>
              <input
                type="datetime-local"
                required
                value={holdDate}
                onChange={(e) => setHoldDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Optional Note</label>
              <textarea
                rows={2}
                value={actionNote}
                onChange={(e) => setActionNote(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setHoldModalOpen(false)}>Cancel</Button>
              <Button type="submit" variant="primary" size="sm" loading={actionLoading}>Place on Hold</Button>
            </div>
          </form>
        </Modal>

        <Modal
          isOpen={abortModalOpen}
          onClose={() => setAbortModalOpen(false)}
          title="Request Grievance Abort"
          maxWidth="md"
        >
          <form onSubmit={handleAbortSubmit} className="space-y-4">
            <p className="text-xs text-slate-300">
              Request supervisor approval to abort this grievance. This action halts all SLA timers.
            </p>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Abort Reason</label>
              <select
                required
                value={abortReason}
                onChange={(e) => setAbortReason(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100"
              >
                <option value="">Select reason...</option>
                <option value="DUPLICATE_ISSUE">Duplicate Issue</option>
                <option value="INVALID_COMPLAINT">Invalid Complaint</option>
                <option value="OUT_OF_JURISDICTION">Out of Jurisdiction</option>
                <option value="UNRESOLVABLE_TECHNICAL">Unresolvable Technical/Legal Block</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Detailed Explanation</label>
              <textarea
                required
                rows={3}
                value={actionNote}
                onChange={(e) => setActionNote(e.target.value)}
                placeholder="Explain why this grievance must be aborted..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setAbortModalOpen(false)}>Cancel</Button>
              <Button type="submit" variant="primary" className="bg-red-600 hover:bg-red-700" size="sm" loading={actionLoading}>Submit Abort Request</Button>
            </div>
          </form>
        </Modal>
      </div>
    </AppLayout>
  );
}

export default OfficerDashboard;
