import { useState } from 'react';
import { X, Filter, Eye } from 'lucide-react';
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
    <div className="w-[380px] flex-shrink-0 h-full bg-nd-surface border-l border-nd-border flex flex-col animate-fade-in">
      {/* Header */}
      <div className="sticky top-0 bg-nd-surface border-b border-nd-border px-4 py-3 flex items-center justify-between z-10 flex-shrink-0">
        <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Alerts</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-1 rounded-nd-technical transition-colors ${
              showFilters ? 'bg-nd-surface-raised text-nd-text-display' : 'text-nd-text-disabled hover:text-nd-text-primary'
            }`}
          >
            <Filter size={14} strokeWidth={1.5} />
          </button>
          <button
            onClick={() => setRightPanelContent(null)}
            className="text-nd-text-disabled hover:text-nd-text-primary transition-colors"
          >
            <X size={16} strokeWidth={1.5} />
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="px-4 py-2 border-b border-nd-border flex gap-1.5 flex-wrap flex-shrink-0">
          {severityOrder.map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(filterSeverity === sev ? null : sev)}
              className={`font-mono text-label uppercase tracking-[0.06em] px-2 py-0.5 rounded-nd-pill border transition-colors ${
                filterSeverity === sev
                  ? 'border-current text-white'
                  : 'border-nd-border-visible text-nd-text-disabled hover:text-nd-text-secondary'
              }`}
              style={filterSeverity === sev ? { backgroundColor: getSeverityColor(sev), borderColor: getSeverityColor(sev) } : {}}
            >
              {sev}
            </button>
          ))}
        </div>
      )}

      {/* Alert list */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="p-4 text-center font-mono text-caption text-nd-text-disabled">[LOADING...]</div>
        )}

        {!loading && filteredAlerts.length === 0 && (
          <div className="p-8 text-center">
            <div className="font-mono text-caption text-nd-text-disabled">[NO ALERTS]</div>
          </div>
        )}

        {filteredAlerts.map((alert) => (
          <div
            key={alert.id}
            className="px-4 py-3 border-b border-nd-border hover:bg-nd-surface-raised transition-colors animate-fade-in"
            style={{ borderLeftWidth: 2, borderLeftColor: getSeverityColor(alert.severity) }}
          >
            <div className="flex items-center justify-between mb-1">
              <span
                className="font-mono text-label uppercase tracking-[0.08em] font-bold"
                style={{ color: getSeverityColor(alert.severity) }}
              >
                {alert.severity}
              </span>
              <span className="font-mono text-label text-nd-text-disabled">{formatTimeAgo(alert.created_at)}</span>
            </div>

            <h4 className="text-body-sm font-sans font-medium text-nd-text-primary mb-0.5">{alert.title}</h4>
            {alert.description && (
              <p className="text-caption text-nd-text-secondary mb-2">{alert.description}</p>
            )}

            {alert.status === 'open' && (
              <div className="flex gap-3">
                {alert.device_id && (
                  <button
                    onClick={() => {
                      selectDevice(alert.device_id!);
                      setCurrentView('topology');
                      setRightPanelContent('device');
                    }}
                    className="font-mono text-label uppercase tracking-[0.06em] text-nd-interactive hover:underline flex items-center gap-1"
                  >
                    <Eye size={10} strokeWidth={1.5} />
                    Investigate
                  </button>
                )}
                <button
                  onClick={() => acknowledgeAlert(alert.id)}
                  className="font-mono text-label uppercase tracking-[0.06em] text-nd-text-disabled hover:text-nd-text-primary"
                >
                  Acknowledge
                </button>
                <button
                  onClick={() => dismissAlert(alert.id)}
                  className="font-mono text-label uppercase tracking-[0.06em] text-nd-text-disabled hover:text-nd-accent"
                >
                  Dismiss
                </button>
              </div>
            )}

            {alert.status !== 'open' && (
              <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">[{alert.status}]</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
