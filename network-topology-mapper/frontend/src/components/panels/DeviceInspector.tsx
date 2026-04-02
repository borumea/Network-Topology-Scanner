import { useEffect, useState } from 'react';
import { X, Zap, Route } from 'lucide-react';
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

    const local = devices.find((d) => d.id === selectedDeviceId);
    if (local) setDevice(local);

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
    <div className="w-[380px] flex-shrink-0 h-full bg-nd-surface border-l border-nd-border overflow-y-auto animate-fade-in">
      {/* Header */}
      <div className="sticky top-0 bg-nd-surface border-b border-nd-border px-4 py-3 flex items-center justify-between z-10">
        <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Device Inspector</span>
        <button
          onClick={() => selectDevice(null)}
          className="text-nd-text-disabled hover:text-nd-text-primary transition-colors"
        >
          <X size={16} strokeWidth={1.5} />
        </button>
      </div>

      <div className="p-4 space-y-5">
        {/* Device identity header */}
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-nd-compact bg-nd-surface-raised border border-nd-border flex items-center justify-center flex-shrink-0">
            <DeviceIcon type={device.device_type} size={22} />
          </div>
          <div>
            <h3 className="text-subheading font-sans font-medium text-nd-text-display">
              {device.hostname || device.ip}
            </h3>
            <p className="font-mono text-caption text-nd-text-secondary">
              {device.vendor} {device.model}
              {device.os && ` \u00b7 ${device.os}`}
            </p>
            <div className="mt-1">
              <StatusBadge status={device.status} />
            </div>
          </div>
        </div>

        {/* Risk Score */}
        <div className="bg-nd-surface-raised rounded-nd-compact p-3 border border-nd-border">
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled mb-2">Risk Score</div>
          <RiskScore score={device.risk_score} size="md" />
          {device.risk_details?.factors && device.risk_details.factors.length > 0 && (
            <div className="mt-2 space-y-0.5">
              {device.risk_details.factors.map((f: string, i: number) => (
                <div key={i} className="font-mono text-caption text-nd-text-secondary">
                  {'\u2022'} {f}
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
          <InfoRow label="First Seen" value={formatDate(device.first_seen)} />
          <InfoRow label="Last Seen" value={formatTimeAgo(device.last_seen)} />
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
                <div key={port} className="flex items-center justify-between">
                  <span className="font-mono text-caption text-nd-text-primary">{port}/tcp</span>
                  <span className="font-mono text-caption text-nd-text-secondary">
                    {device.services[i] || 'unknown'}
                  </span>
                  <span className="font-mono text-label uppercase text-nd-success">open</span>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* Connected Devices */}
        {deviceConns.length > 0 && (
          <Section title={`Connected To (${deviceConns.length})`}>
            <div className="space-y-1">
              {deviceConns.map((conn) => {
                const peerId = conn.source_id === device.id ? conn.target_id : conn.source_id;
                const peer = devices.find((d) => d.id === peerId);
                return (
                  <button
                    key={conn.id}
                    onClick={() => selectDevice(peerId)}
                    className="w-full flex items-center justify-between py-1 border-b border-nd-border last:border-0 hover:bg-nd-surface-raised transition-colors text-left"
                  >
                    <span className="font-mono text-caption text-nd-text-primary">{peer?.hostname || peer?.ip || peerId.slice(0, 12)}</span>
                    <span className="font-mono text-label uppercase text-nd-text-disabled">{conn.connection_type}</span>
                  </button>
                );
              })}
            </div>
          </Section>
        )}

        {/* Dependencies */}
        <Section title="Dependencies">
          {deps.depends_on.length > 0 && (
            <div className="space-y-1">
              {deps.depends_on.map((dep) => (
                <div key={dep.id} className="font-mono text-caption text-nd-text-secondary">
                  <span className="text-nd-text-disabled mr-1">{'\u2191'}</span>
                  Depends on: {dep.target_id.slice(0, 8)} ({dep.dependency_type})
                </div>
              ))}
            </div>
          )}
          {deps.depended_by.length > 0 && (
            <div className="font-mono text-caption text-nd-text-secondary mt-1">
              <span className="text-nd-text-disabled mr-1">{'\u2193'}</span>
              {deps.depended_by.length} devices depend on this
            </div>
          )}
          {deps.depends_on.length === 0 && deps.depended_by.length === 0 && (
            <div className="font-mono text-caption text-nd-text-disabled">No dependencies tracked</div>
          )}
        </Section>

        {/* Actions */}
        <div className="flex flex-wrap gap-2 pt-2">
          <button
            onClick={handleSimulate}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-nd-pill border border-nd-accent font-mono text-label uppercase tracking-[0.06em] text-nd-accent hover:bg-nd-accent/10 transition-colors"
          >
            <Zap size={12} strokeWidth={1.5} />
            Simulate Failure
          </button>
          <button
            onClick={() => setCurrentView('topology')}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-nd-pill border border-nd-border-visible font-mono text-label uppercase tracking-[0.06em] text-nd-text-secondary hover:text-nd-text-primary hover:border-nd-text-disabled transition-colors"
          >
            <Route size={12} strokeWidth={1.5} />
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
      <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled mb-2 border-b border-nd-border pb-1">
        {title}
      </div>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-0.5">
      <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">{label}</span>
      <span className="font-mono text-caption text-nd-text-primary text-right max-w-[200px] truncate">{value}</span>
    </div>
  );
}
