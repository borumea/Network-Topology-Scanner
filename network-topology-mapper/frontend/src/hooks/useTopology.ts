import { useEffect, useCallback, useRef } from 'react';
import { useTopologyStore } from '../stores/topologyStore';
import { useFilterStore } from '../stores/filterStore';
import { fetchTopology, fetchTopologyStats, fetchSPOFs } from '../lib/api';

export function useTopology() {
  const { setTopology, setStats, setSPOFs, setLoading, setError } = useTopologyStore();
  const { activeLayer } = useFilterStore();
  const reloadTimerRef = useRef<number>();

  const loadTopology = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (activeLayer) params.layer = activeLayer;

      const [topology, stats] = await Promise.all([
        fetchTopology(params),
        fetchTopologyStats(),
      ]);

      setTopology(topology);
      setStats(stats);

      // Load SPOFs
      try {
        const spofData = await fetchSPOFs();
        setSPOFs(spofData.spofs || []);
      } catch {
        // SPOFs might fail if graph analysis isn't available
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load topology');
    } finally {
      setLoading(false);
    }
  }, [activeLayer, setTopology, setStats, setSPOFs, setLoading, setError]);

  useEffect(() => {
    loadTopology();
  }, [loadTopology]);

  // Auto-reload topology when a scan completes
  useEffect(() => {
    const handleScanProgress = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail?.phase === 'completed' || detail?.percent >= 100) {
        // Small delay to let Neo4j finish writing
        if (reloadTimerRef.current) clearTimeout(reloadTimerRef.current);
        reloadTimerRef.current = window.setTimeout(() => {
          loadTopology();
        }, 1500);
      }
    };

    window.addEventListener('ws-scan-progress', handleScanProgress);
    return () => {
      window.removeEventListener('ws-scan-progress', handleScanProgress);
      if (reloadTimerRef.current) clearTimeout(reloadTimerRef.current);
    };
  }, [loadTopology]);

  return { reload: loadTopology };
}
