import { create } from 'zustand';

export interface AlertItem {
  id: string;
  title: string;
  message: string;
  type: 'OPPORTUNITY' | 'PRICE_DROP' | 'INFO';
  is_read: boolean;
  created_at: string;
}

interface AlertState {
  alerts: AlertItem[];
  unreadCount: number;
  loading: boolean;
  fetchAlerts: () => Promise<void>;
  markRead: (id: string) => Promise<void>;
  markAllRead: () => Promise<void>;
}

export const useAlertStore = create<AlertState>((set) => ({
  alerts: [],
  unreadCount: 0,
  loading: false,
  fetchAlerts: async () => {
    set({ loading: false });
  },
  markRead: async (id: string) => {
    set((state) => ({
      alerts: state.alerts.map(a => a.id === id ? { ...a, is_read: true } : a),
      unreadCount: Math.max(0, state.unreadCount - 1)
    }));
  },
  markAllRead: async () => {
    set((state) => ({
      alerts: state.alerts.map(a => ({ ...a, is_read: true })),
      unreadCount: 0
    }));
  }
}));
