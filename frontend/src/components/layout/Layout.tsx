import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="light-theme flex min-h-screen bg-slate-100 text-slate-900">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col transition-all duration-300">
        <Header />
        <main className="flex-1 p-6 overflow-x-hidden relative">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-brand-100/70 via-slate-100 to-slate-100 -z-10 pointer-events-none"></div>
          {children}
        </main>
      </div>
    </div>
  );
};
