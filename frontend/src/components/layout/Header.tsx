import React from 'react';
import { useAuth } from '../../context/AuthContext';
import Avatar from '../ui/Avatar';
import Dropdown from '../ui/Dropdown';
import { Bell, Menu, Search, LogOut, User as UserIcon, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export interface HeaderProps {
  title?: string;
  breadcrumb?: string;
  unreadNotificationsCount?: number;
  onOpenNotifications: () => void;
  onOpenMobileSidebar: () => void;
  onSearchClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title = 'Dashboard',
  breadcrumb = 'Overview',
  unreadNotificationsCount = 0,
  onOpenNotifications,
  onOpenMobileSidebar,
  onSearchClick,
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Mobile Menu & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileSidebar}
          className="md:hidden p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
            <span>SARA</span>
            <span>/</span>
            <span className="text-slate-300 font-semibold">{breadcrumb}</span>
          </div>
          <h2 className="text-base sm:text-lg font-bold text-slate-100 leading-none mt-0.5">{title}</h2>
        </div>
      </div>

      {/* Right: Actions, Notification Bell, User Dropdown */}
      <div className="flex items-center gap-3">
        {/* Global Quick Search Button */}
        <button
          onClick={onSearchClick}
          className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-700 transition"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Quick Search...</span>
          <kbd className="px-1.5 py-0.5 text-[10px] bg-slate-800 rounded font-mono text-slate-400">Ctrl+K</kbd>
        </button>

        {/* Notification Bell Button */}
        <button
          onClick={onOpenNotifications}
          className="relative p-2 rounded-xl bg-slate-950/60 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition"
          aria-label="Notifications"
        >
          <Bell className="w-5 h-5" />
          {unreadNotificationsCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center border-2 border-slate-900 shadow">
              {unreadNotificationsCount > 9 ? '9+' : unreadNotificationsCount}
            </span>
          )}
        </button>

        {/* Profile Dropdown */}
        <Dropdown
          align="right"
          trigger={
            <button className="flex items-center gap-2 p-1 rounded-xl hover:bg-slate-800/60 transition">
              <Avatar name={user?.full_name} role={user?.role} size="sm" />
            </button>
          }
          items={[
            {
              id: 'profile-info',
              label: (
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-slate-200">{user?.full_name}</div>
                  <div className="text-[11px] text-slate-400 font-mono">{user?.email}</div>
                </div>
              ),
              icon: <UserIcon className="w-4 h-4 text-blue-400" />,
              onClick: () => {},
            },
            {
              id: 'security-info',
              label: 'Encrypted Government Session',
              icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
              onClick: () => {},
            },
            {
              id: 'logout',
              label: 'Sign Out',
              icon: <LogOut className="w-4 h-4 text-red-400" />,
              danger: true,
              onClick: handleLogout,
            },
          ]}
        />
      </div>
    </header>
  );
};

export default Header;
