import { useAlertStore } from '../../../store/alertStore';

export const useAlerts = () => {
  const store = useAlertStore();
  return {
    alerts: store.alerts,
    unreadCount: store.unreadCount,
    loading: store.loading,
    markRead: store.markRead,
    markAllRead: store.markAllRead,
    refetch: store.fetchAlerts
  };
};
