'use client';

/**
 * BackendStatusBanner
 *
 * Polls /health every 30 seconds. Shows a sticky amber warning banner
 * when the backend is unreachable or the database is paused/errored.
 * Disappears automatically when the backend recovers.
 */

import { useEffect, useState, useCallback } from 'react';
import { AlertTriangle, WifiOff, X, RefreshCw } from 'lucide-react';
import { API_BASE } from '@/lib/api';

type BackendStatus = 'ok' | 'backend_down' | 'db_paused' | 'db_error' | 'checking';

interface HealthResponse {
  status: string;
  database?: string;
  ai?: string;
}

const POLL_INTERVAL_MS = 30_000; // 30 seconds

export default function BackendStatusBanner() {
  const [status, setStatus] = useState<BackendStatus>('checking');
  const [dismissed, setDismissed] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const check = useCallback(async () => {
    setRetrying(true);
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      const res = await fetch(`${API_BASE}/health`, { signal: controller.signal });
      clearTimeout(timeout);

      if (!res.ok) {
        setStatus('backend_down');
        return;
      }

      const data: HealthResponse = await res.json();

      if (data.database === 'paused' || data.database === 'paused_or_unreachable') {
        setStatus('db_paused');
      } else if (data.database === 'error') {
        setStatus('db_error');
      } else {
        setStatus('ok');
        setDismissed(false); // auto-restore banner dismiss if backend comes back
      }
    } catch {
      setStatus('backend_down');
    } finally {
      setRetrying(false);
    }
  }, []);

  useEffect(() => {
    check();
    const interval = setInterval(check, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [check]);

  // Nothing to show when healthy or during first check
  if (status === 'ok' || status === 'checking') return null;
  if (dismissed) return null;

  const configs = {
    backend_down: {
      icon: <WifiOff size={15} className="shrink-0" />,
      color: 'bg-red-500/15 border-red-500/30 text-red-300',
      dot: 'bg-red-400',
      message: 'Backend is unreachable. Some features may not work.',
    },
    db_paused: {
      icon: <AlertTriangle size={15} className="shrink-0" />,
      color: 'bg-amber-500/15 border-amber-500/30 text-amber-300',
      dot: 'bg-amber-400',
      message: 'Database is paused (free-tier inactivity). Restore it at supabase.com/dashboard.',
    },
    db_error: {
      icon: <AlertTriangle size={15} className="shrink-0" />,
      color: 'bg-orange-500/15 border-orange-500/30 text-orange-300',
      dot: 'bg-orange-400',
      message: 'Database connection error. Data may not load correctly.',
    },
  };

  const cfg = configs[status];

  return (
    <div
      className={`
        fixed top-3 left-1/2 -translate-x-1/2 z-[200]
        flex items-center gap-2.5 px-4 py-2.5 rounded-xl
        border backdrop-blur-md text-xs font-medium
        shadow-xl shadow-black/30 animate-fade-in
        ${cfg.color}
      `}
      role="alert"
    >
      {/* Pulsing dot */}
      <span className="relative flex h-2 w-2 shrink-0">
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${cfg.dot}`} />
        <span className={`relative inline-flex rounded-full h-2 w-2 ${cfg.dot}`} />
      </span>

      {cfg.icon}
      <span>{cfg.message}</span>

      {/* Retry button */}
      <button
        onClick={check}
        disabled={retrying}
        title="Retry check"
        className="ml-1 p-1 rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50"
      >
        <RefreshCw size={12} className={retrying ? 'animate-spin' : ''} />
      </button>

      {/* Dismiss */}
      <button
        onClick={() => setDismissed(true)}
        title="Dismiss"
        className="p-1 rounded-lg hover:bg-white/10 transition-colors"
      >
        <X size={12} />
      </button>
    </div>
  );
}
