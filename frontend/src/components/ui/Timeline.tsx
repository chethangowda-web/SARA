import React from "react";
import type { GrievanceEvent } from "../../types";
import StatusBadge from "./StatusBadge";
import { Clock, User, CheckCircle2, Bot } from "lucide-react";

export interface TimelineProps {
  events: GrievanceEvent[];
}

const EVENT_LABELS: Record<string, string> = {
  // Lifecycle events (actual backend values)
  GRIEVANCE_SUBMITTED: "Grievance Submitted",
  GRIEVANCE_CLASSIFIED: "AI Classification Complete",
  GRIEVANCE_ROUTED: "Routed to Department",
  OFFICER_ASSIGNED: "Assigned to Officer",
  OFFICER_ACKNOWLEDGED: "Officer Acknowledged",
  WORK_STARTED: "Work Started",
  RESOLUTION_SUBMITTED: "Resolution Submitted",
  VERIFICATION_STARTED: "Awaiting Citizen Verification",
  RESOLUTION_ACCEPTED: "Resolution Accepted",
  RESOLUTION_REJECTED: "Resolution Rejected by Citizen",
  CLOSED: "Case Closed",
  REOPENED: "Case Reopened",
  // Audit events
  COMMENT_ADDED: "Comment Added",
  EVIDENCE_UPLOADED: "Evidence Uploaded",
  DOSSIER_GENERATED: "Accountability Dossier Generated",
  // SLA events
  SLA_WARNING: "SLA Warning Issued",
  SLA_BREACH: "SLA Breach — Escalated",
  ESCALATED: "Case Escalated",
  // Fallback aliases
  ASSIGNED: "Assigned to Officer",
  ACKNOWLEDGED: "Officer Acknowledged",
  IN_PROGRESS: "Work Started",
  VERIFICATION: "Awaiting Citizen Verification",
};

export const Timeline: React.FC<TimelineProps> = ({ events }) => {
  if (!events || events.length === 0) {
    return <div className="text-slate-500 text-sm py-4">No events recorded in audit log yet.</div>;
  }

  return (
    <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
      {events.map((event, idx) => {
        const isSystem = !event.actor_id;
        return (
          <div key={event.id || idx} className="relative flex items-start gap-4 group">
            <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-slate-900 border-2 border-blue-500 text-blue-400 flex items-center justify-center shadow">
              {idx === events.length - 1 ? (
                <CheckCircle2 className="w-3 h-3 text-blue-400" />
              ) : (
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
              )}
            </div>

            <div className="flex-1 bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 shadow-sm hover:border-slate-700/80 transition">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <StatusBadge state={event.to_state} size="sm" />
                  <span className="text-xs font-bold text-slate-300">
                    {EVENT_LABELS[event.event_type] || event.event_type}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-[11px] text-slate-500 font-mono">
                  <Clock className="w-3 h-3" />
                  <span>{new Date(event.created_at).toLocaleString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
                {isSystem ? (
                  <Bot className="w-3.5 h-3.5 text-indigo-400" />
                ) : (
                  <User className="w-3.5 h-3.5 text-slate-500" />
                )}
                <span>
                  <strong className="text-slate-300">
                    {isSystem ? "SARA System" : event.actor_id!.substring(0, 8)}
                  </strong>{" "}
                  ({event.actor_role || "SYSTEM"})
                </span>
              </div>

              {event.reason && (
                <p className="text-xs text-slate-300 mt-2 p-2.5 bg-slate-900/80 rounded-lg border border-slate-800 italic">
                  "{event.reason}"
                </p>
              )}

              {event.metadata_json && event.event_type === "GRIEVANCE_CLASSIFIED" && (
                <div className="mt-2 p-2.5 bg-indigo-950/40 rounded-lg border border-indigo-900/50 text-[11px] space-y-1">
                  <div className="text-indigo-300 font-bold">AI Classification Result</div>
                  <div className="grid grid-cols-2 gap-2 text-slate-300">
                    <span>Category: <strong>{event.metadata_json.category || "—"}</strong></span>
                    <span>Priority: <strong>{event.metadata_json.priority || "—"}</strong></span>
                    <span>Confidence: <strong>{((event.metadata_json.confidence || 0) * 100).toFixed(0)}%</strong></span>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Timeline;
