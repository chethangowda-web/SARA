import React, { useState, useEffect } from 'react';
import Sidebar from '../components/layout/Sidebar';
import Header from '../components/layout/Header';
import Drawer from '../components/ui/Drawer';
import NotificationPanel from '../components/ui/NotificationPanel';
import Modal from '../components/ui/Modal';
import SearchBar from '../components/ui/SearchBar';
import { ToastProvider } from '../components/ui/Toast';
import { fetchNotifications, fetchGrievances } from '../api/grievances';
import type { Grievance } from '../types';
import { useNavigate } from 'react-router-dom';

export interface AppLayoutProps {
  children: React.ReactNode;
  title?: string;
  breadcrumb?: string;
}

export const AppLayoutContent: React.FC<AppLayoutProps> = ({ children, title = 'Dashboard', breadcrumb = 'Overview' }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [notifDrawerOpen, setNotifDrawerOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Grievance[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  const navigate = useNavigate();

  const loadUnreadCount = async () => {
    try {
      const notifs = await fetchNotifications();
      if (Array.isArray(notifs)) {
        setUnreadCount(notifs.filter((n) => !n.is_read).length);
      }
    } catch {
      // Ignore background notification count failures
    }
  };

  useEffect(() => {
    loadUnreadCount();
    const interval = setInterval(loadUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard shortcut Ctrl+K for search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setSearchModalOpen(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      setSearchLoading(true);
      const list = await fetchGrievances(50, 0);
      const filtered = (list || []).filter(
        (g) =>
          g.title.toLowerCase().includes(query.toLowerCase()) ||
          g.id.toLowerCase().includes(query.toLowerCase()) ||
          (g.description && g.description.toLowerCase().includes(query.toLowerCase())) ||
          (g.category && g.category.toLowerCase().includes(query.toLowerCase()))
      );
      setSearchResults(filtered);
    } catch {
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex shrink-0 sticky top-0 h-screen">
        <Sidebar collapsed={collapsed} onToggleCollapse={() => setCollapsed(!collapsed)} />
      </div>

      {/* Mobile Sidebar Drawer */}
      <Drawer isOpen={mobileSidebarOpen} onClose={() => setMobileSidebarOpen(false)} position="left" width="md">
        <Sidebar
          collapsed={false}
          onToggleCollapse={() => {}}
          onNavigateMobile={() => setMobileSidebarOpen(false)}
        />
      </Drawer>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          title={title}
          breadcrumb={breadcrumb}
          unreadNotificationsCount={unreadCount}
          onOpenNotifications={() => setNotifDrawerOpen(true)}
          onOpenMobileSidebar={() => setMobileSidebarOpen(true)}
          onSearchClick={() => setSearchModalOpen(true)}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6">
          {children}
        </main>
      </div>

      {/* Notification Drawer */}
      <Drawer
        isOpen={notifDrawerOpen}
        onClose={() => setNotifDrawerOpen(false)}
        title="Notifications & Alerts"
        width="md"
      >
        <NotificationPanel
          onSelectGrievance={(id) => {
            setNotifDrawerOpen(false);
            navigate(`/grievances/${id}`);
          }}
          onClose={() => setNotifDrawerOpen(false)}
        />
      </Drawer>

      {/* Global Quick Search Modal */}
      <Modal
        isOpen={searchModalOpen}
        onClose={() => setSearchModalOpen(false)}
        title="Search Grievances"
        maxWidth="lg"
      >
        <div className="space-y-4">
          <SearchBar
            value={searchQuery}
            onChange={handleSearch}
            placeholder="Type ID, title, keyword or category..."
          />

          <div className="max-h-60 overflow-y-auto space-y-2">
            {searchLoading ? (
              <div className="text-center py-6 text-slate-400 text-sm">Searching records...</div>
            ) : searchResults.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-sm">
                {searchQuery ? 'No matching grievances found.' : 'Start typing to search grievances...'}
              </div>
            ) : (
              searchResults.map((g) => (
                <div
                  key={g.id}
                  onClick={() => {
                    setSearchModalOpen(false);
                    navigate(`/grievances/${g.id}`);
                  }}
                  className="p-3 bg-slate-950 border border-slate-800 hover:border-blue-500/50 rounded-xl cursor-pointer transition flex items-center justify-between"
                >
                  <div>
                    <div className="font-bold text-sm text-slate-200">{g.title}</div>
                    <div className="text-xs text-slate-500 font-mono">{g.id}</div>
                  </div>
                  <span className="px-2 py-1 bg-blue-950 text-blue-400 text-xs rounded border border-blue-800/50">
                    {g.current_state}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
};

export const AppLayout: React.FC<AppLayoutProps> = (props) => (
  <ToastProvider>
    <AppLayoutContent {...props} />
  </ToastProvider>
);

export default AppLayout;

