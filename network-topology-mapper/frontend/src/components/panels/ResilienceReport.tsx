import { useEffect, useState } from 'react';
import { RefreshCw, Sparkles, FileText } from 'lucide-react';
import { fetchResilienceReport } from '../../lib/api';
import { getRiskColor, getRiskLabel } from '../../lib/graph-utils';
import type { ResilienceReport as ReportType } from '../../types/topology';

function renderInlineFormatting(text: string) {
  // Split on **bold** and *italic* patterns
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  if (parts.length === 1) return text;
  return parts.map((part, j) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={j} className="font-medium text-nd-text-primary">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={j} className="italic text-nd-text-secondary">{part.slice(1, -1)}</em>;
    }
    return <span key={j}>{part}</span>;
  });
}

function parseTableRow(line: string): string[] {
  return line.split('|').slice(1, -1).map(cell => cell.trim());
}

function isTableSeparator(line: string): boolean {
  return /^\|[\s\-:|]+\|$/.test(line.trim());
}

function renderTable(lines: string[], startKey: number) {
  const header = parseTableRow(lines[0]);
  const dataRows = lines.slice(2).map(l => parseTableRow(l));

  return (
    <div key={startKey} className="overflow-x-auto my-3">
      <table className="w-full text-body-sm border border-nd-border">
        <thead>
          <tr className="border-b border-nd-border bg-nd-bg">
            {header.map((cell, j) => (
              <th key={j} className="px-3 py-2 text-left font-mono text-label uppercase tracking-[0.06em] text-nd-text-secondary">
                {renderInlineFormatting(cell)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dataRows.map((row, ri) => (
            <tr key={ri} className="border-b border-nd-border last:border-0">
              {row.map((cell, ci) => (
                <td key={ci} className="px-3 py-2 text-nd-text-secondary">
                  {renderInlineFormatting(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderMarkdownBody(text: string) {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Detect table: line starts with |, next line is separator
    if (line.trim().startsWith('|') && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const tableLines = [line];
      let j = i + 1;
      while (j < lines.length && lines[j].trim().startsWith('|')) {
        tableLines.push(lines[j]);
        j++;
      }
      elements.push(renderTable(tableLines, i));
      i = j;
      continue;
    }

    // Skip standalone separator lines (e.g. ---)
    if (/^-{3,}$/.test(line.trim())) {
      elements.push(<hr key={i} className="border-nd-border my-4" />);
      i++;
      continue;
    }

    if (line.startsWith('### ')) {
      elements.push(<h4 key={i} className="font-sans text-body-sm font-semibold text-nd-text-display mt-4 mb-1 uppercase tracking-wide">{line.slice(4)}</h4>);
    } else if (line.startsWith('## ')) {
      elements.push(<h3 key={i} className="font-sans text-body font-medium text-nd-text-display mt-4 mb-2">{line.slice(3)}</h3>);
    } else if (line.startsWith('# ')) {
      elements.push(<h2 key={i} className="font-sans text-subheading font-medium text-nd-text-display mt-4 mb-2">{line.slice(2)}</h2>);
    } else if (line.match(/^\d+\./)) {
      // Split off "Impact:" or "Estimated impact:" onto its own line
      const impactMatch = line.match(/^(.+?)\s*\*?(Estimated\s+)?[Ii]mpact:\s*(.+?)\*?$/);
      if (impactMatch) {
        const mainText = impactMatch[1].replace(/\.\s*$/, '.');
        const impactText = ((impactMatch[2] || '') + 'Impact: ' + impactMatch[3]).replace(/\*+/g, '');
        elements.push(
          <div key={i} className="mb-3 pl-4">
            <p className="text-body-sm text-nd-text-secondary">{renderInlineFormatting(mainText)}</p>
            <p className="text-body-sm text-nd-text-disabled italic mt-1 pl-2 border-l-2 border-nd-border">{impactText}</p>
          </div>
        );
      } else {
        elements.push(<p key={i} className="text-body-sm text-nd-text-secondary mb-1 pl-4">{renderInlineFormatting(line)}</p>);
      }
    } else if (line.startsWith('- ')) {
      elements.push(<p key={i} className="text-body-sm text-nd-text-secondary mb-1 pl-4">&#8226; {renderInlineFormatting(line.slice(2))}</p>);
    } else if (line.startsWith('**') && line.endsWith('**')) {
      elements.push(<p key={i} className="text-body-sm font-medium text-nd-text-primary mt-2">{line.replace(/\*\*/g, '')}</p>);
    } else if (line.trim() === '') {
      elements.push(<br key={i} />);
    } else {
      elements.push(<p key={i} className="text-body-sm text-nd-text-secondary mb-1">{renderInlineFormatting(line)}</p>);
    }
    i++;
  }

  return elements;
}

let cachedReport: ReportType | null = null;

export default function ResilienceReport() {
  const [report, setReport] = useState<ReportType | null>(cachedReport);
  const [loading, setLoading] = useState(false);

  const loadReport = async () => {
    setLoading(true);
    try {
      const data = await fetchResilienceReport();
      cachedReport = data;
      setReport(data);
    } catch (err) {
      console.error('Failed to load report:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!cachedReport) {
      loadReport();
    }
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <RefreshCw size={16} strokeWidth={1.5} className="animate-spin text-nd-text-disabled" />
        <span className="font-mono text-caption text-nd-text-disabled">[GENERATING REPORT...]</span>
        <span className="font-mono text-caption text-nd-text-disabled opacity-60">This may take a moment</span>
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
            <div className="flex items-center gap-2 mt-1.5">
              {report.generated ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-nd-pill bg-black text-white font-mono text-label uppercase tracking-[0.06em]">
                  <Sparkles size={10} strokeWidth={1.5} />
                  AI Report
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-nd-pill border border-nd-border-visible font-mono text-label uppercase tracking-[0.06em] text-nd-text-secondary">
                  <FileText size={10} strokeWidth={1.5} />
                  Template
                </span>
              )}
            </div>
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
            {renderMarkdownBody(report.report)}
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
