import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import type { Grievance } from '../../types';
import Button from './Button';
import { 
  acknowledgeGrievance, 
  startGrievanceWork, 
  resolveGrievance,
  assignOfficerToGrievance,
  routeGrievanceToDepartment,
  fetchDepartments
} from '../../api/grievances';
import { formatApiError, apiFetch } from '../../api/client';
import { CheckCircle, Play, Send, Users, Building2 } from 'lucide-react';

interface GrievanceWorkflowProps {
  grievance: Grievance;
  onUpdate: () => void;
}

export function GrievanceWorkflow({ grievance, onUpdate }: GrievanceWorkflowProps) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [departments, setDepartments] = useState<any[]>([]);
  const [selectedDept, setSelectedDept] = useState('');
  const [officers, setOfficers] = useState<any[]>([]);
  const [selectedOfficer, setSelectedOfficer] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');

  useEffect(() => {
    if (user?.role === 'ADMIN' && grievance.current_state === 'CLASSIFIED') {
      fetchDepartments().then(setDepartments).catch(console.error);
    }
    if (user?.role === 'SUPERVISOR' && (grievance.current_state === 'ROUTED' || grievance.current_state === 'ASSIGNED')) {
      // Fetch officers in the supervisor's department
      apiFetch<any[]>('/admin/users?role=OFFICER')
        .then(res => setOfficers(res.filter(u => u.department_id === user.department_id)))
        .catch(console.error);
    }
  }, [user, grievance.current_state]);

  if (!user) return null;

  const handleAction = async (actionFn: () => Promise<any>) => {
    try {
      setLoading(true);
      setError(null);
      await actionFn();
      onUpdate();
    } catch (err: any) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const isAdmin = user.role === 'ADMIN';
  const isSupervisor = user.role === 'SUPERVISOR';
  const isOfficer = user.role === 'OFFICER';
  
  const state = grievance.current_state;

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 shadow-lg mb-6">
      <h3 className="text-lg font-bold text-white mb-4">Workflow Actions</h3>
      
      {error && (
        <div className="mb-4 p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-lg">
          {error}
        </div>
      )}

      {/* ADMIN ROUTING */}
      {isAdmin && (state === 'SUBMITTED' || state === 'CLASSIFIED') && (
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <label className="block text-xs font-bold text-slate-400 mb-1">Route to Department</label>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-slate-200"
            >
              <option value="">Select Department...</option>
              {departments.map(d => (
                <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
              ))}
            </select>
          </div>
          <Button 
            variant="primary" 
            disabled={!selectedDept} 
            loading={loading}
            onClick={() => handleAction(() => routeGrievanceToDepartment(grievance.id, selectedDept))}
            icon={<Building2 className="w-4 h-4" />}
          >
            Route Grievance
          </Button>
        </div>
      )}

      {/* SUPERVISOR ASSIGNMENT */}
      {isSupervisor && (state === 'ROUTED' || state === 'ASSIGNED') && (
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <label className="block text-xs font-bold text-slate-400 mb-1">Assign to Officer</label>
            <select
              value={selectedOfficer}
              onChange={(e) => setSelectedOfficer(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-slate-200"
            >
              <option value="">Select Officer...</option>
              {officers.map(o => (
                <option key={o.id} value={o.id}>{o.full_name} ({o.email})</option>
              ))}
            </select>
          </div>
          <Button 
            variant="primary" 
            disabled={!selectedOfficer} 
            loading={loading}
            onClick={() => handleAction(() => assignOfficerToGrievance(grievance.id, selectedOfficer))}
            icon={<Users className="w-4 h-4" />}
          >
            {state === 'ASSIGNED' ? 'Reassign' : 'Assign'} Officer
          </Button>
        </div>
      )}

      {/* OFFICER ACTIONS */}
      {isOfficer && (
        <div className="space-y-4">
          {state === 'ASSIGNED' && (
            <div>
              <p className="text-sm text-slate-300 mb-3">You have been assigned to this grievance. Please acknowledge receipt to begin SLA tracking.</p>
              <Button 
                variant="primary" 
                loading={loading}
                onClick={() => handleAction(() => acknowledgeGrievance(grievance.id))}
                icon={<CheckCircle className="w-4 h-4" />}
              >
                Acknowledge Assignment
              </Button>
            </div>
          )}
          
          {state === 'ACKNOWLEDGED' && (
            <div>
              <p className="text-sm text-slate-300 mb-3">Ready to begin work? Start the resolution process.</p>
              <Button 
                variant="success" 
                loading={loading}
                onClick={() => handleAction(() => startGrievanceWork(grievance.id))}
                icon={<Play className="w-4 h-4" />}
              >
                Start Work
              </Button>
            </div>
          )}

          {state === 'IN_PROGRESS' && (
            <div className="space-y-3">
              <label className="block text-xs font-bold text-slate-400">Submit Resolution</label>
              <textarea
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="Enter detailed resolution notes here..."
                className="w-full h-24 bg-slate-950 border border-slate-700 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-500 resize-none"
              />
              <Button 
                variant="success" 
                disabled={!resolutionNotes.trim()} 
                loading={loading}
                onClick={() => handleAction(() => resolveGrievance(grievance.id, resolutionNotes))}
                icon={<Send className="w-4 h-4" />}
              >
                Submit Resolution for Verification
              </Button>
            </div>
          )}
        </div>
      )}

      {/* IF NOTHING TO DO */}
      {((isAdmin && state !== 'SUBMITTED' && state !== 'CLASSIFIED') ||
        (isSupervisor && state !== 'ROUTED' && state !== 'ASSIGNED') ||
        (isOfficer && !['ASSIGNED', 'ACKNOWLEDGED', 'IN_PROGRESS'].includes(state))) && (
          <div className="text-sm text-slate-400 italic">
            No workflow actions available for your role in the current state.
          </div>
      )}
    </div>
  );
}

export default GrievanceWorkflow;
