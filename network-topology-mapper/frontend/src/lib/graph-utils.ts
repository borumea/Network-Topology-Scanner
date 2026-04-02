import type { DeviceType, ConnectionType, DeviceStatus } from '../types/topology';

// Nothing light-mode: monochrome nodes. Device types differentiated by shape/icon,
// not fill color. These are used only for the minimap dots and legend.
export const DEVICE_TYPE_COLORS: Record<DeviceType, string> = {
  router: '#1A1A1A',
  switch: '#333333',
  server: '#4D4D4D',
  firewall: '#1A1A1A',
  ap: '#666666',
  workstation: '#808080',
  iot: '#999999',
  printer: '#808080',
  unknown: '#CCCCCC',
};

export const STATUS_COLORS: Record<DeviceStatus, string> = {
  online: '#4A9E5C',
  offline: '#D71921',
  degraded: '#D4A843',
};

export const CONNECTION_TYPE_COLORS: Record<ConnectionType, string> = {
  ethernet: '#CCCCCC',
  fiber: '#999999',
  wireless: '#CCCCCC',
  vpn: '#CCCCCC',
  virtual: '#CCCCCC',
};

export const CONNECTION_TYPE_STYLES: Record<ConnectionType, string> = {
  ethernet: 'solid',
  fiber: 'solid',
  wireless: 'dashed',
  vpn: 'dotted',
  virtual: 'dashed',
};

export function getRiskColor(score: number): string {
  if (score < 0.3) return '#4A9E5C';
  if (score < 0.6) return '#D4A843';
  if (score < 0.8) return '#D4A843';
  return '#D71921';
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
  const normalized = dateStr.endsWith('Z') || dateStr.includes('+') ? dateStr : dateStr + 'Z';
  const date = new Date(normalized);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const seconds = Math.floor(diff / 1000);
  if (seconds < 0) return 'just now';
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
    case 'critical': return '#D71921';
    case 'high': return '#D71921';
    case 'medium': return '#D4A843';
    case 'low': return '#666666';
    case 'info': return '#999999';
    default: return '#999999';
  }
}

export function getSeverityIcon(severity: string): string {
  switch (severity) {
    case 'critical': return '\u25CF';  // filled circle
    case 'high': return '\u25CF';
    case 'medium': return '\u25CB';    // open circle
    case 'low': return '\u25CB';
    case 'info': return '\u25CB';
    default: return '\u25CB';
  }
}
