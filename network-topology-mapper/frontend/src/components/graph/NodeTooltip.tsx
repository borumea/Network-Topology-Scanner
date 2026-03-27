import { useState, useEffect, RefObject } from 'react';
import type { Device } from '../../types/topology';
import DeviceIcon from '../shared/DeviceIcon';
import StatusBadge from '../shared/StatusBadge';
import { formatTimeAgo, getRiskColor, CONNECTION_TYPE_COLORS } from '../../lib/graph-utils';
import { Cable, Wifi, Globe, Shield, Zap } from 'lucide-react';

interface Props {
  containerRef: RefObject<HTMLDivElement>;
  devices: Device[];
}

interface EdgeTooltipData {
  x: number; y: number;
  connection_type: string; bandwidth: string;
  latency: number | undefined; status: string; is_redundant: boolean;
}

const CONNECTION_ICONS: Record<string, typeof Cable> = {
  ethernet: Cable, fiber: Zap, wireless: Wifi, vpn: Shield, virtual: Globe,
};

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

  if (edgeTooltip) {
    const ConnIcon = CONNECTION_ICONS[edgeTooltip.connection_type] || Cable;
    const color = CONNECTION_TYPE_COLORS[edgeTooltip.connection_type as keyof typeof CONNECTION_TYPE_COLORS] || '#5C5C5F';
    const statusColor = edgeTooltip.status === 'active' ? '#34D399' : edgeTooltip.status === 'flapping' ? '#F87171' : '#FBBF24';

    return (
      <div className="absolute z-50 bg-bg-secondary border border-border rounded-lg shadow-lg pointer-events-none min-w-[200px] animate-fade-in" style={{ left: edgeTooltip.x + 16, top: edgeTooltip.y - 12 }}>
        <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
          <ConnIcon size={13} style={{ color }} />
          <span className="text-[12px] font-medium capitalize" style={{ color }}>{edgeTooltip.connection_type}</span>
          <span className="ml-auto w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColor }} />
        </div>
        <div className="px-3 py-2 grid grid-cols-2 gap-x-4 gap-y-1.5 text-[12px]">
          <div><div className="text-text-muted text-[10px]">Bandwidth</div><div className="text-text-secondary">{edgeTooltip.bandwidth}</div></div>
          <div><div className="text-text-muted text-[10px]">Latency</div><div className="text-text-secondary">{edgeTooltip.latency != null ? `${edgeTooltip.latency}ms` : '—'}</div></div>
          <div><div className="text-text-muted text-[10px]">Status</div><div className="capitalize" style={{ color: statusColor }}>{edgeTooltip.status}</div></div>
          {edgeTooltip.is_redundant && <div><div className="text-text-muted text-[10px]">Redundant</div><div className="text-status-online">Yes</div></div>}
        </div>
      </div>
    );
  }

  if (!tooltip) return null;
  const device = devices.find((d) => d.id === tooltip.deviceId);
  if (!device) return null;

  return (
    <div className="absolute z-50 bg-bg-secondary border border-border rounded-lg shadow-lg pointer-events-none min-w-[250px] animate-fade-in" style={{ left: tooltip.x + 20, top: tooltip.y - 20 }}>
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <div className="flex items-center gap-2">
          <DeviceIcon type={device.device_type} size={14} />
          <div>
            <div className="text-[13px] font-medium text-text-primary">{device.hostname || 'Unknown'}</div>
            <div className="text-[10px] text-text-muted capitalize">{device.device_type}</div>
          </div>
        </div>
        <StatusBadge status={device.status} size={8} />
      </div>
      <div className="px-3 py-2 grid grid-cols-2 gap-x-4 gap-y-1.5 text-[12px]">
        <div><div className="text-text-muted text-[10px]">IP</div><div className="text-text-secondary font-mono">{device.ip}</div></div>
        <div><div className="text-text-muted text-[10px]">Tier</div><div className="text-text-secondary">Level {device.tier}</div></div>
        <div><div className="text-text-muted text-[10px]">Risk</div><div className="font-medium" style={{ color: getRiskColor(device.risk_score) }}>{device.risk_score.toFixed(1)}</div></div>
        <div><div className="text-text-muted text-[10px]">Last seen</div><div className="text-text-muted">{formatTimeAgo(device.last_seen)}</div></div>
      </div>
      {device.vendor && (
        <div className="px-3 py-1.5 border-t border-border text-[10px] text-text-muted flex justify-between">
          <span>{device.vendor}</span><span>{device.model || '—'}</span>
        </div>
      )}
    </div>
  );
}
