import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Upload, TrendingUp, List, Box, Gem, Palette, Search, BrainCircuit, Grid, ChevronLeft, ChevronRight, Sparkles } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  const navGroups = [
    {
      title: 'MAIN',
      items: [{ icon: LayoutDashboard, label: 'Dashboard', to: '/' }]
    },
    {
      title: 'DATA',
      items: [{ icon: Upload, label: 'Upload 3 Data Files', to: '/import' }]
    },
    {
      title: 'AI SELLING PLATFORM',
      items: [
        { icon: BrainCircuit, label: 'Selling Intelligence', to: '/ai-pricing', pulse: true },
        { icon: Sparkles, label: 'Inventory Intelligence', to: '/inventory-intelligence' },
        { icon: Grid, label: 'Carat Bin Matrix View', to: '/carat-matrix' }
      ]
    },
    {
      title: 'ANALYTICS',
      items: [
        { icon: TrendingUp, label: 'Sales Analysis', to: '/sales-analysis' },
        { icon: List, label: 'Sales Details', to: '/sales-details' }
      ]
    },
    {
      title: 'DIMENSIONS',
      items: [
        { icon: Box, label: 'Size Master', to: '/carat-analysis' },
        { icon: Gem, label: 'Shape', to: '/shape-analysis' },
        { icon: Palette, label: 'Color', to: '/color-analysis' },
        { icon: Search, label: 'Clarity', to: '/clarity-analysis' }
      ]
    }
  ];

  return (
    <aside className={`fixed top-0 left-0 h-screen transition-all duration-300 ease-in-out z-20 glass border-r border-white/10 ${collapsed ? 'w-20' : 'w-64'} flex flex-col`}>
      <div className="h-16 flex items-center justify-center border-b border-white/5">
        <Gem className="w-8 h-8 text-brand-400" />
        {!collapsed && <span className="ml-3 font-bold text-lg bg-gradient-to-r from-brand-400 to-accent-cyan bg-clip-text text-transparent truncate">Diamond AI</span>}
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-hide py-4">
        {navGroups.map((group, idx) => (
          <div key={idx} className="mb-6">
            {!collapsed && <div className="px-6 mb-2 text-xs font-semibold text-slate-500 tracking-wider">{group.title}</div>}
            <ul>
              {group.items.map((item, i) => (
                <li key={i}>
                  <NavLink
                    to={item.to}
                    className={({ isActive }) => `
                      flex items-center px-6 py-3 transition-all duration-200 relative group
                      ${isActive ? 'text-white bg-brand-500/10' : 'text-slate-400 hover:text-white hover:bg-white/5'}
                    `}
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-brand-400 to-accent-cyan" />}
                        <div className="relative">
                          <item.icon className={`w-5 h-5 ${isActive ? 'text-brand-400' : 'text-slate-400 group-hover:text-slate-300'}`} />
                          {'pulse' in item && item.pulse && <span className="absolute -top-1 -right-1 w-2 h-2 bg-accent-cyan rounded-full animate-pulse"></span>}
                        </div>
                        {!collapsed && <span className="ml-3 font-medium truncate">{item.label}</span>}
                      </>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-white/5">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors"
        >
          {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>
    </aside>
  );
};
