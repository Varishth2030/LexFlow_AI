import React, { useState } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { 
  Menu, 
  Search, 
  Bell, 
  ChevronRight, 
  CheckCircle2, 
  AlertTriangle, 
  LogOut, 
  User, 
  Settings,
  ShieldAlert
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface TopbarProps {
  onOpenMobileMenu: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onOpenMobileMenu }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, organization, logout } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  // Generate breadcrumb items
  const pathnames = location.pathname.split('/').filter((x) => x);
  const breadcrumbMap: Record<string, string> = {
    contracts: 'Contracts',
    risks: 'Risk Analysis',
    obligations: 'Obligations',
    compliance: 'Compliance',
    assistant: 'AI Assistant',
    reports: 'Reports',
    audit: 'Audit Logs',
    settings: 'Settings',
  };

  const notifications = [
    {
      id: 'n1',
      title: 'Critical Risk Detected',
      desc: 'Uncapped Liability clause flagged in SAP ERP Subscription Draft.',
      time: '15m ago',
      type: 'risk',
    },
    {
      id: 'n2',
      title: 'Compliance Task Overdue',
      desc: 'Execute EU Standard Contractual Clauses due date elapsed.',
      time: '2h ago',
      type: 'task',
    },
    {
      id: 'n3',
      title: 'Contract Upload Processed',
      desc: 'Apex Global MSA text extracted & chunked (19 chunks).',
      time: '1d ago',
      type: 'info',
    },
  ];

  return (
    <header className="sticky top-0 z-30 h-16 bg-white border-b border-slate-200/90 px-4 sm:px-6 flex items-center justify-between shadow-xs">
      {/* Left side: Mobile menu & Breadcrumbs */}
      <div className="flex items-center gap-4">
        <button
          onClick={onOpenMobileMenu}
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Breadcrumbs */}
        <nav className="flex items-center text-xs font-medium text-slate-500">
          <Link to="/" className="hover:text-slate-900 transition-colors">
            Workspace
          </Link>
          {pathnames.length === 0 ? (
            <>
              <ChevronRight className="w-3.5 h-3.5 mx-1.5 text-slate-400" />
              <span className="text-slate-900 font-semibold">Dashboard</span>
            </>
          ) : (
            pathnames.map((segment, index) => {
              const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
              const isLast = index === pathnames.length - 1;
              const title = breadcrumbMap[segment] || segment;

              return (
                <React.Fragment key={routeTo}>
                  <ChevronRight className="w-3.5 h-3.5 mx-1.5 text-slate-400" />
                  {isLast ? (
                    <span className="text-slate-900 font-semibold">{title}</span>
                  ) : (
                    <Link to={routeTo} className="hover:text-slate-900 transition-colors">
                      {title}
                    </Link>
                  )}
                </React.Fragment>
              );
            })
          )}
        </nav>
      </div>

      {/* Right side: Global Search, System Pill, Notifications & Profile */}
      <div className="flex items-center gap-3">
        {/* Search quick button */}
        <button 
          onClick={() => navigate('/assistant')}
          className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-slate-100/80 hover:bg-slate-200/80 text-slate-500 text-xs rounded-lg transition-colors border border-slate-200"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Search contracts & clauses...</span>
          <kbd className="ml-2 font-mono text-[10px] bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-400">
            ⌘K
          </kbd>
        </button>

        {/* Non-generative deterministic engine badge */}
        <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-medium">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>Rule-Based Screening Active</span>
        </div>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowProfileMenu(false);
            }}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg relative transition-colors"
          >
            <Bell className="w-4.5 h-4.5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full ring-2 ring-white" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50 animate-in fade-in duration-150">
              <div className="px-4 py-2 border-b border-slate-100 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-900">Notifications</span>
                <span className="text-[10px] bg-rose-50 text-rose-600 px-1.5 py-0.5 rounded-full font-medium">
                  3 unread
                </span>
              </div>
              <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto">
                {notifications.map((n) => (
                  <div key={n.id} className="p-3 hover:bg-slate-50 cursor-pointer transition-colors">
                    <div className="flex items-start gap-2.5">
                      {n.type === 'risk' && <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />}
                      {n.type === 'task' && <ShieldAlert className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />}
                      {n.type === 'info' && <CheckCircle2 className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />}
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-slate-900">{n.title}</p>
                        <p className="text-[11px] text-slate-500 line-clamp-2 mt-0.5">{n.desc}</p>
                        <p className="text-[10px] text-slate-400 mt-1">{n.time}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="px-4 py-2 border-t border-slate-100 text-center">
                <Link 
                  to="/audit" 
                  onClick={() => setShowNotifications(false)}
                  className="text-xs text-brand-600 hover:underline font-medium"
                >
                  View full audit activity
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Menu */}
        <div className="relative">
          <button
            onClick={() => {
              setShowProfileMenu(!showProfileMenu);
              setShowNotifications(false);
            }}
            className="flex items-center gap-2 p-1 pl-2 hover:bg-slate-100 rounded-lg transition-colors border border-transparent hover:border-slate-200"
          >
            <div className="w-7 h-7 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-semibold">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <span className="text-xs font-semibold text-slate-700 hidden sm:inline-block max-w-[120px] truncate">
              {user?.full_name || 'Counsel'}
            </span>
          </button>

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-slate-200 py-1.5 z-50 animate-in fade-in duration-150">
              <div className="px-4 py-2.5 border-b border-slate-100">
                <p className="text-xs font-semibold text-slate-900">{user?.full_name}</p>
                <p className="text-[11px] text-slate-500 truncate">{user?.email}</p>
                <p className="text-[10px] text-brand-600 font-medium mt-0.5">{organization?.name}</p>
              </div>
              <div className="py-1">
                <Link
                  to="/settings"
                  onClick={() => setShowProfileMenu(false)}
                  className="flex items-center gap-2.5 px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  <User className="w-3.5 h-3.5 text-slate-400" />
                  <span>My Profile</span>
                </Link>
                <Link
                  to="/settings"
                  onClick={() => setShowProfileMenu(false)}
                  className="flex items-center gap-2.5 px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  <Settings className="w-3.5 h-3.5 text-slate-400" />
                  <span>Organization Settings</span>
                </Link>
              </div>
              <div className="border-t border-slate-100 pt-1">
                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    logout();
                    navigate('/login');
                  }}
                  className="flex items-center gap-2.5 w-full text-left px-4 py-2 text-xs text-rose-600 hover:bg-rose-50 transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5 text-rose-500" />
                  <span>Sign out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
