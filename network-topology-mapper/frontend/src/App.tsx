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
import { Settings } from 'lucide-react';

function TopologyView() {
  const { rightPanelContent, selectedDeviceId } = useTopologyStore();

  return (
    <div className="flex flex-col h-full">
      <MetricsBar />
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 relative">
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
  const { stats, devices, spofs } = useTopologyStore();

  if (!stats) return <div className="p-6 text-text-muted">Loading...</div>;

  const typeEntries = Object.entries(stats.type_counts).sort((a, b) => b[1] - a[1]);

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <h1 className="text-xl font-bold text-text-primary">Dashboard</h1>

        <MetricsBar />

        <div className="grid grid-cols-2 gap-6">
          {/* Device types breakdown */}
          <div className="bg-bg-secondary rounded-xl p-5 border border-bg-tertiary">
            <h3 className="text-sm font-semibold text-text-primary mb-4">Device Types</h3>
            <div className="space-y-3">
              {typeEntries.map(([type, count]) => (
                <div key={type} className="flex items-center gap-3">
                  <span className="text-xs text-text-secondary capitalize w-24">{type}</span>
                  <div className="flex-1 h-2 bg-bg-tertiary rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${(count / stats.total_devices) * 100}%`,
                        backgroundColor: `var(--node-${type}, #6B7280)`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-text-muted w-8 text-right">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Status breakdown */}
          <div className="bg-bg-secondary rounded-xl p-5 border border-bg-tertiary">
            <h3 className="text-sm font-semibold text-text-primary mb-4">Device Status</h3>
            <div className="flex gap-6 items-end h-32">
              <StatusBar label="Online" count={stats.online} total={stats.total_devices} color="#10B981" />
              <StatusBar label="Offline" count={stats.offline} total={stats.total_devices} color="#EF4444" />
              <StatusBar label="Degraded" count={stats.degraded} total={stats.total_devices} color="#F59E0B" />
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
      <span className="text-lg font-bold" style={{ color }}>{count}</span>
      <div className="w-full bg-bg-tertiary rounded-full overflow-hidden" style={{ height: `${Math.max(pct, 5)}%`, minHeight: 4 }}>
        <div className="w-full h-full rounded-full" style={{ backgroundColor: color }} />
      </div>
      <span className="text-[10px] text-text-muted">{label}</span>
    </div>
  );
}

function SettingsView() {
  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-xl font-bold text-text-primary">Settings</h1>

        <div className="bg-bg-secondary rounded-xl p-5 border border-bg-tertiary space-y-4">
          <h3 className="text-sm font-semibold text-text-primary">Scan Configuration</h3>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-text-primary">Full Scan Interval</div>
                <div className="text-[10px] text-text-muted">How often to run a complete network scan</div>
              </div>
              <select className="bg-bg-tertiary border border-bg-tertiary rounded-lg px-3 py-1.5 text-xs text-text-primary outline-none">
                <option value="3600">Every 1 hour</option>
                <option value="7200">Every 2 hours</option>
                <option value="21600" selected>Every 6 hours</option>
                <option value="86400">Every 24 hours</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-text-primary">SNMP Poll Interval</div>
                <div className="text-[10px] text-text-muted">Frequency of SNMP device queries</div>
              </div>
              <select className="bg-bg-tertiary border border-bg-tertiary rounded-lg px-3 py-1.5 text-xs text-text-primary outline-none">
                <option value="900">Every 15 min</option>
                <option value="1800" selected>Every 30 min</option>
                <option value="3600">Every 1 hour</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-text-primary">Agent Mode</div>
                <div className="text-[10px] text-text-muted">How the system responds to findings</div>
              </div>
              <select className="bg-bg-tertiary border border-bg-tertiary rounded-lg px-3 py-1.5 text-xs text-text-primary outline-none">
                <option value="alert" selected>Alert Only</option>
                <option value="interactive">Interactive</option>
                <option value="autonomous">Autonomous</option>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-bg-secondary rounded-xl p-5 border border-bg-tertiary space-y-4">
          <h3 className="text-sm font-semibold text-text-primary">Display</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-primary">Show node labels</span>
              <input type="checkbox" defaultChecked className="accent-node-switch" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-primary">Show risk halos</span>
              <input type="checkbox" defaultChecked className="accent-node-switch" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-primary">Animation enabled</span>
              <input type="checkbox" defaultChecked className="accent-node-switch" />
            </div>
          </div>
        </div>

        <div className="bg-bg-secondary rounded-xl p-5 border border-bg-tertiary">
          <h3 className="text-sm font-semibold text-text-primary mb-2">About</h3>
          <div className="text-xs text-text-secondary space-y-1">
            <p>Network Topology Mapper v1.0.0</p>
            <p>Real-time network discovery, visualization, and resilience analysis.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function SimulateView() {
  const { setRightPanelContent } = useTopologyStore();

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
