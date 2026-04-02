import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { fetchResilienceReport } from '../../lib/api';
import { getRiskColor, getRiskLabel } from '../../lib/graph-utils';
import type { ResilienceReport as ReportType } from '../../types/topology';

export default function ResilienceReport() {
  const [report, setReport] = useState<ReportType | null>(null);
  const [loading, setLoading] = useState(false);

  const loadReport = async () => {
    setLoading(true);
    try {
      const data = await fetchResilienceReport();
      setReport(data);
    } catch (err) {
      console.error('Failed to load report:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="font-mono text-caption text-nd-text-disabled">[GENERATING REPORT...]</span>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-6">
        <div className="font-mono text-caption text-nd-text-disabled">[NO REPORT AVAILABLE]</div>
        <button
          onClick={loadReport}
          className="px-5 py-2 rounded-nd-pill bg-black text-white font-mono text-label uppercase tracking-[0.06em] hover:opacity-90 transition-opacity"
        >
          Generate Report
        </button>
      </div>
    );
  }

  const riskColor = getRiskColor(report.score / 10);
  const scoreSegments = 10;
  const scoreFilled = Math.round((report.score / report.max_score) * scoreSegments);

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-display-md font-bold text-black">Resilience</h1>
            <p className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled mt-1">
              {report.generated ? 'AI-generated' : 'Auto-generated'} assessment
            </p>
          </div>
          <button
            onClick={loadReport}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-nd-pill border border-nd-border-visible font-mono text-label uppercase tracking-[0.06em] text-nd-text-secondary hover:text-nd-text-primary hover:border-nd-text-disabled transition-colors"
          >
            <RefreshCw size={12} strokeWidth={1.5} />
            Regenerate
          </button>
        </div>

        {/* Score hero */}
        <div className="bg-nd-surface rounded-nd-card p-6 border border-nd-border">
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled mb-3">Overall Score</div>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="font-display text-display-xl font-bold" style={{ color: riskColor }}>
              {report.score}
            </span>
            <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">/ {report.max_score}</span>
            <span
              className="font-mono text-label uppercase tracking-[0.08em] ml-2"
              style={{ color: riskColor }}
            >
              {getRiskLabel(report.score / 10)} Risk
            </span>
          </div>
          {/* Segmented bar */}
          <div className="h-3 flex gap-[2px]">
            {Array.from({ length: scoreSegments }).map((_, i) => (
              <div
                key={i}
                className="flex-1 h-full"
                style={{ backgroundColor: i < scoreFilled ? riskColor : '#E8E8E8' }}
              />
            ))}
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { value: report.stats.total_devices, label: 'Devices', color: '#1A1A1A' },
            { value: report.stats.total_connections, label: 'Connections', color: '#1A1A1A' },
            { value: report.spofs.length, label: 'SPOFs', color: report.spofs.length > 0 ? '#D71921' : '#1A1A1A' },
          ].map((stat) => (
            <div key={stat.label} className="bg-nd-surface rounded-nd-compact p-4 border border-nd-border">
              <div className="font-mono text-heading font-bold" style={{ color: stat.color }}>{stat.value}</div>
              <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled mt-0.5">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Report body */}
        <div className="bg-nd-surface rounded-nd-card p-6 border border-nd-border">
          <div className="space-y-2">
            {report.report.split('\n').map((line, i) => {
              if (line.startsWith('# ')) {
                return <h2 key={i} className="font-sans text-subheading font-medium text-nd-text-display mt-4 mb-2">{line.slice(2)}</h2>;
              }
              if (line.startsWith('## ')) {
                return <h3 key={i} className="font-sans text-body font-medium text-nd-text-display mt-4 mb-2">{line.slice(3)}</h3>;
              }
              if (line.match(/^\d+\./)) {
                return <p key={i} className="text-body-sm text-nd-text-secondary mb-1 pl-4">{line}</p>;
              }
              if (line.startsWith('**') && line.endsWith('**')) {
                return <p key={i} className="text-body-sm font-medium text-nd-text-primary mt-2">{line.replace(/\*\*/g, '')}</p>;
              }
              if (line.trim() === '') {
                return <br key={i} />;
              }
              return <p key={i} className="text-body-sm text-nd-text-secondary mb-1">{line}</p>;
            })}
          </div>
        </div>

        {/* SPOFs table */}
        {report.spofs.length > 0 && (
          <div className="bg-nd-surface rounded-nd-card p-6 border border-nd-border">
            <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary mb-3">Single Points of Failure</div>
            <div className="space-y-0">
              {report.spofs.map((spof, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-nd-border last:border-0">
                  <div>
                    <span className="font-sans text-body-sm font-medium text-nd-text-primary">{spof.hostname}</span>
                    <span className="font-mono text-label uppercase text-nd-text-disabled ml-2">({spof.device_type})</span>
                  </div>
                  <span className="font-mono text-caption text-nd-accent font-bold">
                    Impact: {spof.impact}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
