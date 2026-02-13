import type { DeviceType, ConnectionType, DeviceStatus } from '../types/topology';

export const DEVICE_TYPE_COLORS: Record<DeviceType, string> = {
  router: '#818CF8', // Indigo-400
  switch: '#60A5FA', // Blue-400
  server: '#34D399', // Emerald-400
  firewall: '#FBBF24', // Amber-400
  ap: '#A78BFA', // Violet-400
  workstation: '#94A3B8', // Slate-400
  iot: '#F472B6', // Pink-400
  printer: '#FB923C', // Orange-400
  unknown: '#6B7280', // Gray-500
};

export const STATUS_COLORS: Record<DeviceStatus, string> = {
  online: '#34D399', // Emerald-400
  offline: '#F87171', // Red-400
  degraded: '#FBBF24', // Amber-400
};

export const CONNECTION_TYPE_COLORS: Record<ConnectionType, string> = {
  ethernet: '#475569', // Slate-600
  fiber: '#818CF8', // Indigo-400
  wireless: '#A78BFA', // Violet-400
  vpn: '#FBBF24', // Amber-400
  virtual: '#94A3B8', // Slate-400
};

export const CONNECTION_TYPE_STYLES: Record<ConnectionType, string> = {
  ethernet: 'solid',
  fiber: 'solid',
  wireless: 'dashed',
  vpn: 'dotted',
  virtual: 'dashed',
};

export function getRiskColor(score: number): string {
  if (score < 0.3) return '#34D399';
  if (score < 0.6) return '#FBBF24';
  if (score < 0.8) return '#FB923C';
  return '#F87171';
}

export function getRiskLabel(score: number): string {
  if (score < 0.3) return 'Low';
  if (score < 0.6) return 'Medium';
  if (score < 0.8) return 'High';
  return 'Critical';
}

export function getBandwidthWidth(bandwidth: string): number {
  if (!bandwidth) return 1;
  const bw = bandwidth.toLowerCase();
  if (bw.includes('10g')) return 4;
  if (bw.includes('1g')) return 2;
  if (bw.includes('100m')) return 1;
  return 1;
}

export function truncate(str: string, max: number = 16): string {
  if (str.length <= max) return str;
  return str.slice(0, max - 1) + '\u2026';
}

export function formatTimeAgo(dateStr: string): string {
  if (!dateStr) return 'unknown';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}s ago`;

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical': return '#EF4444';
    case 'high': return '#F97316';
    case 'medium': return '#F59E0B';
    case 'low': return '#3B82F6';
    case 'info': return '#6B7280';
    default: return '#6B7280';
  }
}

export function getSeverityIcon(severity: string): string {
  switch (severity) {
    case 'critical': return '🔴';
    case 'high': return '🟠';
    case 'medium': return '🟡';
    case 'low': return '🔵';
    case 'info': return '⚪';
    default: return '⚪';
  }
}
