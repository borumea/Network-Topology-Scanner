import { X, Play, Trash2, Plus, Zap, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { useTopologyStore } from '../../stores/topologyStore';
import { useSimulation } from '../../hooks/useSimulation';
import DeviceIcon from '../shared/DeviceIcon';
import type { Device } from '../../types/topology';
import { useState } from 'react';

export default function SimulationPanel() {
  const {
    devices, simulationResult, simulationActive,
    setRightPanelContent,
  } = useTopologyStore();
  const {
    simulationTargets, addTarget, removeTarget,
    runSimulation, clearSimulation, loading, error,
  } = useSimulation();

  const [showDevicePicker, setShowDevicePicker] = useState(false);
  const [search, setSearch] = useState('');

  const targetDevices = devices.filter((d) => simulationTargets.nodes.includes(d.id));

  const filteredDevices = devices
    .filter((d) =>
      !simulationTargets.nodes.includes(d.id) &&
      (d.hostname.toLowerCase().includes(search.toLowerCase()) ||
       d.ip.includes(search))
    )
    .slice(0, 20);

  return (
    <div className="w-[380px] h-full bg-bg-secondary border-l border-bg-tertiary flex flex-col animate-slide-in-right">
      <div className="sticky top-0 bg-bg-secondary border-b border-bg-tertiary px-4 py-3 flex items-center justify-between z-10 flex-shrink-0">
        <span className="text-sm font-semibold text-text-primary">Failure Simulation</span>
        <button
          onClick={() => setRightPanelContent(null)}
          className="text-text-muted hover:text-text-primary transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Target selection */}
        <div>
          <div className="text-xs text-text-muted mb-2">Select targets to simulate failure:</div>
          <div className="space-y-1.5">
            {targetDevices.map((d) => (
              <div key={d.id} className="flex items-center justify-between bg-bg-tertiary rounded-lg px-3 py-2">
                <div className="flex items-center gap-2">
                  <DeviceIcon type={d.device_type} size={14} />
                  <span className="text-xs text-text-primary">{d.hostname || d.ip}</span>
                </div>
                <button
                  onClick={() => removeTarget('nodes', d.id)}
                  className="text-text-muted hover:text-risk-critical transition-colors"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>

          <div className="relative mt-2">
            <button
              onClick={() => setShowDevicePicker(!showDevicePicker)}
              className="flex items-center gap-1.5 text-xs text-node-switch hover:text-node-switch/80 transition-colors"
            >
              <Plus size={12} />
              Add device
            </button>

            {showDevicePicker && (
              <div className="absolute top-full left-0 mt-1 w-full bg-bg-primary border border-bg-tertiary rounded-lg shadow-xl z-20 max-h-60 overflow-y-auto">
                <input
                  autoFocus
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search devices..."
                  className="w-full px-3 py-2 text-xs bg-transparent border-b border-bg-tertiary outline-none text-text-primary"
                />
                {filteredDevices.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => {
                      addTarget('nodes', d.id);
                      setShowDevicePicker(false);
                      setSearch('');
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-left hover:bg-bg-tertiary transition-colors"
                  >
                    <DeviceIcon type={d.device_type} size={12} />
                    <span className="text-text-primary">{d.hostname || d.ip}</span>
                    <span className="text-text-muted ml-auto">{d.ip}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Run button */}
        <div className="flex gap-2">
          <button
            onClick={runSimulation}
            disabled={loading || simulationTargets.nodes.length === 0}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-risk-critical text-white text-xs font-medium hover:bg-risk-critical/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Play size={12} />
            {loading ? 'Running...' : 'Run Simulation'}
          </button>
          {(simulationActive || simulationTargets.nodes.length > 0) && (
            <button
              onClick={clearSimulation}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-bg-tertiary text-text-secondary text-xs hover:text-text-primary transition-colors"
            >
              <Trash2 size={12} />
              Clear
            </button>
          )}
        </div>

        {error && (
          <div className="text-xs text-risk-critical bg-risk-critical/10 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        {/* Results */}
        {simulationResult && (
          <div className="space-y-3 pt-2 border-t border-bg-tertiary">
            <div className="text-xs font-semibold text-text-primary uppercase">Results</div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-text-secondary">Blast Radius</span>
                <span className="text-risk-critical font-mono">
                  {simulationResult.blast_radius} devices ({simulationResult.blast_radius_pct}%)
                </span>
              </div>
              <div className="h-2 bg-bg-tertiary rounded-full overflow-hidden">
                <div
                  className="h-full bg-risk-critical rounded-full transition-all duration-500"
                  style={{ width: `${simulationResult.blast_radius_pct}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-bg-tertiary rounded-lg p-2">
                <div className="text-text-muted">Disconnected</div>
                <div className="text-lg font-bold text-risk-critical">
                  {simulationResult.disconnected_devices.length}
                </div>
              </div>
              <div className="bg-bg-tertiary rounded-lg p-2">
                <div className="text-text-muted">Degraded</div>
                <div className="text-lg font-bold text-risk-medium">
                  {simulationResult.degraded_devices.length}
                </div>
              </div>
            </div>

            {simulationResult.affected_services.length > 0 && (
              <div>
                <div className="text-[10px] text-text-muted uppercase mb-1">Services Down</div>
                <div className="flex flex-wrap gap-1">
                  {simulationResult.affected_services.map((svc) => (
                    <span key={svc} className="text-[10px] px-2 py-0.5 rounded bg-risk-critical/10 text-risk-critical">
                      {svc}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="text-xs">
              <span className="text-text-muted">Risk delta: </span>
              <span className="text-risk-critical font-mono">+{simulationResult.risk_delta}</span>
            </div>

            {/* Affected devices */}
            {simulationResult.disconnected_devices.length > 0 && (
              <div>
                <div className="text-[10px] text-text-muted uppercase mb-1">
                  Affected Devices (top 10)
                </div>
                <div className="space-y-1">
                  {simulationResult.disconnected_devices.slice(0, 10).map((d) => (
                    <div key={d.id} className="flex items-center justify-between text-xs bg-bg-tertiary/50 rounded px-2 py-1">
                      <span className="text-text-primary">{d.hostname || d.id.slice(0, 8)}</span>
                      <span className="text-risk-critical flex items-center gap-1">
                        <XCircle size={10} />
                        {d.status}
                      </span>
                    </div>
                  ))}
                  {simulationResult.degraded_devices.slice(0, 5).map((d) => (
                    <div key={d.id} className="flex items-center justify-between text-xs bg-bg-tertiary/50 rounded px-2 py-1">
                      <span className="text-text-primary">{d.hostname || d.id.slice(0, 8)}</span>
                      <span className="text-risk-medium flex items-center gap-1">
                        <AlertTriangle size={10} />
                        {d.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {simulationResult.recommendations.length > 0 && (
              <div>
                <div className="text-[10px] text-text-muted uppercase mb-1">Recommendations</div>
                <div className="space-y-2">
                  {simulationResult.recommendations.map((rec, i) => (
                    <div key={i} className="text-xs bg-bg-tertiary rounded-lg p-2">
                      <div className="text-text-primary">{i + 1}. {rec.action}</div>
                      <div className="text-text-muted mt-0.5">{rec.impact}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

