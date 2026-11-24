import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  AlertTriangle, 
  CheckSquare, 
  ShieldCheck, 
  Bot, 
  BarChart3, 
  History, 
  Settings,
  Scale,
  X
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user, organization } = useAuth();

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Contracts', path: '/contracts', icon: FileText, badge: '5' },
    { name: 'Risk Analysis', path: '/risks', icon: AlertTriangle, badge: '4' },
    { name: 'Obligations', path: '/obligations', icon: CheckSquare, badge: '5' },
    { name: 'Compliance', path: '/compliance', icon: ShieldCheck, badge: '4' },
    { name: 'AI Assistant', path: '/assistant', icon: Bot, isNew: true },
    { name: 'Reports', path: '/reports', icon: BarChart3 },
    { name: 'Audit Logs', path: '/audit', icon: History },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-slate-950/70 backdrop-blur-xs lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-[#0b1329] text-slate-300 flex flex-col transition-transform duration-200 ease-in-out border-r border-slate-800/80 ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Logo and Brand */}
        <div className="h-16 px-6 flex items-center justify-between border-b border-slate-800/80">
          <NavLink to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-blue-400 flex items-center justify-center text-white shadow-md shadow-brand-500/20 group-hover:scale-105 transition-transform">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <span className="text-base font-bold text-white tracking-tight flex items-center gap-1.5">
                LexFlow <span className="text-brand-400 text-xs px-1.5 py-0.5 rounded-md bg-brand-500/10 border border-brand-500/20 font-semibold">AI</span>
              </span>
              <p className="text-[10px] text-slate-400 tracking-wider uppercase font-medium">Legal Intelligence</p>
            </div>
          </NavLink>
          <button 
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Organization pill */}
        <div className="px-4 py-3 border-b border-slate-800/50 bg-[#080d1c]/50">
          <div className="px-3 py-2 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <div className="truncate">
              <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Active Tenant</p>
              <p className="text-xs font-medium text-slate-200 truncate">{organization?.name || 'Hamilton Legal Group'}</p>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-400 ring-4 ring-emerald-950 shrink-0" />
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => onClose()}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                    isActive
                      ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/30 font-semibold'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className="flex items-center gap-3">
                      <Icon className={`w-4.5 h-4.5 shrink-0 transition-colors ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}`} />
                      <span>{item.name}</span>
                    </div>
                    {item.badge && (
                      <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                        isActive ? 'bg-white/20 text-white' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                    {item.isNew && (
                      <span className="text-[9px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded bg-brand-500/20 text-brand-300 border border-brand-500/30">
                        Search
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* User Profile Footer */}
        <div className="p-4 border-t border-slate-800/80 bg-[#080d1c]/60">
          <NavLink 
            to="/settings" 
            className="flex items-center gap-3 p-2 rounded-xl hover:bg-slate-800/60 transition-colors group"
          >
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-slate-700 to-slate-600 border border-slate-700 flex items-center justify-center text-xs font-bold text-white shrink-0">
              {user?.full_name ? user.full_name.substring(0, 2).toUpperCase() : 'AH'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-slate-200 truncate group-hover:text-brand-300 transition-colors">
                {user?.full_name || 'Alexander Hamilton'}
              </p>
              <p className="text-[11px] text-slate-400 truncate capitalize">
                {user?.role || 'Owner'}
              </p>
            </div>
          </NavLink>
        </div>
      </aside>
    </>
  );
};
