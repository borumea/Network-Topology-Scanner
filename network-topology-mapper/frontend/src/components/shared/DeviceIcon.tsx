import {
  Server, Router, Wifi, Shield, Monitor, Printer, Cpu, HelpCircle, Network,
} from 'lucide-react';
import type { DeviceType } from '../../types/topology';

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

  return <Icon size={size} strokeWidth={1.5} color="#1A1A1A" className={className} />;
}
