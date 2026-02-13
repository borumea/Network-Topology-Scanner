
import { useState, useEffect, RefObject } from 'react';
import type { Device } from '../../types/topology';
import DeviceIcon from '../shared/DeviceIcon';
import StatusBadge from '../shared/StatusBadge';
import { formatTimeAgo, getRiskColor, CONNECTION_TYPE_COLORS } from '../../lib/graph-utils';
import { Activity, Clock, Box, Wifi, Cable, Globe, Shield, Zap } from 'lucide-react';

interface Props {
  containerRef: RefObject<HTMLDivElement>;
  devices: Device[];
}

interface EdgeTooltipData {
  x: number;
  y: number;
  connection_type: string;
  bandwidth: string;
  latency: number | undefined;
  status: string;
  is_redundant: boolean;
}

const CONNECTION_ICONS: Record<string, typeof Cable> = {
  ethernet: Cable,
  fiber: Zap,
  wireless: Wifi,
  vpn: Shield,
  virtual: Globe,
};

export default function NodeTooltip({ containerRef, devices }: Props) {
  const [tooltip, setTooltip] = useState<{ deviceId: string; x: number; y: number } | null>(null);
  const [edgeTooltip, setEdgeTooltip] = useState<EdgeTooltipData | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const nodeHandler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      setTooltip(detail);
      if (detail) setEdgeTooltip(null);
    };

    const edgeHandler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      setEdgeTooltip(detail);
      if (detail) setTooltip(null);
    };

    el.addEventListener('node-hover', nodeHandler);
    el.addEventListener('edge-hover', edgeHandler);
    return () => {
      el.removeEventListener('node-hover', nodeHandler);
      el.removeEventListener('edge-hover', edgeHandler);
    };
  }, [containerRef]);

  // ── Edge tooltip ──
  if (edgeTooltip) {
    const ConnIcon = CONNECTION_ICONS[edgeTooltip.connection_type] || Cable;
    const color = CONNECTION_TYPE_COLORS[edgeTooltip.connection_type as keyof typeof CONNECTION_TYPE_COLORS] || '#6B7280';
    const statusColor = edgeTooltip.status === 'active' ? '#34D399'
      : edgeTooltip.status === 'flapping' ? '#F87171'
      : edgeTooltip.status === 'disabled' ? '#6B7280'
      : '#FBBF24';

    return (
      <div
        className="absolute z-50 bg-[#0F1115]/95 backdrop-blur-md border border-white/10 rounded-lg p-0 shadow-2xl pointer-events-none min-w-[200px] animate-fade-in font-mono text-sm"
        style={{
          left: edgeTooltip.x + 16,
          top: edgeTooltip.y - 12,
        }}
      >
        <div className="flex items-center gap-2 p-2.5 border-b border-white/5 bg-white/5 rounded-t-lg">
          <ConnIcon size={14} style={{ color }} />
          <span className="text-xs font-bold uppercase tracking-wider" style={{ color }}>
            {edgeTooltip.connection_type}
          </span>
          <span
            className="ml-auto w-2 h-2 rounded-full"
            style={{ backgroundColor: statusColor }}
          />
        </div>
        <div className="p-2.5 grid grid-cols-2 gap-2">
          <div>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider">Bandwidth</div>
            <div className="text-gray-300 text-xs">{edgeTooltip.bandwidth}</div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider">Latency</div>
            <div className="text-gray-300 text-xs">
              {edgeTooltip.latency != null ? `${edgeTooltip.latency}ms` : 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 uppercase tracking-wider">Status</div>
            <div className="text-xs capitalize" style={{ color: statusColor }}>{edgeTooltip.status}</div>
          </div>
          {edgeTooltip.is_redundant && (
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider">Redundant</div>
              <div className="text-emerald-400 text-xs">Yes</div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Node tooltip ──
  if (!tooltip) return null;

  const device = devices.find((d) => d.id === tooltip.deviceId);
  if (!device) return null;

  return (
    <div
      className="absolute z-50 bg-[#0F1115]/95 backdrop-blur-md border border-white/10 rounded-lg p-0 shadow-2xl pointer-events-none min-w-[280px] animate-fade-in font-mono text-sm"
      style={{
        left: tooltip.x + 20,
        top: tooltip.y - 20,
      }}
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between p-3 border-b border-white/5 bg-white/5 rounded-t-lg">
        <div className="flex items-center gap-3">
          <div className={`p-1.5 rounded-md bg-black/40 border border-white/10`}>
            <DeviceIcon type={device.device_type} size={16} className="text-blue-400" />
          </div>
          <div>
            <div className="font-bold text-white tracking-tight">{device.hostname || 'Unknown Host'}</div>
            <div className="text-[10px] text-blue-400 uppercase tracking-wider font-semibold opacity-80">{device.device_type}</div>
          </div>
        </div>
        <StatusBadge status={device.status} size={8} />
      </div>

      {/* Stats Grid - Technical Look */}
      <div className="p-3 grid grid-cols-2 gap-px bg-white/5">
        <div className="bg-[#0F1115] p-2">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-0.5">IP Address</div>
          <div className="text-gray-300">{device.ip}</div>
        </div>
        <div className="bg-[#0F1115] p-2">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-0.5">Tier</div>
          <div className="text-gray-300">Level {device.tier}</div>
        </div>
        <div className="bg-[#0F1115] p-2">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-0.5">Risk Score</div>
          <span className="font-bold" style={{ color: getRiskColor(device.risk_score) }}>
            {device.risk_score.toFixed(1)} / 10
          </span>
        </div>
        <div className="bg-[#0F1115] p-2">
          <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-0.5">Last Seen</div>
          <div className="text-gray-400 text-xs">{formatTimeAgo(device.last_seen)}</div>
        </div>
      </div>

      {/* Footer Details */}
      {device.vendor && (
        <div className="p-2 border-t border-white/5 bg-[#0F1115]/50 rounded-b-lg flex justify-between items-center text-[10px] text-gray-500">
          <span>VENDOR: {device.vendor.toUpperCase()}</span>
          <span>MODEL: {device.model || 'N/A'}</span>
        </div>
      )}
    </div>
  );
}
