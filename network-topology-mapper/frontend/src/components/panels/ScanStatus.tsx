import { useEffect, useRef, useState } from 'react';
import { Play, Square, RefreshCw, Clock, CheckCircle, XCircle, AlertTriangle, Wifi, ChevronDown, ChevronUp, Trash2, Terminal } from 'lucide-react';
import { fetchScans, triggerScan, cancelScan, fetchSettings, clearTopology } from '../../lib/api';
import { formatTimeAgo } from '../../lib/graph-utils';
import type { Scan, ScanProgress } from '../../types/topology';

export default function ScanStatus() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(false);
  const [detectedSubnet, setDetectedSubnet] = useState('');
  const [scanTarget, setScanTarget] = useState('');
  const [scanIntensity, setScanIntensity] = useState<'light' | 'normal' | 'deep'>('normal');
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

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

  const loadSettings = async () => {
    try {
      const data = await fetchSettings();
      const subnet = data?.settings?.scan_default_range || '';
      setDetectedSubnet(subnet);
      setScanTarget(subnet);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  useEffect(() => {
    loadScans();
    loadSettings();

    const handler = (e: Event) => {
      const p = (e as CustomEvent).detail as ScanProgress;
      setProgress(p);
      if (p.percent >= 100) {
        setTimeout(loadScans, 1000);
      }
    };
    window.addEventListener('ws-scan-progress', handler as EventListener);
    return () => window.removeEventListener('ws-scan-progress', handler as EventListener);
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [progress?.log_messages?.length]);

  const handleCancelScan = async () => {
    if (!progress?.scan_id) return;
    try {
      await cancelScan(progress.scan_id);
      setProgress(null);
      setTimeout(loadScans, 1000);
    } catch (err) {
      console.error('Failed to cancel scan:', err);
    }
  };

  const handleClearDatabase = async () => {
    try {
      await clearTopology();
      setShowClearConfirm(false);
      window.location.reload();
    } catch (err) {
      console.error('Failed to clear database:', err);
    }
  };

  const handleStartScan = async (target?: string) => {
    try {
      await triggerScan('full', target ?? scanTarget, scanIntensity);
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

  const friendlySubnet = detectedSubnet
    ? detectedSubnet.replace('/24', ' network').replace('/16', ' network')
    : '';

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-xl font-bold text-text-primary">Network Scanner</h1>

        {/* Scan My Network — primary action */}
        <div className="bg-bg-secondary rounded-xl p-5 border border-bg-tertiary space-y-4">
          <div className="text-sm font-semibold text-text-primary">Scan Your Network</div>

          {detectedSubnet ? (
            <div className="flex items-center gap-3 bg-bg-tertiary/50 rounded-lg px-4 py-3">
              <Wifi size={18} className="text-node-switch shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-xs text-text-secondary">Detected network</div>
                <div className="text-sm text-text-primary font-medium truncate">{detectedSubnet}</div>
              </div>
              <button
                onClick={() => handleStartScan(detectedSubnet)}
                className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-node-switch text-white text-sm font-medium hover:bg-node-switch/90 transition-colors shrink-0"
              >
                <Play size={14} />
                Scan My Network
              </button>
            </div>
          ) : (
            <div className="text-xs text-text-muted">Detecting your network...</div>
          )}

          {/* Intensity */}
          <div className="flex items-center gap-4">
            <label className="text-xs text-text-muted">Scan intensity:</label>
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

          {/* Advanced — manual target entry */}
          <div>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-1 text-xs text-text-muted hover:text-text-secondary transition-colors"
            >
              {showAdvanced ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              Advanced: scan a different network
            </button>
            {showAdvanced && (
              <div className="flex items-center gap-3 mt-2">
                <input
                  value={scanTarget}
                  onChange={(e) => setScanTarget(e.target.value)}
                  placeholder="e.g. 192.168.1.0/24"
                  className="flex-1 bg-bg-tertiary border border-bg-tertiary rounded-lg px-3 py-1.5 text-xs text-text-primary outline-none focus:border-node-switch transition-colors"
                />
                <button
                  onClick={() => handleStartScan()}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-bg-tertiary text-text-primary text-xs font-medium hover:bg-bg-tertiary/70 border border-bg-tertiary transition-colors"
                >
                  <Play size={12} />
                  Scan
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Current progress */}
        {progress && (
          <div className={`bg-bg-secondary rounded-xl p-5 space-y-3 border ${progress.percent >= 100 ? 'border-status-online/30' : 'border-node-switch/30'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {progress.percent >= 100 ? (
                  <>
                    <CheckCircle size={14} className="text-status-online" />
                    <span className="text-sm font-semibold text-text-primary">Scan Complete</span>
                  </>
                ) : (
                  <>
                    <RefreshCw size={14} className="text-node-switch animate-spin" />
                    <span className="text-sm font-semibold text-text-primary">Scan In Progress</span>
                  </>
                )}
              </div>
              {progress.percent >= 100 ? (
                <button
                  onClick={() => { setProgress(null); loadScans(); }}
                  className="text-xs text-text-muted hover:text-text-primary transition-colors"
                >
                  Dismiss
                </button>
              ) : (
                <button
                  onClick={handleCancelScan}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-risk-critical border border-risk-critical/30 text-xs font-medium hover:bg-risk-critical/10 transition-colors"
                >
                  <Square size={10} />
                  Cancel
                </button>
              )}
            </div>

            <div className="flex justify-between text-xs mb-1">
              <span className="text-text-secondary capitalize">{progress.phase.replace(/_/g, ' ')}</span>
              <span className="text-text-muted">{progress.percent}% &middot; {progress.devices_found} devices</span>
            </div>
            <div className="h-2 bg-bg-tertiary rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${progress.percent >= 100 ? 'bg-status-online' : 'bg-node-switch'}`}
                style={{ width: `${progress.percent}%` }}
              />
            </div>

            {/* Live log */}
            {progress.log_messages && progress.log_messages.length > 0 && (
              <div className="mt-2">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <Terminal size={12} className="text-text-muted" />
                  <span className="text-xs text-text-muted">Scan log</span>
                </div>
                <div className="bg-bg-primary rounded-lg p-3 max-h-40 overflow-y-auto font-mono text-xs border border-bg-tertiary">
                  {progress.log_messages.map((msg, i) => (
                    <div key={i} className="text-text-secondary py-0.5">
                      <span className="text-text-muted select-none">&gt; </span>{msg}
                    </div>
                  ))}
                  <div ref={logEndRef} />
                </div>
              </div>
            )}
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

        {/* Clear database */}
        <div className="bg-bg-secondary rounded-xl p-5 border border-risk-critical/20">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-text-primary">Clear Device Database</div>
              <div className="text-xs text-text-muted mt-0.5">Remove all discovered devices, connections, and dependencies.</div>
            </div>
            {!showClearConfirm ? (
              <button
                onClick={() => setShowClearConfirm(true)}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-risk-critical border border-risk-critical/30 text-xs font-medium hover:bg-risk-critical/10 transition-colors"
              >
                <Trash2 size={12} />
                Clear All
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-xs text-risk-critical">Are you sure?</span>
                <button
                  onClick={handleClearDatabase}
                  className="px-3 py-1.5 rounded-lg bg-risk-critical text-white text-xs font-medium hover:bg-risk-critical/90 transition-colors"
                >
                  Yes, clear everything
                </button>
                <button
                  onClick={() => setShowClearConfirm(false)}
                  className="px-3 py-1.5 rounded-lg bg-bg-tertiary text-text-secondary text-xs font-medium hover:bg-bg-tertiary/70 transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
