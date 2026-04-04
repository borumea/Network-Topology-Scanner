import { useEffect, useRef, useState } from 'react';
import { Play, Square, RefreshCw, Clock, ChevronDown, ChevronUp, Trash2, Terminal } from 'lucide-react';
import { fetchScans, triggerScan, cancelScan, fetchSettings, clearTopology, clearScans } from '../../lib/api';
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

  const handleClearScans = async () => {
    try {
      await clearScans();
      setScans([]);
    } catch (err) {
      console.error('Failed to clear scans:', err);
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

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed': return <span className="font-mono text-label uppercase text-nd-success">[DONE]</span>;
      case 'running': return <span className="font-mono text-label uppercase text-nd-text-primary">[RUNNING]</span>;
      case 'failed': return <span className="font-mono text-label uppercase text-nd-accent">[FAILED]</span>;
      case 'cancelled': return <span className="font-mono text-label uppercase text-nd-warning">[CANCELLED]</span>;
      default: return <span className="font-mono text-label uppercase text-nd-text-disabled">[PENDING]</span>;
    }
  };

  const segments = 20;
  const filledSegments = progress ? Math.round((progress.percent / 100) * segments) : 0;

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="font-display text-display-md font-bold text-black">Scanner</h1>

        {/* Scan My Network — primary action */}
        <div className="bg-nd-surface rounded-nd-card p-5 border border-nd-border space-y-4">
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Scan Your Network</div>

          {detectedSubnet ? (
            <div className="flex items-center gap-3 bg-nd-surface-raised rounded-nd-compact px-4 py-3">
              <div className="flex-1 min-w-0">
                <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">Detected Network</div>
                <div className="font-mono text-body-sm text-nd-text-display font-bold truncate mt-0.5">{detectedSubnet}</div>
              </div>
              <button
                onClick={() => handleStartScan(detectedSubnet)}
                className="flex items-center gap-1.5 px-5 py-2 rounded-nd-pill bg-black text-white font-mono text-label uppercase tracking-[0.06em] hover:opacity-90 transition-opacity shrink-0"
              >
                <Play size={14} strokeWidth={1.5} />
                SCAN
              </button>
            </div>
          ) : (
            <div className="font-mono text-caption text-nd-text-disabled">[DETECTING...]</div>
          )}

          {/* Intensity */}
          <div className="flex items-center gap-4">
            <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">Intensity:</span>
            <div className="flex border border-nd-border-visible rounded-nd-pill overflow-hidden">
              {(['light', 'normal', 'deep'] as const).map((level) => (
                <button
                  key={level}
                  onClick={() => setScanIntensity(level)}
                  className={`px-3 py-1 font-mono text-label uppercase tracking-[0.08em] transition-colors ${
                    scanIntensity === level
                      ? 'bg-black text-white'
                      : 'text-nd-text-secondary hover:text-nd-text-primary'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          {/* Advanced */}
          <div>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-1 font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled hover:text-nd-text-secondary transition-colors"
            >
              {showAdvanced ? <ChevronUp size={12} strokeWidth={1.5} /> : <ChevronDown size={12} strokeWidth={1.5} />}
              Custom target
            </button>
            {showAdvanced && (
              <div className="flex items-center gap-3 mt-2">
                <input
                  value={scanTarget}
                  onChange={(e) => setScanTarget(e.target.value)}
                  placeholder="e.g. 192.168.1.0/24"
                  className="flex-1 bg-transparent border-b border-nd-border-visible px-1 py-1.5 font-mono text-body-sm text-nd-text-primary outline-none focus:border-nd-text-primary transition-colors"
                />
                <button
                  onClick={() => handleStartScan()}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-nd-pill border border-nd-border-visible font-mono text-label uppercase tracking-[0.06em] text-nd-text-primary hover:border-nd-text-primary transition-colors"
                >
                  <Play size={12} strokeWidth={1.5} />
                  Scan
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Current progress */}
        {progress && (
          <div className={`bg-nd-surface rounded-nd-card p-5 space-y-3 border ${progress.percent >= 100 ? 'border-nd-success' : 'border-nd-border'}`}>
            <div className="flex items-center justify-between">
              <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-display">
                {progress.percent >= 100 ? '[SCAN COMPLETE]' : '[SCANNING...]'}
              </span>
              {progress.percent >= 100 ? (
                <button
                  onClick={() => { setProgress(null); loadScans(); }}
                  className="font-mono text-label uppercase tracking-[0.06em] text-nd-text-disabled hover:text-nd-text-primary transition-colors"
                >
                  Dismiss
                </button>
              ) : (
                <button
                  onClick={handleCancelScan}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-nd-pill border border-nd-accent font-mono text-label uppercase tracking-[0.06em] text-nd-accent hover:bg-nd-accent/10 transition-colors"
                >
                  <Square size={10} strokeWidth={1.5} />
                  Cancel
                </button>
              )}
            </div>

            <div className="flex justify-between font-mono text-caption mb-1">
              <span className="text-nd-text-secondary uppercase">{progress.phase.replace(/_/g, ' ')}</span>
              <span className="text-nd-text-disabled">{progress.percent}% &middot; {progress.devices_found} devices</span>
            </div>
            {/* Segmented progress bar */}
            <div className="h-2 flex gap-[2px]">
              {Array.from({ length: segments }).map((_, i) => (
                <div
                  key={i}
                  className="flex-1 h-full"
                  style={{ backgroundColor: i < filledSegments ? (progress.percent >= 100 ? '#4A9E5C' : '#1A1A1A') : '#E8E8E8' }}
                />
              ))}
            </div>

            {/* Live log */}
            {progress.log_messages && progress.log_messages.length > 0 && (
              <div className="mt-2">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <Terminal size={12} strokeWidth={1.5} className="text-nd-text-disabled" />
                  <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">Scan Log</span>
                </div>
                <div className="bg-nd-black rounded-nd-compact p-3 max-h-40 overflow-y-auto font-mono text-caption border border-nd-border">
                  {progress.log_messages.map((msg, i) => (
                    <div key={i} className="text-nd-text-secondary py-0.5">
                      <span className="text-nd-text-disabled select-none">&gt; </span>{msg}
                    </div>
                  ))}
                  <div ref={logEndRef} />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Scheduled scans */}
        <div className="bg-nd-surface rounded-nd-card p-5 border border-nd-border">
          <div className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary mb-3">Scheduled Scans</div>
          <div className="space-y-2">
            {[
              { label: 'Full scan', value: 'Every 6 hours' },
              { label: 'Passive capture', value: 'Continuous', active: true },
              { label: 'SNMP poll', value: 'Every 30 min' },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between py-1 border-b border-nd-border last:border-0">
                <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-disabled">{item.label}</span>
                <span className={`font-mono text-caption ${item.active ? 'text-nd-success' : 'text-nd-text-secondary'}`}>
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Scan history */}
        <div className="bg-nd-surface rounded-nd-card p-5 border border-nd-border">
          <div className="flex items-center justify-between mb-3">
            <span className="font-mono text-label uppercase tracking-[0.08em] text-nd-text-secondary">Recent Scans</span>
            <div className="flex items-center gap-2">
              {scans.length > 0 && (
                <button
                  onClick={handleClearScans}
                  className="flex items-center gap-1 font-mono text-label uppercase tracking-[0.06em] text-nd-text-disabled hover:text-nd-accent transition-colors"
                >
                  <Trash2 size={12} strokeWidth={1.5} />
                  Clear
                </button>
              )}
              <button onClick={loadScans} className="text-nd-text-disabled hover:text-nd-text-primary transition-colors">
                <RefreshCw size={14} strokeWidth={1.5} />
              </button>
            </div>
          </div>

          {loading && <div className="font-mono text-caption text-nd-text-disabled">[LOADING...]</div>}

          <div className="space-y-1">
            {scans.map((scan) => (
              <div key={scan.id} className="flex items-center gap-3 py-2 border-b border-nd-border last:border-0">
                {getStatusLabel(scan.status)}
                <div className="flex-1">
                  <div className="font-mono text-caption text-nd-text-primary uppercase">{scan.scan_type} scan</div>
                  <div className="font-mono text-label text-nd-text-disabled">{scan.target_range}</div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-caption text-nd-text-secondary">{scan.devices_found} devices</div>
                  <div className="font-mono text-label text-nd-text-disabled">{formatTimeAgo(scan.started_at || '')}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Clear database */}
        <div className="bg-nd-surface rounded-nd-card p-5 border border-nd-accent/30">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-sans text-body-sm font-medium text-nd-text-primary">Clear Device Database</div>
              <div className="font-mono text-label uppercase tracking-[0.06em] text-nd-text-disabled mt-0.5">Remove all discovered data</div>
            </div>
            {!showClearConfirm ? (
              <button
                onClick={() => setShowClearConfirm(true)}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-nd-pill border border-nd-accent font-mono text-label uppercase tracking-[0.06em] text-nd-accent hover:bg-nd-accent/10 transition-colors"
              >
                <Trash2 size={12} strokeWidth={1.5} />
                Clear All
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <span className="font-mono text-caption text-nd-accent">Are you sure?</span>
                <button
                  onClick={handleClearDatabase}
                  className="px-3 py-1.5 rounded-nd-pill bg-nd-accent text-white font-mono text-label uppercase tracking-[0.06em] hover:opacity-90 transition-opacity"
                >
                  Yes
                </button>
                <button
                  onClick={() => setShowClearConfirm(false)}
                  className="px-3 py-1.5 rounded-nd-pill border border-nd-border-visible font-mono text-label uppercase tracking-[0.06em] text-nd-text-secondary hover:text-nd-text-primary transition-colors"
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
