import { useEffect, useState } from 'react';
import { Clock, Radio, Link2, AlertTriangle, FileText, Eye } from 'lucide-react';
import { useAlerts } from '../../hooks/useAlerts';
import { fetchChangelog } from '../../lib/api';
import { formatTimeAgo, getSeverityColor } from '../../lib/graph-utils';
import type { Alert } from '../../types/topology';

interface TimelineEntry {
  id: string;
  timestamp: string;
  type: 'alert' | 'scan' | 'change' | 'snapshot';
  title: string;
  description: string;
  severity?: string;
  icon: React.ElementType;
}

export default function TimelineView() {
  const { alerts } = useAlerts();
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h');

  const entries: TimelineEntry[] = alerts
    .map((a) => ({
      id: a.id,
      timestamp: a.created_at,
      type: 'alert' as const,
      title: a.title,
      description: a.description,
      severity: a.severity,
      icon: AlertTriangle,
    }))
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-text-primary">Topology Timeline</h1>
          <div className="flex rounded-lg bg-bg-secondary border border-bg-tertiary overflow-hidden">
            {(['24h', '7d', '30d'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 text-xs transition-colors ${
                  timeRange === range
                    ? 'bg-node-switch/20 text-node-switch'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        {entries.length === 0 && (
          <div className="text-center text-text-muted py-12">
            <Clock size={48} className="mx-auto mb-3 text-text-muted/30" />
            <p className="text-sm">No timeline events</p>
          </div>
        )}

        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-4 top-0 bottom-0 w-px bg-bg-tertiary" />

          <div className="space-y-0">
            {entries.map((entry) => {
              const Icon = entry.icon;
              const dotColor = entry.severity ? getSeverityColor(entry.severity) : '#6B7280';

              return (
                <div key={entry.id} className="relative flex gap-4 py-3 pl-0">
                  {/* Dot */}
                  <div
                    className="w-9 h-9 rounded-full flex items-center justify-center z-10 flex-shrink-0 bg-bg-primary border-2"
                    style={{ borderColor: dotColor }}
                  >
                    <Icon size={14} style={{ color: dotColor }} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[10px] text-text-muted">{formatTimeAgo(entry.timestamp)}</span>
                      {entry.severity && (
                        <span
                          className="text-[10px] font-bold uppercase"
                          style={{ color: getSeverityColor(entry.severity) }}
                        >
                          {entry.severity}
                        </span>
                      )}
                    </div>
                    <h4 className="text-xs font-medium text-text-primary">{entry.title}</h4>
                    {entry.description && (
                      <p className="text-[11px] text-text-secondary mt-0.5">{entry.description}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
