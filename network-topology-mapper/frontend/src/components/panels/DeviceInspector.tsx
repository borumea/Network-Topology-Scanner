import { useEffect, useState } from 'react';
import { X, ExternalLink, AlertTriangle, Zap, Route, FileText } from 'lucide-react';
import { useTopologyStore } from '../../stores/topologyStore';
import { fetchDevice, fetchDeviceDependencies } from '../../lib/api';
import DeviceIcon from '../shared/DeviceIcon';
import StatusBadge from '../shared/StatusBadge';
import RiskScore from '../shared/RiskScore';
import { formatTimeAgo, formatDate } from '../../lib/graph-utils';
import type { Device, Dependency } from '../../types/topology';

export default function DeviceInspector() {
  const { selectedDeviceId, selectDevice, devices, connections, setRightPanelContent, setCurrentView, addSimulationTarget } = useTopologyStore();
  const [device, setDevice] = useState<Device | null>(null);
  const [deps, setDeps] = useState<{ depends_on: Dependency[]; depended_by: Dependency[] }>({
    depends_on: [],
    depended_by: [],
  });

  useEffect(() => {
    if (!selectedDeviceId) {
      setDevice(null);
      return;
    }

    // First try local store
    const local = devices.find((d) => d.id === selectedDeviceId);
    if (local) setDevice(local);

    // Then fetch full details from API
    fetchDevice(selectedDeviceId)
      .then((d) => { if (d && !d.error) setDevice(d); })
      .catch(() => {});

    fetchDeviceDependencies(selectedDeviceId)
      .then((data) => {
        setDeps({
          depends_on: data.depends_on || [],
          depended_by: data.depended_by || [],
        });
      })
      .catch(() => {});
  }, [selectedDeviceId, devices]);

  if (!device) return null;

  const deviceConns = connections.filter(
    (c) => c.source_id === device.id || c.target_id === device.id
  );
  const activeConns = deviceConns.filter((c) => c.status === 'active').length;

  const handleSimulate = () => {
    addSimulationTarget('nodes', device.id);
    setRightPanelContent('simulation');
    setCurrentView('simulate');
  };

  return (
    <div className="w-[380px] h-full bg-bg-secondary border-l border-bg-tertiary overflow-y-auto animate-slide-in-right">
      <div className="sticky top-0 bg-bg-secondary border-b border-bg-tertiary px-4 py-3 flex items-center justify-between z-10">
        <span className="text-sm font-semibold text-text-primary">Device Inspector</span>
        <button
          onClick={() => selectDevice(null)}
          className="text-text-muted hover:text-text-primary transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-bg-tertiary flex items-center justify-center flex-shrink-0">
            <DeviceIcon type={device.device_type} size={22} />
          </div>
          <div>
            <h3 className="text-base font-semibold text-text-primary">
              {device.hostname || device.ip}
            </h3>
            <p className="text-xs text-text-secondary">
              {device.vendor} {device.model}
              {device.os && ` \u00b7 ${device.os}`}
            </p>
            <div className="mt-1">
              <StatusBadge status={device.status} />
            </div>
          </div>
        </div>

        {/* Risk Score */}
        <div className="bg-bg-tertiary rounded-lg p-3">
          <div className="text-xs text-text-muted mb-2">Risk Score</div>
          <RiskScore score={device.risk_score} size="md" />
          {device.risk_details?.factors && device.risk_details.factors.length > 0 && (
            <div className="mt-2 text-xs text-text-muted">
              {device.risk_details.factors.map((f, i) => (
                <div key={i} className="flex items-start gap-1 mt-0.5">
                  <AlertTriangle size={10} className="flex-shrink-0 mt-0.5 text-risk-medium" />
                  <span>{f}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Identity */}
        <Section title="Identity">
          <InfoRow label="IP" value={device.ip} />
          <InfoRow label="MAC" value={device.mac} />
          <InfoRow label="Vendor" value={device.vendor} />
          <InfoRow label="Type" value={device.device_type} />
          <InfoRow label="First seen" value={formatDate(device.first_seen)} />
          <InfoRow label="Last seen" value={formatTimeAgo(device.last_seen)} />
          <InfoRow label="Discovery" value={device.discovery_method} />
        </Section>

        {/* Network */}
        <Section title="Network">
          <InfoRow label="VLANs" value={device.vlan_ids.join(', ') || 'None'} />
          <InfoRow label="Subnet" value={device.subnet || 'Unknown'} />
          <InfoRow label="Gateway" value={device.is_gateway ? 'Yes' : 'No'} />
          <InfoRow label="Connections" value={`${activeConns} active / ${deviceConns.length} total`} />
          {device.location && <InfoRow label="Location" value={device.location} />}
        </Section>

        {/* Open Ports */}
        {device.open_ports.length > 0 && (
          <Section title="Open Ports">
            <div className="space-y-1">
              {device.open_ports.map((port, i) => (
                <div key={port} className="flex items-center justify-between text-xs">
                  <span className="text-text-primary font-mono">{port}/tcp</span>
                  <span className="text-text-secondary">
                    {device.services[i] || 'unknown'}
                  </span>
                  <span className="text-status-online text-[10px]">open</span>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* Dependencies */}
        <Section title="Dependencies">
          {deps.depends_on.length > 0 && (
            <div className="space-y-1">
              {deps.depends_on.map((dep) => (
                <div key={dep.id} className="text-xs text-text-secondary">
                  <span className="text-text-muted mr-1">\u2191</span>
                  Depends on: {dep.target_id.slice(0, 8)} ({dep.dependency_type})
                </div>
              ))}
            </div>
          )}
          {deps.depended_by.length > 0 && (
            <div className="text-xs text-text-secondary mt-1">
              <span className="text-text-muted mr-1">\u2193</span>
              {deps.depended_by.length} devices depend on this
            </div>
          )}
          {deps.depends_on.length === 0 && deps.depended_by.length === 0 && (
            <div className="text-xs text-text-muted">No dependencies tracked</div>
          )}
        </Section>

        {/* Actions */}
        <div className="flex flex-wrap gap-2 pt-2">
          <button
            onClick={handleSimulate}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-risk-critical/10 text-risk-critical text-xs font-medium hover:bg-risk-critical/20 transition-colors"
          >
            <Zap size={12} />
            Simulate Failure
          </button>
          <button
            onClick={() => setCurrentView('topology')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-bg-tertiary text-text-secondary text-xs font-medium hover:text-text-primary transition-colors"
          >
            <Route size={12} />
            Show Paths
          </button>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] text-text-muted uppercase tracking-wider mb-2 border-b border-bg-tertiary pb-1">
        {title}
      </div>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-0.5 text-xs">
      <span className="text-text-muted">{label}</span>
      <span className="text-text-secondary font-mono text-right max-w-[200px] truncate">{value}</span>
    </div>
  );
}
