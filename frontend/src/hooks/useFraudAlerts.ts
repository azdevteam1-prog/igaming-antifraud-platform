import { useState, useEffect, useCallback } from 'react';
import { fraudApi, FraudAlert, AlertsFilter, FraudStats } from '../api/fraud';

export function useFraudAlerts(initialFilters?: AlertsFilter) {
  const [alerts, setAlerts] = useState<FraudAlert[]>([]);
  const [stats, setStats] = useState<FraudStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<AlertsFilter>(initialFilters || {});
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
  });

  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fraudApi.getAlerts({
        ...filters,
        page: pagination.page,
        limit: pagination.limit,
      });
      setAlerts(data.items || data);
      if (data.total !== undefined) {
        setPagination((prev) => ({ ...prev, total: data.total }));
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch alerts');
    } finally {
      setIsLoading(false);
    }
  }, [filters, pagination.page, pagination.limit]);

  const fetchStats = useCallback(async () => {
    try {
      const data = await fraudApi.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch fraud stats:', err);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const updateAlertStatus = useCallback(
    async (
      alertId: string,
      status: FraudAlert['status'],
      notes?: string
    ) => {
      const updated = await fraudApi.updateAlertStatus(alertId, status, notes);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? updated : a))
      );
      await fetchStats();
      return updated;
    },
    [fetchStats]
  );

  const applyFilters = useCallback((newFilters: AlertsFilter) => {
    setFilters(newFilters);
    setPagination((prev) => ({ ...prev, page: 1 }));
  }, []);

  return {
    alerts,
    stats,
    isLoading,
    error,
    filters,
    pagination,
    applyFilters,
    updateAlertStatus,
    refresh: fetchAlerts,
  };
}
