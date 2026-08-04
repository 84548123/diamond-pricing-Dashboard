import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Search, Bell, Settings, RefreshCw } from 'lucide-react';
import { useAlertStore } from '../../store/alertStore';

export const Header = () => {
  const location = useLocation();
  const { unreadCount, fetchAlerts } = useAlertStore();

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const getPageTitle = (path: string) => {
    switch (path) {
      case '/': return 'Dashboard';
      case '/import': return 'Import Files';
      case '/sales-analysis': return 'Sales Analysis';
      case '/sales-details': return 'Sales Details';
      case '/carat-analysis': return 'Carat Bin Analysis';
      case '/shape-analysis': return 'Shape Analysis';
      case '/color-analysis': return 'Color Analysis';
      case '/clarity-analysis': return 'Clarity Analysis';
      case '/ai-pricing': return 'AI Pricing Intelligence';
      default: return 'Diamond AI';
    }
  };

  return (
    <header className="h-16 glass border-b border-white/10 sticky top-0 z-10 px-6 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-bold text-white">{getPageTitle(location.pathname)}</h1>
      </div>

      <div className="flex-1 max-w-xl mx-8">
        <div className="relative group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-brand-400 transition-colors" />
          <input
            type="text"
            placeholder="Search stones, orders, clients..."
            className="w-full bg-dark-900/50 border border-white/10 rounded-full py-2 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/50 transition-all"
          />
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <button onClick={fetchAlerts} className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-full transition-colors">
          <RefreshCw className="w-5 h-5" />
        </button>
        <div className="relative">
          <button className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-full transition-colors relative">
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-accent-rose rounded-full animate-pulse border border-dark-950"></span>
            )}
          </button>
        </div>
        <button className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-full transition-colors">
          <Settings className="w-5 h-5" />
        </button>
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-500 to-accent-cyan flex items-center justify-center text-sm font-bold text-white border border-white/20 ml-2">
          JD
        </div>
      </div>
    </header>
  );
};
