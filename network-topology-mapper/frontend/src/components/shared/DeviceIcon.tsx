import {
  Server, Router, Wifi, Shield, Monitor, Printer, Cpu, HelpCircle, Network,
} from 'lucide-react';
import type { DeviceType } from '../../types/topology';
import { DEVICE_TYPE_COLORS } from '../../lib/graph-utils';

const iconMap: Record<DeviceType, React.ElementType> = {
  router: Router,
  switch: Network,
  server: Server,
  firewall: Shield,
  ap: Wifi,
  workstation: Monitor,
  printer: Printer,
  iot: Cpu,
  unknown: HelpCircle,
};

interface Props {
  type: DeviceType;
  size?: number;
  className?: string;
}

export default function DeviceIcon({ type, size = 18, className = '' }: Props) {
  const Icon = iconMap[type] || HelpCircle;
  const color = DEVICE_TYPE_COLORS[type] || '#6B7280';

  return <Icon size={size} color={color} className={className} />;
}
