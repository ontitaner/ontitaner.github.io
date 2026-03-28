import { useState, useEffect, useRef } from 'react';
import { useSyncContext } from '@/lib/SyncContext';

function IconCloud({ size = 16 }: { size?: number }) {
  const s = { display: 'inline-block', verticalAlign: 'middle', fill: 'none', stroke: 'currentColor' } as const;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={s} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 10h-1.26A8 8 0 109 20h9a5 5 0 000-10z" />
    </svg>
  );
}

function IconCheck({ size = 14 }: { size?: number }) {
  const s = { display: 'inline-block', verticalAlign: 'middle', fill: 'none', stroke: 'currentColor' } as const;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={s} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function IconLogout({ size = 14 }: { size?: number }) {
  const s = { display: 'inline-block', verticalAlign: 'middle', fill: 'none', stroke: 'currentColor' } as const;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={s} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

export default function SyncButton() {
  const { token, status, login, logout, triggerSync } = useSyncContext();
  const [showPanel, setShowPanel] = useState(false);
  const [inputToken, setInputToken] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  // Auto-close panel after 4s when connected
  useEffect(() => {
    if (showPanel && token) {
      const timer = setTimeout(() => setShowPanel(false), 4000);
      return () => clearTimeout(timer);
    }
  }, [showPanel, token]);

  // Close on click outside
  useEffect(() => {
    if (!showPanel) return;
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setShowPanel(false);
      }
    };
    setTimeout(() => document.addEventListener('mousedown', handler), 0);
    return () => document.removeEventListener('mousedown', handler);
  }, [showPanel]);

  const handleLogin = async () => {
    if (!inputToken.trim()) return;
    setLoading(true);
    setError('');
    const ok = await login(inputToken.trim());
    setLoading(false);
    if (ok) {
      setInputToken('');
      setShowPanel(false);
    } else {
      setError('Token 无效，请检查权限（需要 gist scope）');
    }
  };

  const statusLabel = {
    idle: '未连接',
    syncing: '同步中...',
    synced: '已同步',
    error: '同步失败',
    offline: '离线',
  }[status];

  const statusColor = {
    idle: 'var(--text-muted)',
    syncing: 'var(--accent)',
    synced: '#3fb950',
    error: '#f85149',
    offline: 'var(--text-muted)',
  }[status];

  return (
    <div className="sync-wrap">
      <button className="sync-btn" onClick={() => setShowPanel(!showPanel)}>
        <IconCloud size={15} />
        <span className="sync-dot" style={{ background: statusColor }} />
      </button>

      {showPanel && (
        <div className="sync-panel" ref={panelRef}>
          {token ? (
            <>
              <div className="sync-status">
                <IconCheck size={14} />
                <span>已连接 GitHub Gist</span>
              </div>
              <div className="sync-status-line">
                <span className="sync-dot-inline" style={{ background: statusColor }} />
                <span>{statusLabel}</span>
              </div>
              <div className="sync-actions">
                <button className="anno-save" onClick={triggerSync}>立即同步</button>
                <button className="sync-logout" onClick={() => { logout(); setShowPanel(false); }}>
                  <IconLogout size={13} /> 断开
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="sync-title">连接 GitHub Gist</div>
              <p className="sync-desc">
                输入 GitHub Personal Access Token（需要 gist 权限）实现跨设备同步批注和标签。
              </p>
              <input
                type="password"
                placeholder="ghp_xxxxxxxxxxxx"
                value={inputToken}
                onChange={e => setInputToken(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleLogin(); }}
                className="sync-input"
              />
              {error && <div className="sync-error">{error}</div>}
              <button className="anno-save" style={{ width: '100%' }} onClick={handleLogin} disabled={loading}>
                {loading ? '验证中...' : '连接'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
