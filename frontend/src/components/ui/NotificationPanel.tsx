import React, { useEffect, useState } from 'react';
import type { Notification } from '../../types';
import { fetchNotifications, markNotificationRead, markAllNotificationsRead } from '../../api/grievances';
import Button from './Button';
import EmptyState from './EmptyState';
import { Bell, CheckCheck, Clock, FileText, AlertTriangle, ShieldAlert } from 'lucide-react';
import { formatApiError } from '../../api/client';

export interface NotificationPanelProps {
  onSelectGrievance?: (grievanceId: string) => void;
  onClose?: () => void;
}

export const NotificationPanel: React.FC<NotificationPanelProps> = ({ onSelectGrievance, onClose }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const loadNotifs = async () => {
    try {
      setLoading(true);
      const res = await fetchNotifications();
      setNotifications(res || []);
    } catch (err) {
      console.error(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifs();
  }, []);

  const handleMarkRead = async (id: string) => {
    try {
      await markNotificationRead(id);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = notifications.filter((n) => (filter === 'unread' ? !n.is_read : true));
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const getNotifIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'sla_breach':
      case 'escalation':
        return <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />;
      case 'sla_warning':
        return <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />;
      default:
        return <FileText className="w-4 h-4 text-blue-400 shrink-0" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Action Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
              filter === 'all' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({notifications.length})
          </button>
          <button
            onClick={() => setFilter('unread')}
            className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
              filter === 'unread' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Unread ({unreadCount})
          </button>
        </div>

        {unreadCount > 0 && (
          <Button variant="ghost" size="sm" onClick={handleMarkAllRead} icon={<CheckCheck className="w-3.5 h-3.5" />}>
            Mark all read
          </Button>
        )}
      </div>

      {/* Notification List */}
      {loading ? (
        <div className="space-y-3">
          <div className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
          <div className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
          <div className="h-16 bg-slate-800/40 rounded-xl animate-pulse" />
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Bell className="w-8 h-8 text-slate-500" />}
          title="No notifications"
          description={filter === 'unread' ? 'You have read all notifications!' : 'No notification history found.'}
        />
      ) : (
        <div className="space-y-2.5 max-h-[70vh] overflow-y-auto pr-1">
          {filtered.map((notif) => (
            <div
              key={notif.id}
              onClick={() => {
                if (!notif.is_read) handleMarkRead(notif.id);
                if (notif.grievance_id && onSelectGrievance) {
                  onSelectGrievance(notif.grievance_id);
                  if (onClose) onClose();
                }
              }}
              className={`p-4 rounded-xl border transition cursor-pointer flex items-start gap-3 ${
                notif.is_read
                  ? 'bg-slate-950/40 border-slate-800/60 opacity-80 hover:bg-slate-800/30'
                  : 'bg-slate-900 border-blue-900/50 shadow-md hover:border-blue-700/60'
              }`}
            >
              <div className="mt-0.5">{getNotifIcon(notif.type)}</div>

              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-bold ${notif.is_read ? 'text-slate-300' : 'text-blue-200'}`}>
                    {notif.title}
                  </span>
                  {!notif.is_read && <span className="w-2 h-2 rounded-full bg-blue-500" />}
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">{notif.message}</p>

                <div className="flex items-center justify-between pt-1 text-[10px] text-slate-500 font-mono">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(notif.created_at).toLocaleString()}
                  </span>
                  {notif.grievance_id && (
                    <span className="text-blue-400 underline">View Grievance</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NotificationPanel;
