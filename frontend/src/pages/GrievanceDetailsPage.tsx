import React, { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import StatusBadge from '../components/ui/StatusBadge';
import PriorityBadge from '../components/ui/PriorityBadge';
import RiskBadge from '../components/ui/RiskBadge';
import Button from '../components/ui/Button';
import Timeline from '../components/ui/Timeline';
import Avatar from '../components/ui/Avatar';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import GrievanceWorkflow from '../components/ui/GrievanceWorkflow';
import { formatApiError } from '../api/client';
import {
  fetchGrievanceById,
  fetchGrievanceTimeline,
  fetchEvidenceList,
  fetchComments,
  addComment,
  uploadEvidence,
  verifyGrievanceResolution,
} from '../api/grievances';
import type { Grievance, GrievanceEvent, Evidence, Comment } from '../types';
import { useAuth } from '../context/AuthContext';
import {
  ArrowLeft,
  Clock,
  Sparkles,
  Paperclip,
  Send,
  Download,
  Upload,
  CheckCircle2,
  XCircle,
  FileText,
  ShieldAlert,
} from 'lucide-react';

export function GrievanceDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [grievance, setGrievance] = useState<Grievance | null>(null);
  const [timeline, setTimeline] = useState<GrievanceEvent[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);

  // Comment input
  const [newComment, setNewComment] = useState('');
  const [commentSubmitting, setCommentSubmitting] = useState(false);

  // Evidence upload modal
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileDescription, setFileDescription] = useState('');
  const [uploading, setUploading] = useState(false);

  // Reject Resolution modal
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [verifySubmitting, setVerifySubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      const [gData, tData, eData, cData] = await Promise.all([
        fetchGrievanceById(id),
        fetchGrievanceTimeline(id).catch(() => []),
        fetchEvidenceList(id).catch(() => []),
        fetchComments(id).catch(() => []),
      ]);
      setGrievance(gData);
      setTimeline(tData || []);
      setEvidence(eData || []);
      setComments(cData || []);
    } catch (err: any) {
      setActionError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !newComment.trim()) return;
    try {
      setCommentSubmitting(true);
      await addComment({ id, comment: newComment });
      setNewComment('');
      const updatedComments = await fetchComments(id);
      setComments(updatedComments);
    } catch (err: any) {
      alert(formatApiError(err));
    } finally {
      setCommentSubmitting(false);
    }
  };

  const handleUploadFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !selectedFile) return;
    try {
      setUploading(true);
      await uploadEvidence({ id, file: selectedFile, description: fileDescription });
      setUploadModalOpen(false);
      setSelectedFile(null);
      setFileDescription('');
      const updatedEvidence = await fetchEvidenceList(id);
      setEvidence(updatedEvidence);
    } catch (err: any) {
      alert(formatApiError(err));
    } finally {
      setUploading(false);
    }
  };

  const handleVerify = async (accept: boolean) => {
    if (!id) return;
    if (!accept && !rejectReason.trim()) {
      alert('Please provide an explanation for rejecting the resolution.');
      return;
    }
    try {
      setVerifySubmitting(true);
      await verifyGrievanceResolution(id, accept, rejectReason);
      setRejectModalOpen(false);
      setRejectReason('');
      await loadData();
    } catch (err: any) {
      alert(formatApiError(err));
    } finally {
      setVerifySubmitting(false);
    }
  };

  if (loading) {
    return (
      <AppLayout title="Grievance Details" breadcrumb="Track Case">
        <div className="text-center py-20 text-slate-400">Loading grievance specifications...</div>
      </AppLayout>
    );
  }

  if (!grievance) {
    return (
      <AppLayout title="Grievance Details" breadcrumb="Track Case">
        <div className="text-center py-20 space-y-4">
          <div className="text-red-400 text-lg font-bold">Grievance Not Found or Access Restricted</div>
          <Button onClick={() => navigate(-1)} icon={<ArrowLeft className="w-4 h-4" />}>
            Back to Dashboard
          </Button>
        </div>
      </AppLayout>
    );
  }

  const isCitizen = user?.role === 'CITIZEN';
  const canVerify = isCitizen && (grievance.current_state === 'VERIFICATION' || grievance.current_state === 'RESOLUTION_SUBMITTED');

  return (
    <AppLayout title={`Grievance ${grievance.id.substring(0, 8)}`} breadcrumb="Case Details">
      <div className="space-y-6">
        {/* Top Header Card */}
        {actionError && (
          <div className="p-4 bg-red-950/60 border border-red-800 text-red-300 text-xs font-semibold rounded-xl flex items-center justify-between">
            <span>{actionError}</span>
            <button onClick={loadData} className="underline font-bold text-red-200">
              Retry
            </button>
          </div>
        )}
        <Card className="p-6 bg-slate-900 border-slate-800">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-2 max-w-3xl">
              <button
                onClick={() => navigate(-1)}
                className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition mb-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back to Overview</span>
              </button>

              <div className="flex items-center gap-3">
                <span className="text-xs font-mono px-2.5 py-1 bg-slate-950 border border-slate-800 rounded-lg text-blue-400 font-bold">
                  {grievance.id}
                </span>
                <StatusBadge state={grievance.current_state} />
                <PriorityBadge priority={grievance.priority} />
                {grievance.risk_score !== undefined && <RiskBadge score={grievance.risk_score} />}
              </div>

              <h1 className="text-xl sm:text-2xl font-black text-white">{grievance.title}</h1>
              <p className="text-sm text-slate-300 leading-relaxed">{grievance.description}</p>
            </div>

            {/* Quick Meta */}
            <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800 space-y-2 text-xs text-slate-400 min-w-[220px]">
              <div>
                <span className="text-slate-500 block">Submitted On</span>
                <span className="font-semibold text-slate-200">{new Date(grievance.created_at).toLocaleString()}</span>
              </div>
              {grievance.location && (
                <div>
                  <span className="text-slate-500 block">Location</span>
                  <span className="font-semibold text-slate-200">{grievance.location}</span>
                </div>
              )}
              {grievance.expected_resolution && (
                <div>
                  <span className="text-slate-500 block">Target Resolution</span>
                  <span className="font-semibold text-emerald-400">{new Date(grievance.expected_resolution).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Workflow Actions (Admin, Supervisor, Officer) */}
        {!isCitizen && (
          <GrievanceWorkflow grievance={grievance} onUpdate={loadData} />
        )}

        {/* Citizen Resolution Verification Alert Panel */}
        {canVerify && (
          <div className="p-6 rounded-2xl bg-amber-950/40 border-2 border-amber-500/50 shadow-2xl space-y-4 animate-pulse">
            <div className="flex items-center gap-3 text-amber-300 font-bold text-base">
              <ShieldAlert className="w-6 h-6 text-amber-400 shrink-0" />
              <span>Resolution Verification Action Required</span>
            </div>
            <p className="text-sm text-slate-200">
              The assigned department has submitted a resolution for your complaint. Please verify if the issue has been completely fixed on-ground.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Button
                variant="success"
                size="md"
                loading={verifySubmitting}
                onClick={() => handleVerify(true)}
                icon={<CheckCircle2 className="w-4 h-4" />}
              >
                Accept Resolution & Close Case
              </Button>
              <Button
                variant="danger"
                size="md"
                onClick={() => setRejectModalOpen(true)}
                icon={<XCircle className="w-4 h-4" />}
              >
                Reject Resolution & Reopen
              </Button>
            </div>
          </div>
        )}

        {/* Grid Container */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Audit Timeline & Evidence */}
          <div className="lg:col-span-2 space-y-6">
            {/* Timeline */}
            <Card>
              <CardHeader>
                <CardTitle>
                  <Clock className="w-5 h-5 text-blue-400" />
                  Chronological Governance Audit Log
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Timeline events={timeline} />
              </CardContent>
            </Card>

            {/* Evidence Gallery */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>
                  <Paperclip className="w-5 h-5 text-purple-400" />
                  Uploaded Evidence ({evidence.length})
                </CardTitle>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setUploadModalOpen(true)}
                  icon={<Upload className="w-3.5 h-3.5" />}
                >
                  Upload Evidence
                </Button>
              </CardHeader>
              <CardContent>
                {evidence.length === 0 ? (
                  <div className="text-center py-6 text-slate-500 text-sm">No evidence files uploaded yet.</div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {evidence.map((ev) => (
                      <div key={ev.id} className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2.5 truncate">
                          <FileText className="w-4 h-4 text-blue-400 shrink-0" />
                          <div className="truncate">
                            <div className="font-bold text-slate-200 truncate">{ev.file_name}</div>
                            <div className="text-[10px] text-slate-500">{new Date(ev.uploaded_at).toLocaleDateString()}</div>
                          </div>
                        </div>
                        <a
                          href={`http://localhost:8000/api/v1/grievances/${grievance.id}/evidence/${ev.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                          className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-blue-400"
                          title="Download Evidence"
                        >
                          <Download className="w-4 h-4" />
                        </a>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column: AI Advisory & Conversational Comments */}
          <div className="space-y-6">
            {/* AI Advisory Panel */}
            <Card className="bg-indigo-950/20 border-indigo-900/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-indigo-300">
                    <Sparkles className="w-5 h-5 text-indigo-400" />
                    AI Operational Advisory
                  </CardTitle>
                  <Badge variant="purple">Decision Support</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-2 bg-slate-950/60 p-3 rounded-xl border border-indigo-900/40">
                  <div>
                    <span className="text-slate-400 block text-[10px]">Detected Category</span>
                    <span className="font-bold text-slate-200">{grievance.category || '—'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">AI Confidence</span>
                    <span className="font-bold text-emerald-400 font-mono">
                      {grievance.classification_confidence
                        ? `${(grievance.classification_confidence * 100).toFixed(0)}%`
                        : '—'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">Priority Score</span>
                    <span className="font-bold text-amber-400 font-mono">
                      {grievance.priority_score !== null && grievance.priority_score !== undefined
                        ? `${grievance.priority_score} / 100`
                        : '—'}
                    </span>
                  </div>
                </div>

                {grievance.summary && (
                  <p className="text-slate-300 italic bg-slate-950/40 p-3 rounded-lg border border-slate-800/80 leading-relaxed">
                    "{grievance.summary}"
                  </p>
                )}

                {grievance.priority_explanation && (
                  <p className="text-[11px] text-indigo-300/80 italic">
                    {grievance.priority_explanation}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Comments Stream */}
            <Card>
              <CardHeader>
                <CardTitle>Activity & Comments</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Comment Input */}
                <form onSubmit={handleAddComment} className="flex gap-2">
                  <input
                    type="text"
                    required
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Add an update or comment..."
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                  <Button type="submit" size="sm" loading={commentSubmitting} icon={<Send className="w-3.5 h-3.5" />}>
                    Send
                  </Button>
                </form>

                {/* Comment Feed */}
                <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                  {comments.length === 0 ? (
                    <div className="text-center py-4 text-slate-500 text-xs">No comments posted yet.</div>
                  ) : (
                    comments.map((c) => (
                      <div key={c.id} className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1.5 text-xs">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Avatar name={c.author_id ? c.author_id.substring(0, 6) : 'User'} role={c.author_role as any} size="sm" />
                            <span className="font-bold text-slate-200">{c.author_id ? c.author_id.substring(0, 8) : 'User'}</span>
                            {c.author_role && <Badge variant="primary" size="sm">{c.author_role}</Badge>}
                          </div>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-slate-300 leading-relaxed pl-9">{c.comment}</p>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Upload Evidence Modal */}
        <Modal
          isOpen={uploadModalOpen}
          onClose={() => setUploadModalOpen(false)}
          title="Upload Evidence File"
          maxWidth="md"
        >
          <form onSubmit={handleUploadFile} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Select File
              </label>
              <input
                type="file"
                required
                onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2 text-xs text-slate-200"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                File Description
              </label>
              <input
                type="text"
                value={fileDescription}
                onChange={(e) => setFileDescription(e.target.value)}
                placeholder="e.g. Photo showing completed pipe repair"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setUploadModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" loading={uploading}>
                Upload
              </Button>
            </div>
          </form>
        </Modal>

        {/* Reject Resolution Explanation Modal */}
        <Modal
          isOpen={rejectModalOpen}
          onClose={() => setRejectModalOpen(false)}
          title="Reject Resolution & Reopen Case"
          maxWidth="md"
        >
          <div className="space-y-4">
            <p className="text-xs text-slate-300">
              Please explain why the resolution submitted by the department is unsatisfactory. Your grievance will be reopened and escalated.
            </p>
            <textarea
              required
              rows={4}
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Water leak was partially fixed, but street pavement is still blocked..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100"
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setRejectModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                loading={verifySubmitting}
                onClick={() => handleVerify(false)}
              >
                Confirm Reopen
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </AppLayout>
  );
}

export default GrievanceDetailsPage;
