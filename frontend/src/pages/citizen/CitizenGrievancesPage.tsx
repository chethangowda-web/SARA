import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '../../layouts/AppLayout';
import Button from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import StatusBadge from '../../components/ui/StatusBadge';
import PriorityBadge from '../../components/ui/PriorityBadge';
import SearchBar from '../../components/ui/SearchBar';
import Modal from '../../components/ui/Modal';
import SubmitGrievanceWizard from '../../components/grievances/SubmitGrievanceWizard';
import EmptyState from '../../components/ui/EmptyState';
import { formatApiError } from '../../api/client';
import { fetchGrievances } from '../../api/grievances';
import type { Grievance } from '../../types';
import { FilePlus, FileText, Eye, Filter } from 'lucide-react';

export function CitizenGrievancesPage() {
  const navigate = useNavigate();
  const [grievances, setGrievances] = useState<Grievance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [wizardOpen, setWizardOpen] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const list = await fetchGrievances(100, 0);
      setGrievances(list || []);
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredGrievances = grievances.filter((g) => {
    const matchesSearch =
      g.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (g.location && g.location.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesStatus = statusFilter === 'ALL' || g.current_state === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <AppLayout title="My Grievances" breadcrumb="Citizen Workspace">
      <div className="space-y-6">
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">Your Submitted Grievances</h1>
            <p className="text-xs text-slate-400 mt-1">
              View full grievance details, track operational status, and inspect resolution timelines.
            </p>
          </div>
          <Button
            variant="primary"
            size="md"
            onClick={() => setWizardOpen(true)}
            icon={<FilePlus className="w-4 h-4" />}
          >
            Submit New Grievance
          </Button>
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
              <FileText className="w-5 h-5 text-blue-400" />
              Grievance List ({filteredGrievances.length})
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
              <div className="space-y-3 py-4">
                <div className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
                <div className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
              </div>
            ) : filteredGrievances.length === 0 ? (
              <EmptyState
                icon={<FileText className="w-10 h-10 text-slate-500" />}
                title="No grievances found"
                description={searchQuery || statusFilter !== 'ALL' ? 'No complaints match your filters.' : 'You have not submitted any grievances yet.'}
                action={
                  <Button variant="primary" size="sm" onClick={() => setWizardOpen(true)} icon={<FilePlus className="w-4 h-4" />}>
                    Submit Grievance
                  </Button>
                }
              />
            ) : (
              <div className="space-y-3">
                {filteredGrievances.map((g) => (
                  <div
                    key={g.id}
                    onClick={() => navigate(`/grievances/${g.id}`)}
                    className="p-4 bg-slate-950/60 border border-slate-800 hover:border-blue-500/50 rounded-2xl transition cursor-pointer flex flex-wrap items-center justify-between gap-4 group"
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
                      <div className="text-xs text-slate-400">
                        Location: {g.location || 'Not specified'} • Submitted: {new Date(g.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    <Button variant="secondary" size="sm" icon={<Eye className="w-3.5 h-3.5" />}>
                      View Details
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Modal
          isOpen={wizardOpen}
          onClose={() => {
            setWizardOpen(false);
            loadData();
          }}
          title="Submit New Grievance"
          maxWidth="2xl"
        >
          <SubmitGrievanceWizard
            onClose={() => {
              setWizardOpen(false);
              loadData();
            }}
          />
        </Modal>
      </div>
    </AppLayout>
  );
}

export default CitizenGrievancesPage;
