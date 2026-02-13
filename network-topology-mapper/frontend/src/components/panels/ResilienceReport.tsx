import { useEffect, useState } from 'react';
import { FileText, RefreshCw, Download } from 'lucide-react';
import { fetchResilienceReport } from '../../lib/api';
import { getRiskColor, getRiskLabel } from '../../lib/graph-utils';
import type { ResilienceReport as ReportType } from '../../types/topology';
import RiskScore from '../shared/RiskScore';

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
      <div className="flex items-center justify-center h-full text-text-muted">
        <RefreshCw size={20} className="animate-spin mr-2" />
        Generating report...
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-text-muted gap-4">
        <FileText size={48} className="text-text-muted/30" />
        <p className="text-sm">No report available</p>
        <button
          onClick={loadReport}
          className="px-4 py-2 rounded-lg bg-node-switch text-white text-sm hover:bg-node-switch/90 transition-colors"
        >
          Generate Report
        </button>
      </div>
    );
  }

  const riskColor = getRiskColor(report.score / 10);

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-text-primary">Network Resilience Assessment</h1>
            <p className="text-xs text-text-muted mt-1">
              {report.generated ? 'AI-generated' : 'Auto-generated'} report
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={loadReport}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-bg-secondary border border-bg-tertiary text-xs text-text-secondary hover:text-text-primary transition-colors"
            >
              <RefreshCw size={12} />
              Regenerate
            </button>
          </div>
        </div>

        {/* Score */}
        <div className="bg-bg-secondary rounded-xl p-6 border border-bg-tertiary">
          <div className="text-sm text-text-muted mb-3">Overall Score</div>
          <div className="flex items-end gap-3 mb-3">
            <span className="text-4xl font-bold" style={{ color: riskColor }}>
              {report.score}
            </span>
            <span className="text-text-muted text-lg mb-1">/ {report.max_score}</span>
            <span
              className="text-sm font-medium mb-1.5 ml-2"
              style={{ color: riskColor }}
            >
              ({getRiskLabel(report.score / 10)} Risk)
            </span>
          </div>
          <div className="h-3 bg-bg-tertiary rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${(report.score / report.max_score) * 100}%`,
                backgroundColor: riskColor,
              }}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-bg-secondary rounded-lg p-4 border border-bg-tertiary">
            <div className="text-2xl font-bold text-text-primary">{report.stats.total_devices}</div>
            <div className="text-xs text-text-muted">Devices</div>
          </div>
          <div className="bg-bg-secondary rounded-lg p-4 border border-bg-tertiary">
            <div className="text-2xl font-bold text-text-primary">{report.stats.total_connections}</div>
            <div className="text-xs text-text-muted">Connections</div>
          </div>
          <div className="bg-bg-secondary rounded-lg p-4 border border-bg-tertiary">
            <div className="text-2xl font-bold text-risk-critical">{report.spofs.length}</div>
            <div className="text-xs text-text-muted">SPOFs</div>
          </div>
        </div>

        {/* Report body */}
        <div className="bg-bg-secondary rounded-xl p-6 border border-bg-tertiary">
          <div className="prose prose-invert prose-sm max-w-none">
            {report.report.split('\n').map((line, i) => {
              if (line.startsWith('# ')) {
                return <h2 key={i} className="text-lg font-bold text-text-primary mt-4 mb-2">{line.slice(2)}</h2>;
              }
              if (line.startsWith('## ')) {
                return <h3 key={i} className="text-base font-semibold text-text-primary mt-4 mb-2">{line.slice(3)}</h3>;
              }
              if (line.match(/^\d+\./)) {
                return <p key={i} className="text-sm text-text-secondary mb-1 pl-4">{line}</p>;
              }
              if (line.startsWith('**') && line.endsWith('**')) {
                return <p key={i} className="text-sm font-semibold text-text-primary mt-2">{line.replace(/\*\*/g, '')}</p>;
              }
              if (line.trim() === '') {
                return <br key={i} />;
              }
              return <p key={i} className="text-sm text-text-secondary mb-1">{line}</p>;
            })}
          </div>
        </div>

        {/* SPOFs table */}
        {report.spofs.length > 0 && (
          <div className="bg-bg-secondary rounded-xl p-6 border border-bg-tertiary">
            <h3 className="text-sm font-semibold text-text-primary mb-3">Single Points of Failure</h3>
            <div className="space-y-2">
              {report.spofs.map((spof, i) => (
                <div key={i} className="flex items-center justify-between bg-bg-tertiary rounded-lg px-3 py-2">
                  <div>
                    <span className="text-xs font-medium text-text-primary">{spof.hostname}</span>
                    <span className="text-[10px] text-text-muted ml-2 capitalize">({spof.device_type})</span>
                  </div>
                  <span className="text-xs text-risk-critical">
                    Impact: {spof.impact} devices
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
