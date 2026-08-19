import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '../../layouts/AppLayout';
import Button from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import StatusBadge from '../../components/ui/StatusBadge';
import PriorityBadge from '../../components/ui/PriorityBadge';
import RiskBadge from '../../components/ui/RiskBadge';
import SearchBar from '../../components/ui/SearchBar';
import Modal from '../../components/ui/Modal';
import EmptyState from '../../components/ui/EmptyState';
import { formatApiError } from '../../api/client';
import {
  fetchGrievances,
  acknowledgeGrievance,
  startGrievanceWork,
  resolveGrievance,
} from '../../api/grievances';
import type { Grievance } from '../../types';
import {
  Briefcase,
  Eye,
  Send,
  Play,
  Check,
  Filter,
} from 'lucide-react';

export function OfficerAssignedCasesPage() {
  const navigate = useNavigate();
  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const [resolveModalOpen, setResolveModalOpen] = useState(false);
  const [targetGrievanceId, setTargetGrievanceId] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const gList = await fetchGrievances(100, 0);
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

  const filteredGrievances = grievances.filter((g) => {
    const matchesSearch =
      g.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || g.current_state === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <AppLayout title="Assigned Cases" breadcrumb="Officer Workspace">
      <div className="space-y-6">
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">Assigned Grievance Pipeline</h1>
            <p className="text-xs text-slate-400 mt-1">
              Acknowledge incoming assignments, log field work progress, and submit verified resolution notes.
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
              <Briefcase className="w-5 h-5 text-purple-400" />
              Assigned Cases ({filteredGrievances.length})
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
                  <option value="ASSIGNED">Assigned</option>
                  <option value="ACKNOWLEDGED">Acknowledged</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="VERIFICATION">Verification</option>
                  <option value="CLOSED">Closed</option>
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
                icon={<Briefcase className="w-10 h-10 text-slate-500" />}
                title="No assigned cases found"
                description="No active cases match your search or filters."
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
                    </div>

                    <div className="space-y-1">
                      <h3 className="text-base font-bold text-slate-100">{g.title}</h3>
                      <p className="text-xs text-slate-400 line-clamp-2">{g.description}</p>
                    </div>

<div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 font-mono">
                        <span>Location: {g.location || 'Not specified'}</span>
                        {g.department_name && (
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                            {g.department_name}
                          </span>
                        )}
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
      </div>
    </AppLayout>
  );
}

export default OfficerAssignedCasesPage;
