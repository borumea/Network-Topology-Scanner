import { useEffect, useState, useCallback } from 'react';
import { fetchAlerts, updateAlert as apiUpdateAlert } from '../lib/api';
import type { Alert } from '../types/topology';

export function useAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);

  const loadAlerts = useCallback(async (params?: Record<string, string>) => {
    setLoading(true);
    try {
      const data = await fetchAlerts(params);
      setAlerts(data.alerts || []);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const acknowledgeAlert = useCallback(async (alertId: string) => {
    try {
      await apiUpdateAlert(alertId, 'acknowledged');
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId ? { ...a, status: 'acknowledged' as const } : a
        )
      );
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  }, []);

  const dismissAlert = useCallback(async (alertId: string) => {
    try {
      await apiUpdateAlert(alertId, 'dismissed');
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId ? { ...a, status: 'dismissed' as const } : a
        )
      );
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  }, []);

  // Listen for WebSocket alert events
  useEffect(() => {
    const handler = (event: CustomEvent) => {
      const newAlert = event.detail as Alert;
      setAlerts((prev) => [newAlert, ...prev]);
    };
    window.addEventListener('ws-alert', handler as EventListener);
    return () => window.removeEventListener('ws-alert', handler as EventListener);
  }, []);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  return { alerts, loading, loadAlerts, acknowledgeAlert, dismissAlert };
}
