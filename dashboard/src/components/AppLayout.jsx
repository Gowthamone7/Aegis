import React, { useState } from 'react';
import Sidebar from './Sidebar.jsx';
import TopNav from './TopNav.jsx';

export default function AppLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-brand-bg text-brand-textPrimary flex">
      {/* Sidebar for Desktop & Mobile */}
      <Sidebar
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ease-in-out min-w-0 ${
          collapsed ? 'md:ml-20' : 'md:ml-64'
        }`}
      >
        <TopNav
          collapsed={collapsed}
          onToggleMobile={() => setMobileOpen(!mobileOpen)}
        />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
