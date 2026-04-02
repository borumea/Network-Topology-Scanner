import { useTopology } from './hooks/useTopology';
import { useTopologyStore } from './stores/topologyStore';
import AppShell from './components/layout/AppShell';
import MetricsBar from './components/dashboard/MetricsBar';
import NetworkCanvas from './components/graph/NetworkCanvas';
import DeviceInspector from './components/panels/DeviceInspector';
import AlertFeed from './components/panels/AlertFeed';
import SimulationPanel from './components/panels/SimulationPanel';
import ScanStatus from './components/panels/ScanStatus';
import ResilienceReport from './components/panels/ResilienceReport';
import RiskHeatmap from './components/dashboard/RiskHeatmap';
import TimelineView from './components/dashboard/TimelineView';
import DependencyMatrix from './components/dashboard/DependencyMatrix';
import { useFilterStore } from './stores/filterStore';

function TopologyView() {
  const { rightPanelContent, selectedDeviceId } = useTopologyStore();

  return (
    <div className="flex flex-col h-full">
      <MetricsBar />
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 min-w-0 relative">
          <NetworkCanvas />
        </div>
        {rightPanelContent === 'device' && selectedDeviceId && <DeviceInspector />}
        {rightPanelContent === 'alerts' && <AlertFeed />}
        {rightPanelContent === 'simulation' && <SimulationPanel />}
      </div>
    </div>
  );
}

