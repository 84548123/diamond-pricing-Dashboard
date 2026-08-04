import React from 'react';
import { Bell, CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import { useAlerts } from '../hooks/useAlerts';

export const SmartAlerts = () => {
  const { alerts, markRead, markAllRead } = useAlerts();

  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="glass-card mb-6 overflow-hidden">
      <div className="flex items-center justify-between p-3 border-b border-white/10 bg-dark-900/50">
        <div className="flex items-center space-x-2">
          <Bell className="w-4 h-4 text-brand-400" />
          <h3 className="text-sm font-semibold text-white">Smart Alerts</h3>
        </div>
        <button onClick={() => markAllRead()} className="text-xs text-brand-400 hover:text-brand-300">Mark all read</button>
      </div>
      <div className="flex overflow-x-auto custom-scrollbar p-2 space-x-4">
        {alerts.map(alert => (
          <div 
            key={alert.id} 
            className={`flex-shrink-0 w-80 p-3 rounded-lg border transition-colors cursor-pointer ${alert.is_read ? 'bg-dark-800/30 border-white/5 opacity-60' : 'bg-dark-800 border-white/10 hover:border-brand-500/30'}`}
            onClick={() => !alert.is_read && markRead(alert.id)}
          >
            <div className="flex items-start space-x-3">
              <div className="mt-0.5">
                {alert.type === 'OPPORTUNITY' ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> :
                 alert.type === 'PRICE_DROP' ? <AlertTriangle className="w-4 h-4 text-amber-400" /> :
                 <Info className="w-4 h-4 text-brand-400" />}
              </div>
              <div>
                <p className={`text-sm ${alert.is_read ? 'text-slate-400' : 'text-white'}`}>{alert.message}</p>
                <p className="text-xs text-slate-500 mt-1">{new Date(alert.created_at).toLocaleTimeString()}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
