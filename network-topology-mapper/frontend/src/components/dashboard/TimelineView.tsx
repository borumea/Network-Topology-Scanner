import { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { useAlerts } from '../../hooks/useAlerts';
import { formatTimeAgo, getSeverityColor } from '../../lib/graph-utils';

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
          <h1 className="font-display text-display-md font-bold text-black">Timeline</h1>
          {/* Segmented control for time range */}
          <div className="flex border border-nd-border-visible rounded-nd-pill overflow-hidden">
            {(['24h', '7d', '30d'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 font-mono text-label uppercase tracking-[0.08em] transition-colors ${
                  timeRange === range
                    ? 'bg-black text-white'
                    : 'text-nd-text-secondary hover:text-nd-text-primary'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        {entries.length === 0 && (
          <div className="text-center py-12">
            <div className="font-mono text-caption text-nd-text-disabled">[NO TIMELINE EVENTS]</div>
          </div>
        )}

        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-4 top-0 bottom-0 w-px bg-nd-border" />

          <div className="space-y-0">
            {entries.map((entry) => {
              const dotColor = entry.severity ? getSeverityColor(entry.severity) : '#999999';

              return (
                <div key={entry.id} className="relative flex gap-4 py-3 pl-0">
                  {/* Dot */}
                  <div
                    className="w-9 h-9 rounded-full flex items-center justify-center z-10 flex-shrink-0 bg-nd-black border-2"
                    style={{ borderColor: dotColor }}
                  >
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: dotColor }} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-mono text-label text-nd-text-disabled">{formatTimeAgo(entry.timestamp)}</span>
                      {entry.severity && (
                        <span
                          className="font-mono text-label uppercase tracking-[0.08em] font-bold"
                          style={{ color: getSeverityColor(entry.severity) }}
                        >
                          {entry.severity}
                        </span>
                      )}
                    </div>
                    <h4 className="font-sans text-body-sm font-medium text-nd-text-primary">{entry.title}</h4>
                    {entry.description && (
                      <p className="text-caption text-nd-text-secondary mt-0.5">{entry.description}</p>
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
