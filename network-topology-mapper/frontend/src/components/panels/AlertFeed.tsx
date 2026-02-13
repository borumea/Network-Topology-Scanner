import { useState } from 'react';
import { X, Filter, Eye, XCircle } from 'lucide-react';
import { useAlerts } from '../../hooks/useAlerts';
import { useTopologyStore } from '../../stores/topologyStore';
import { getSeverityColor, formatTimeAgo } from '../../lib/graph-utils';
import type { AlertSeverity, AlertStatus } from '../../types/topology';

const severityOrder: AlertSeverity[] = ['critical', 'high', 'medium', 'low', 'info'];

export default function AlertFeed() {
  const { alerts, loading, acknowledgeAlert, dismissAlert } = useAlerts();
  const { selectDevice, setCurrentView, setRightPanelContent } = useTopologyStore();
  const [filterSeverity, setFilterSeverity] = useState<AlertSeverity | null>(null);
  const [filterStatus, setFilterStatus] = useState<AlertStatus | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const filteredAlerts = alerts.filter((a) => {
    if (filterSeverity && a.severity !== filterSeverity) return false;
    if (filterStatus && a.status !== filterStatus) return false;
    return true;
  });

  return (
    <div className="w-[380px] h-full bg-bg-secondary border-l border-bg-tertiary flex flex-col animate-slide-in-right">
      <div className="sticky top-0 bg-bg-secondary border-b border-bg-tertiary px-4 py-3 flex items-center justify-between z-10 flex-shrink-0">
        <span className="text-sm font-semibold text-text-primary">Alerts</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`text-xs px-2 py-1 rounded transition-colors ${
              showFilters ? 'bg-node-switch/20 text-node-switch' : 'text-text-muted hover:text-text-primary'
            }`}
          >
            <Filter size={14} />
          </button>
          <button
            onClick={() => setRightPanelContent(null)}
            className="text-text-muted hover:text-text-primary transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {showFilters && (
        <div className="px-4 py-2 border-b border-bg-tertiary flex gap-2 flex-wrap flex-shrink-0">
          {severityOrder.map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(filterSeverity === sev ? null : sev)}
              className={`text-[10px] px-2 py-0.5 rounded-full capitalize transition-colors ${
                filterSeverity === sev
                  ? 'text-white'
                  : 'text-text-muted bg-bg-tertiary hover:text-text-secondary'
              }`}
              style={filterSeverity === sev ? { backgroundColor: getSeverityColor(sev) } : {}}
            >
              {sev}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="p-4 text-center text-text-muted text-xs">Loading alerts...</div>
        )}

        {!loading && filteredAlerts.length === 0 && (
          <div className="p-8 text-center text-text-muted text-sm">No alerts</div>
        )}

        {filteredAlerts.map((alert) => (
          <div
            key={alert.id}
            className="px-4 py-3 border-b border-bg-tertiary/50 hover:bg-bg-tertiary/30 transition-colors animate-fade-in"
            style={{ borderLeftWidth: 3, borderLeftColor: getSeverityColor(alert.severity) }}
          >
            <div className="flex items-center justify-between mb-1">
              <span
                className="text-[10px] font-bold uppercase"
                style={{ color: getSeverityColor(alert.severity) }}
              >
                {alert.severity}
              </span>
              <span className="text-[10px] text-text-muted">{formatTimeAgo(alert.created_at)}</span>
            </div>

            <h4 className="text-xs font-medium text-text-primary mb-0.5">{alert.title}</h4>
            {alert.description && (
              <p className="text-[11px] text-text-secondary mb-2">{alert.description}</p>
            )}

            {alert.status === 'open' && (
              <div className="flex gap-2">
                {alert.device_id && (
                  <button
                    onClick={() => {
                      selectDevice(alert.device_id!);
                      setCurrentView('topology');
                      setRightPanelContent('device');
                    }}
                    className="text-[10px] text-node-switch hover:underline flex items-center gap-1"
                  >
                    <Eye size={10} />
                    Investigate
                  </button>
                )}
                <button
                  onClick={() => acknowledgeAlert(alert.id)}
                  className="text-[10px] text-text-muted hover:text-text-primary"
                >
                  Acknowledge
                </button>
                <button
                  onClick={() => dismissAlert(alert.id)}
                  className="text-[10px] text-text-muted hover:text-risk-critical"
                >
                  Dismiss
                </button>
              </div>
            )}

            {alert.status !== 'open' && (
              <span className="text-[10px] text-text-muted capitalize">{alert.status}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