function DashboardView() {
  const { stats, spofs } = useTopologyStore();

  if (!stats) return <div className="p-6 font-mono text-caption text-nd-text-disabled">[LOADING...]</div>;

  const typeEntries = Object.entries(stats.type_counts).sort((a, b) => b[1] - a[1]);

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <h1 className="font-display text-display-md font-bold text-black">Dashboard</h1>

        <MetricsBar />

        <div className="grid grid-cols-2 gap-6">
          {/* Device types breakdown */}
          <div className="bg-nd-surface rounded-nd-card p-5 border border-nd-border">
            <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary mb-4">Device Types</div>
            <div className="space-y-3">
              {typeEntries.map(([type, count]) => {
                const segments = 10;
                const filled = Math.round((count / stats.total_devices) * segments);
                return (
                  <div key={type} className="flex items-center gap-3">
                    <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled w-24">{type}</span>
                    <div className="flex-1 h-2 flex gap-[2px]">
                      {Array.from({ length: segments }).map((_, i) => (
                        <div
                          key={i}
                          className="flex-1 h-full"
                          style={{ backgroundColor: i < filled ? '#1A1A1A' : '#E8E8E8' }}
                        />
                      ))}
                    </div>
                    <span className="font-mono text-caption text-nd-text-secondary w-8 text-right">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Status breakdown */}
          <div className="bg-nd-surface rounded-nd-card p-5 border border-nd-border">
            <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary mb-4">Status</div>
            <div className="flex gap-6 items-end h-32">
              <StatusBar label="Online" count={stats.online} total={stats.total_devices} color="#4A9E5C" />
              <StatusBar label="Offline" count={stats.offline} total={stats.total_devices} color="#D71921" />
              <StatusBar label="Degraded" count={stats.degraded} total={stats.total_devices} color="#D4A843" />
            </div>
          </div>
        </div>

        <DependencyMatrix />
      </div>
    </div>
  );
}

function StatusBar({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex-1 flex flex-col items-center gap-2">
      <span className="font-mono text-heading font-bold" style={{ color }}>{count}</span>
      <div className="w-full overflow-hidden" style={{ height: `${Math.max(pct, 5)}%`, minHeight: 4 }}>
        <div className="w-full h-full" style={{ backgroundColor: color }} />
      </div>
      <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">{label}</span>
    </div>
  );
}

function SettingsView() {
  const { showLabels, setShowLabels, showRiskHalos, setShowRiskHalos } = useFilterStore();

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="font-display text-display-md font-bold text-black">Settings</h1>

        <div className="bg-nd-surface rounded-nd-card p-5 border border-nd-border space-y-4">
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Scan Configuration</div>

          <div className="space-y-3">
            <SettingRow label="Full Scan Interval" description="How often to run a complete network scan">
              <select className="bg-nd-surface-raised border border-nd-border-visible rounded-nd-compact px-3 py-1.5 font-mono text-caption text-nd-text-primary outline-none focus:border-nd-text-disabled transition-colors">
                <option value="3600">Every 1 hour</option>
                <option value="7200">Every 2 hours</option>
                <option value="21600">Every 6 hours</option>
                <option value="86400">Every 24 hours</option>
              </select>
            </SettingRow>

            <SettingRow label="SNMP Poll Interval" description="Frequency of SNMP device queries">
              <select className="bg-nd-surface-raised border border-nd-border-visible rounded-nd-compact px-3 py-1.5 font-mono text-caption text-nd-text-primary outline-none focus:border-nd-text-disabled transition-colors">
                <option value="900">Every 15 min</option>
                <option value="1800">Every 30 min</option>
                <option value="3600">Every 1 hour</option>
              </select>
            </SettingRow>

            <SettingRow label="Agent Mode" description="How the system responds to findings">
              <select className="bg-nd-surface-raised border border-nd-border-visible rounded-nd-compact px-3 py-1.5 font-mono text-caption text-nd-text-primary outline-none focus:border-nd-text-disabled transition-colors">
                <option value="alert">Alert Only</option>
                <option value="interactive">Interactive</option>
                <option value="autonomous">Autonomous</option>
              </select>
            </SettingRow>
          </div>
        </div>

        <div className="bg-nd-surface rounded-nd-card p-5 border border-nd-border space-y-4">
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Display</div>
          <div className="space-y-3">
            <ToggleRow label="Show node labels" checked={showLabels} onChange={setShowLabels} />
            <ToggleRow label="Show risk indicators" checked={showRiskHalos} onChange={setShowRiskHalos} />
          </div>
        </div>

        <div className="bg-nd-surface rounded-nd-card p-5 border border-nd-border">
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary mb-2">About</div>
          <div className="space-y-1">
            <p className="font-mono text-caption text-nd-text-primary">Network Topology Mapper v1.0.0</p>
            <p className="text-caption text-nd-text-secondary">Real-time network discovery, visualization, and resilience analysis.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function SettingRow({ label, description, children }: { label: string; description: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-1 border-b border-nd-border last:border-0">
      <div>
        <div className="font-sans text-body-sm text-nd-text-primary">{label}</div>
        <div className="font-mono text-label text-nd-text-disabled">{description}</div>
      </div>
      {children}
    </div>
  );
}

function ToggleRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between py-1 border-b border-nd-border last:border-0">
      <span className="font-sans text-body-sm text-nd-text-primary">{label}</span>
      <button
        onClick={() => onChange(!checked)}
        className={`w-10 h-5 rounded-nd-pill relative transition-colors border ${checked ? 'bg-black border-black' : 'bg-nd-surface-raised border-nd-border-visible'}`}
      >
        <div className={`absolute top-0.5 w-4 h-4 rounded-full transition-all ${checked ? 'left-5 bg-white' : 'left-0.5 bg-nd-text-secondary'}`} />
      </button>
    </div>
  );
}

function SimulateView() {
  return (
    <div className="flex h-full">
      <div className="flex-1 relative">
        <NetworkCanvas />
      </div>
      <SimulationPanel />
    </div>
  );
}

function AlertsView() {
  return (
    <div className="flex h-full">
      <div className="flex-1 relative">
        <NetworkCanvas />
      </div>
      <AlertFeed />
    </div>
  );
}

export default function App() {
  useTopology();
  const { currentView } = useTopologyStore();

  const viewMap: Record<string, React.ReactNode> = {
    topology: <TopologyView />,
    dashboard: <DashboardView />,
    scan: <ScanStatus />,
    simulate: <SimulateView />,
    alerts: <AlertsView />,
    heatmap: <RiskHeatmap />,
    timeline: <TimelineView />,
    reports: <ResilienceReport />,
    settings: <SettingsView />,
  };

  return (
    <AppShell>
      {viewMap[currentView] || <TopologyView />}
    </AppShell>
  );
}
