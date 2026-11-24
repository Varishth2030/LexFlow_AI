import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export const MainLayout: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Sidebar navigation */}
      <Sidebar isOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />

      {/* Main content wrapper */}
      <div className="lg:pl-64 flex flex-col flex-1 min-h-screen">
        <Topbar onOpenMobileMenu={() => setMobileMenuOpen(true)} />

        {/* Content area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>

        {/* Footer */}
        <footer className="py-4 px-6 border-t border-slate-200/80 bg-white text-center text-xs text-slate-400">
          <p>
            LexFlow AI — Enterprise Contract Intelligence & Compliance Automation Engine (Deterministic Screening)
          </p>
        </footer>
      </div>
    </div>
  );
};
