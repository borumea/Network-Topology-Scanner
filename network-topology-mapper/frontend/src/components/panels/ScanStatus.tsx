import { useEffect, useState } from 'react';
import { Play, Pause, RefreshCw, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { fetchScans, triggerScan, cancelScan } from '../../lib/api';
import { formatTimeAgo } from '../../lib/graph-utils';
import type { Scan, ScanProgress } from '../../types/topology';

export default function ScanStatus() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(false);
  const [scanTarget, setScanTarget] = useState('192.168.0.0/16');
  const [scanIntensity, setScanIntensity] = useState<'light' | 'normal' | 'deep'>('normal');
  const [progress, setProgress] = useState<ScanProgress | null>(null);

  const loadScans = async () => {
    setLoading(true);
    try {
      const data = await fetchScans();
      setScans(data.scans || []);
    } catch (err) {
      console.error('Failed to load scans:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScans();

    const handler = (e: Event) => {
      setProgress((e as CustomEvent).detail as ScanProgress);
    };
    window.addEventListener('ws-scan-progress', handler as EventListener);
    return () => window.removeEventListener('ws-scan-progress', handler as EventListener);
  }, []);

  const handleStartScan = async () => {
    try {
      await triggerScan('full', scanTarget, scanIntensity);
      setTimeout(loadScans, 2000);
    } catch (err) {
      console.error('Failed to start scan:', err);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle size={14} className="text-status-online" />;
      case 'running': return <RefreshCw size={14} className="text-node-switch animate-spin" />;
      case 'failed': return <XCircle size={14} className="text-risk-critical" />;
      case 'cancelled': return <AlertTriangle size={14} className="text-risk-medium" />;
      default: return <Clock size={14} className="text-text-muted" />;
    }
  };

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-xl font-bold text-text-primary">Network Scanner</h1>

        {/* Quick scan */}
        <div className="bg-bg-secondary rounded-xl p-5 border border-bg-tertiary space-y-4">
          <div className="text-sm font-semibold text-text-primary">Quick Scan</div>

          <div className="flex items-center gap-3">
            <label className="text-xs text-text-muted">Target:</label>
            <input
              value={scanTarget}
              onChange={(e) => setScanTarget(e.target.value)}
              className="flex-1 bg-bg-tertiary border border-bg-tertiary rounded-lg px-3 py-1.5 text-xs text-text-primary outline-none focus:border-node-switch transition-colors"
            />
            <button
              onClick={handleStartScan}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-node-switch text-white text-xs font-medium hover:bg-node-switch/90 transition-colors"
            >
              <Play size={12} />
              Scan
            </button>
          </div>

          <div className="flex items-center gap-4">
            <label className="text-xs text-text-muted">Intensity:</label>
            {(['light', 'normal', 'deep'] as const).map((level) => (
              <label key={level} className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  checked={scanIntensity === level}
                  onChange={() => setScanIntensity(level)}
                  className="accent-node-switch"
                />
                <span className="text-xs text-text-secondary capitalize">{level}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Current progress */}
        {progress && progress.percent < 100 && (
          <div className="bg-bg-secondary rounded-xl p-5 border border-bg-tertiary">
            <div className="text-sm font-semibold text-text-primary mb-3">Current Scan</div>
            <div className="flex justify-between text-xs mb-1.5">
              <span className="text-text-secondary capitalize">{progress.phase.replace(/_/g, ' ')}</span>
              <span className="text-text-muted">{progress.percent}%</span>
            </div>
            <div className="h-2 bg-bg-tertiary rounded-full overflow-hidden">
              <div
                className="h-full bg-node-switch rounded-full transition-all duration-300"
                style={{ width: `${progress.percent}%` }}
              />
            </div>
            <div className="text-xs text-text-muted mt-1.5">
              {progress.devices_found} devices found
            </div>
          </div>
        )}

        {/* Scheduled scans */}
        <div className="bg-bg-secondary rounded-xl p-5 border border-bg-tertiary">
          <div className="text-sm font-semibold text-text-primary mb-3">Scheduled Scans</div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-text-primary">Full scan</span>
              <span className="text-text-muted">Every 6 hours</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-text-primary">Passive capture</span>
              <span className="text-status-online">Continuous</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-text-primary">SNMP poll</span>
              <span className="text-text-muted">Every 30 min</span>
            </div>
          </div>
        </div>

        {/* Scan history */}
        <div className="bg-bg-secondary rounded-xl p-5 border border-bg-tertiary">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-semibold text-text-primary">Recent Scans</div>
            <button onClick={loadScans} className="text-text-muted hover:text-text-primary transition-colors">
              <RefreshCw size={14} />
            </button>
          </div>

          {loading && <div className="text-xs text-text-muted">Loading...</div>}

          <div className="space-y-2">
            {scans.map((scan) => (
              <div key={scan.id} className="flex items-center gap-3 text-xs bg-bg-tertiary/50 rounded-lg px-3 py-2">
                {getStatusIcon(scan.status)}
                <div className="flex-1">
                  <div className="text-text-primary capitalize">{scan.scan_type} scan</div>
                  <div className="text-text-muted">{scan.target_range}</div>
                </div>
                <div className="text-right">
                  <div className="text-text-secondary">{scan.devices_found} devices</div>
                  <div className="text-text-muted">{formatTimeAgo(scan.started_at || '')}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
