import { useEffect, useCallback } from 'react';
import { useTopologyStore } from '../stores/topologyStore';
import { useFilterStore } from '../stores/filterStore';
import { fetchTopology, fetchTopologyStats, fetchSPOFs } from '../lib/api';

export function useTopology() {
  const { setTopology, setStats, setSPOFs, setLoading, setError } = useTopologyStore();
  const { activeLayer } = useFilterStore();

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

  return { reload: loadTopology };
}
