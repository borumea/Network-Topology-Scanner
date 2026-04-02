import { X, Play, Trash2, Plus } from 'lucide-react';
import { useTopologyStore } from '../../stores/topologyStore';
import { useSimulation } from '../../hooks/useSimulation';
import DeviceIcon from '../shared/DeviceIcon';
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

  const blastSegments = 20;
  const blastFilled = simulationResult ? Math.round((simulationResult.blast_radius_pct / 100) * blastSegments) : 0;

  return (
    <div className="w-[380px] flex-shrink-0 h-full bg-nd-surface border-l border-nd-border flex flex-col animate-fade-in">
      {/* Header */}
      <div className="sticky top-0 bg-nd-surface border-b border-nd-border px-4 py-3 flex items-center justify-between z-10 flex-shrink-0">
        <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Failure Simulation</span>
        <button
          onClick={() => setRightPanelContent(null)}
          className="text-nd-text-disabled hover:text-nd-text-primary transition-colors"
        >
          <X size={16} strokeWidth={1.5} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Target selection */}
        <div>
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled mb-2">Targets</div>
          <div className="space-y-1.5">
            {targetDevices.map((d) => (
              <div key={d.id} className="flex items-center justify-between bg-nd-surface-raised border border-nd-border rounded-nd-compact px-3 py-2">
                <div className="flex items-center gap-2">
                  <DeviceIcon type={d.device_type} size={14} />
                  <span className="font-mono text-caption text-nd-text-primary">{d.hostname || d.ip}</span>
                </div>
                <button
                  onClick={() => removeTarget('nodes', d.id)}
                  className="text-nd-text-disabled hover:text-nd-accent transition-colors"
                >
                  <X size={14} strokeWidth={1.5} />
                </button>
              </div>
            ))}
          </div>

          <div className="relative mt-2">
            <button
              onClick={() => setShowDevicePicker(!showDevicePicker)}
              className="flex items-center gap-1.5 font-mono text-label uppercase tracking-[0.06em] text-nd-interactive hover:opacity-80 transition-opacity"
            >
              <Plus size={12} strokeWidth={1.5} />
              Add Device
            </button>

            {showDevicePicker && (
              <div className="absolute top-full left-0 mt-1 w-full bg-nd-surface border border-nd-border-visible rounded-nd-compact z-20 max-h-60 overflow-y-auto">
                <input
                  autoFocus
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search devices..."
                  className="w-full px-3 py-2 font-mono text-caption bg-transparent border-b border-nd-border outline-none text-nd-text-primary placeholder:text-nd-text-disabled"
                />
                {filteredDevices.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => {
                      addTarget('nodes', d.id);
                      setShowDevicePicker(false);
                      setSearch('');
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-nd-surface-raised transition-colors"
                  >
                    <DeviceIcon type={d.device_type} size={12} />
                    <span className="font-mono text-caption text-nd-text-primary">{d.hostname || d.ip}</span>
                    <span className="font-mono text-label text-nd-text-disabled ml-auto">{d.ip}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={runSimulation}
            disabled={loading || simulationTargets.nodes.length === 0}
            className="flex items-center gap-1.5 px-4 py-2 rounded-nd-pill bg-nd-accent text-white font-mono text-label uppercase tracking-[0.06em] hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
          >
            <Play size={12} strokeWidth={1.5} />
            {loading ? 'Running...' : 'Simulate'}
          </button>
          {(simulationActive || simulationTargets.nodes.length > 0) && (
            <button
              onClick={clearSimulation}
              className="flex items-center gap-1.5 px-3 py-2 rounded-nd-pill border border-nd-border-visible font-mono text-label uppercase tracking-[0.06em] text-nd-text-secondary hover:text-nd-text-primary transition-colors"
            >
              <Trash2 size={12} strokeWidth={1.5} />
              Clear
            </button>
          )}
        </div>

        {error && (
          <div className="font-mono text-caption text-nd-accent border border-nd-accent/30 rounded-nd-compact px-3 py-2">
            [ERROR] {error}
          </div>
        )}

        {/* Results */}
        {simulationResult && (
          <div className="space-y-4 pt-3 border-t border-nd-border">
            <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Results</div>

            {/* Blast radius */}
            <div>
              <div className="flex justify-between font-mono text-caption mb-1">
                <span className="text-nd-text-disabled uppercase">Blast Radius</span>
                <span className="text-nd-accent font-bold">
                  {simulationResult.blast_radius} devices ({simulationResult.blast_radius_pct}%)
                </span>
              </div>
              <div className="h-2 flex gap-[2px]">
                {Array.from({ length: blastSegments }).map((_, i) => (
                  <div
                    key={i}
                    className="flex-1 h-full"
                    style={{ backgroundColor: i < blastFilled ? '#D71921' : '#E8E8E8' }}
                  />
                ))}
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-nd-surface-raised border border-nd-border rounded-nd-compact p-3">
                <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">Disconnected</div>
                <div className="font-mono text-heading font-bold text-nd-accent mt-1">
                  {simulationResult.disconnected_devices.length}
                </div>
              </div>
              <div className="bg-nd-surface-raised border border-nd-border rounded-nd-compact p-3">
                <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">Degraded</div>
                <div className="font-mono text-heading font-bold text-nd-warning mt-1">
                  {simulationResult.degraded_devices.length}
                </div>
              </div>
            </div>

            {/* Affected services */}
            {simulationResult.affected_services.length > 0 && (
              <div>
                <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled mb-1">Services Down</div>
                <div className="flex flex-wrap gap-1">
                  {simulationResult.affected_services.map((svc) => (
                    <span key={svc} className="font-mono text-label uppercase tracking-[0.06em] px-2 py-0.5 rounded-nd-pill border border-nd-accent/30 text-nd-accent">
                      {svc}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="font-mono text-caption">
              <span className="text-nd-text-disabled uppercase">Risk delta: </span>
              <span className="text-nd-accent font-bold">+{simulationResult.risk_delta}</span>
            </div>

            {/* Affected devices */}
            {simulationResult.disconnected_devices.length > 0 && (
              <div>
                <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled mb-1">
                  Affected Devices
                </div>
                <div className="space-y-1">
                  {simulationResult.disconnected_devices.slice(0, 10).map((d) => (
                    <div key={d.id} className="flex items-center justify-between py-1 border-b border-nd-border last:border-0">
                      <span className="font-mono text-caption text-nd-text-primary">{d.hostname || d.id.slice(0, 12)}</span>
                      <span className="font-mono text-label uppercase text-nd-accent">{d.status}</span>
                    </div>
                  ))}
                  {simulationResult.degraded_devices.slice(0, 5).map((d) => (
                    <div key={d.id} className="flex items-center justify-between py-1 border-b border-nd-border last:border-0">
                      <span className="font-mono text-caption text-nd-text-primary">{d.hostname || d.id.slice(0, 12)}</span>
                      <span className="font-mono text-label uppercase text-nd-warning">{d.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {simulationResult.recommendations.length > 0 && (
              <div>
                <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled mb-1">Recommendations</div>
                <div className="space-y-2">
                  {simulationResult.recommendations.map((rec, i) => (
                    <div key={i} className="border border-nd-border rounded-nd-compact p-2">
                      <div className="font-sans text-caption text-nd-text-primary">{i + 1}. {rec.action}</div>
                      <div className="font-mono text-label text-nd-text-disabled mt-0.5">{rec.impact}</div>
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
