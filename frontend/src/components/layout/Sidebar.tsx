import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Avatar from '../ui/Avatar';
import Badge from '../ui/Badge';
import {
  LayoutDashboard,
  FilePlus,
  FileText,
  Users,
  Building2,
  BarChart3,
  AlertTriangle,
  ShieldCheck,
  LogOut,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';

export interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  onNavigateMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggleCollapse, onNavigateMobile }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Build Nav Items based on user role
  const getNavItems = () => {
    switch (user?.role) {
      case 'CITIZEN':
        return [
          { label: 'Dashboard', path: '/citizen', exact: true, icon: <LayoutDashboard className="w-5 h-5" /> },
          { label: 'My Grievances', path: '/citizen/grievances', icon: <FileText className="w-5 h-5" /> },
          { label: 'Submit Grievance', path: '/citizen/submit', icon: <FilePlus className="w-5 h-5" /> },
        ];
      case 'OFFICER':
        return [
          { label: 'Officer Workspace', path: '/officer', exact: true, icon: <LayoutDashboard className="w-5 h-5" /> },
          { label: 'Assigned Cases', path: '/officer/assigned', icon: <FileText className="w-5 h-5" /> },
        ];
      case 'SUPERVISOR':
        return [
          { label: 'Department Command', path: '/supervisor', exact: true, icon: <LayoutDashboard className="w-5 h-5" /> },
          { label: 'Department Cases', path: '/supervisor/cases', icon: <Building2 className="w-5 h-5" /> },
          { label: 'Officer Workload', path: '/supervisor/officers', icon: <Users className="w-5 h-5" /> },
          { label: 'Escalation Monitor', path: '/supervisor/escalations', icon: <AlertTriangle className="w-5 h-5" /> },
        ];
      case 'ADMIN':
        return [
          { label: 'SARA Command Center', path: '/admin', exact: true, icon: <LayoutDashboard className="w-5 h-5" /> },
          { label: 'Departments', path: '/admin/departments', icon: <Building2 className="w-5 h-5" /> },
          { label: 'Analytics & Trends', path: '/admin/analytics', icon: <BarChart3 className="w-5 h-5" /> },
          { label: 'Anomalies & AI', path: '/admin/anomalies', icon: <ShieldAlert className="w-5 h-5" /> },
        ];
      default:
        return [];
    }
  };

  const navItems = getNavItems();

  return (
    <aside
      className={`bg-slate-900 border-r border-slate-800/80 flex flex-col justify-between transition-all duration-300 z-30 select-none ${
        collapsed ? 'w-20' : 'w-72'
      }`}
    >
      {/* Top Branding Section */}
      <div>
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
          {!collapsed ? (
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
                <ShieldCheck className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h1 className="text-xl font-black tracking-tight bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
                  SARA
                </h1>
                <p className="text-[10px] text-slate-400 font-medium leading-none mt-0.5">
                  Government Accountability Platform
                </p>
              </div>
            </div>
          ) : (
            <div className="mx-auto p-2 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
              <ShieldCheck className="w-6 h-6 text-blue-400" />
            </div>
          )}

          <button
            onClick={onToggleCollapse}
            className="hidden md:flex p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1.5 mt-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.exact}
              onClick={() => onNavigateMobile && onNavigateMobile()}
              className={({ isActive }) =>
                `flex items-center gap-3.5 px-3.5 py-3 rounded-xl font-semibold text-sm transition ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20 border border-blue-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                } ${collapsed ? 'justify-center px-0' : ''}`
              }
              title={collapsed ? item.label : undefined}
            >
              <span className="shrink-0">{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Bottom Profile & Logout Section */}
      <div className="p-3 border-t border-slate-800/80 space-y-2">
        {!collapsed ? (
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
            <div className="flex items-center gap-3 overflow-hidden">
              <Avatar name={user?.full_name} role={user?.role} size="md" />
              <div className="truncate">
                <div className="text-xs font-bold text-slate-200 truncate">{user?.full_name}</div>
                <div className="mt-0.5">
                  <Badge variant="primary" size="sm">
                    {user?.role}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex justify-center py-2">
            <Avatar name={user?.full_name} role={user?.role} size="md" />
          </div>
        )}

        <button
          onClick={handleLogout}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-red-400 hover:bg-red-950/40 transition ${
            collapsed ? 'justify-center' : ''
          }`}
          title="Logout of session"
        >
          <LogOut className="w-5 h-5 shrink-0" />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
