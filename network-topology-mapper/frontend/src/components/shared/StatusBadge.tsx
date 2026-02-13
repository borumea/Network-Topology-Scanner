import { STATUS_COLORS } from '../../lib/graph-utils';
import type { DeviceStatus } from '../../types/topology';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

const statusIcons: Record<DeviceStatus, React.ElementType> = {
  online: CheckCircle,
  offline: XCircle,
  degraded: AlertTriangle,
};

interface Props {
  status: DeviceStatus;
  showLabel?: boolean;
  size?: number;
}

export default function StatusBadge({ status, showLabel = true, size = 12 }: Props) {
  const color = STATUS_COLORS[status] || '#6B7280';
  const Icon = statusIcons[status] || CheckCircle;

  return (
    <span className="inline-flex items-center gap-1.5">
      <Icon size={size} color={color} />
      {showLabel && (
        <span className="text-xs capitalize" style={{ color }}>
          {status}
        </span>
      )}
    </span>
  );
}
