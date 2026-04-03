import { useState, useEffect, RefObject } from 'react';
import type { Device } from '../../types/topology';
import { formatTimeAgo, getRiskColor } from '../../lib/graph-utils';

interface Props {
  containerRef: RefObject<HTMLDivElement>;
  devices: Device[];
}

interface EdgeTooltipData {
  x: number; y: number;
  connection_type: string; bandwidth: string;
  latency: number | undefined; status: string; is_redundant: boolean;
}

export default function NodeTooltip({ containerRef, devices }: Props) {
  const [tooltip, setTooltip] = useState<{ deviceId: string; x: number; y: number } | null>(null);
  const [edgeTooltip, setEdgeTooltip] = useState<EdgeTooltipData | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const nodeHandler = (e: Event) => { const d = (e as CustomEvent).detail; setTooltip(d); if (d) setEdgeTooltip(null); };
    const edgeHandler = (e: Event) => { const d = (e as CustomEvent).detail; setEdgeTooltip(d); if (d) setTooltip(null); };
    el.addEventListener('node-hover', nodeHandler);
    el.addEventListener('edge-hover', edgeHandler);
    return () => { el.removeEventListener('node-hover', nodeHandler); el.removeEventListener('edge-hover', edgeHandler); };
  }, [containerRef]);

  // Edge tooltip
  if (edgeTooltip) {
    const statusColor = edgeTooltip.status === 'active' ? '#4A9E5C' : edgeTooltip.status === 'flapping' ? '#D71921' : '#D4A843';

    return (
      <div
        className="absolute z-50 bg-nd-surface border border-nd-border-visible rounded-nd-compact pointer-events-none min-w-[200px] animate-fade-in"
        style={{ left: edgeTooltip.x + 16, top: edgeTooltip.y - 12 }}
      >
        <div className="flex items-center gap-2 px-3 py-2 border-b border-nd-border">
          <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-primary">{edgeTooltip.connection_type}</span>
          <span className="ml-auto w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColor }} />
        </div>
        <div className="px-3 py-2 grid grid-cols-2 gap-x-4 gap-y-1.5">
          <div>
            <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Bandwidth</div>
            <div className="font-mono text-caption text-nd-text-primary">{edgeTooltip.bandwidth}</div>
          </div>
          <div>
            <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Latency</div>
            <div className="font-mono text-caption text-nd-text-primary">{edgeTooltip.latency != null ? `${edgeTooltip.latency}ms` : '\u2014'}</div>
          </div>
          <div>
            <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Status</div>
            <div className="font-mono text-caption uppercase" style={{ color: statusColor }}>{edgeTooltip.status}</div>
          </div>
          {edgeTooltip.is_redundant && (
            <div>
              <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Redundant</div>
              <div className="font-mono text-caption text-[#4A9E5C]">Yes</div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Node tooltip
  if (!tooltip) return null;
  const device = devices.find((d) => d.id === tooltip.deviceId);
  if (!device) return null;

  const statusColor = device.status === 'online' ? '#4A9E5C' : device.status === 'offline' ? '#D71921' : '#D4A843';

  return (
    <div
      className="absolute z-50 bg-nd-surface border border-nd-border-visible rounded-nd-compact pointer-events-none min-w-[240px] animate-fade-in"
      style={{ left: tooltip.x + 20, top: tooltip.y - 20 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-nd-border">
        <div>
          <div className="text-body-sm font-sans font-medium text-nd-text-display">{device.hostname || 'Unknown'}</div>
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">{device.device_type}</div>
        </div>
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: statusColor }} />
      </div>

      {/* Data grid */}
      <div className="px-3 py-2 grid grid-cols-2 gap-x-4 gap-y-1.5">
        <div>
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">IP</div>
          <div className="font-mono text-caption text-nd-text-primary">{device.ip}</div>
        </div>
        <div>
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Tier</div>
          <div className="font-mono text-caption text-nd-text-primary">Level {device.tier}</div>
        </div>
        <div>
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Risk</div>
          <div className="font-mono text-caption font-bold" style={{ color: getRiskColor(device.risk_score) }}>{device.risk_score.toFixed(1)}</div>
        </div>
        <div>
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Last Seen</div>
          <div className="font-mono text-caption text-nd-text-secondary">{formatTimeAgo(device.last_seen)}</div>
        </div>
      </div>

      {/* Footer */}
      {device.vendor && (
        <div className="px-3 py-1.5 border-t border-nd-border font-mono text-label uppercase tracking-[0.06em] text-nd-text-disabled flex justify-between">
          <span>{device.vendor}</span>
          <span>{device.model || '\u2014'}</span>
        </div>
      )}
    </div>
  );
}
