import { useCallback, useState } from 'react';
import { useTopologyStore } from '../stores/topologyStore';
import { simulateFailure } from '../lib/api';
import type { SimulationResult } from '../types/topology';

export function useSimulation() {
  const {
    simulationTargets,
    setSimulationResult,
    setSimulationActive,
    addSimulationTarget,
    removeSimulationTarget,
    clearSimulationTargets,
  } = useTopologyStore();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = useCallback(async () => {
    if (simulationTargets.nodes.length === 0 && simulationTargets.edges.length === 0) {
      setError('Select at least one device or link to simulate failure');
      return;
    }

    setLoading(true);
    setError(null);
    setSimulationActive(true);

    try {
      const result: SimulationResult = await simulateFailure(
        simulationTargets.nodes,
        simulationTargets.edges.map((e) => e.split('|'))
      );
      setSimulationResult(result);
    } catch (err: any) {
      setError(err.message || 'Simulation failed');
      setSimulationActive(false);
    } finally {
      setLoading(false);
    }
  }, [simulationTargets, setSimulationResult, setSimulationActive]);

  const clearSimulation = useCallback(() => {
    clearSimulationTargets();
    setError(null);
  }, [clearSimulationTargets]);

  return {
    simulationTargets,
    addTarget: addSimulationTarget,
    removeTarget: removeSimulationTarget,
    runSimulation,
    clearSimulation,
    loading,
    error,
  };
}
