import { createContext, useContext, useState, useCallback, useEffect, useRef, ReactNode } from 'react';
import { getToken, setToken as saveToken, clearToken, pullData, pushData, validateToken, SyncData } from './gistSync';

type SyncStatus = 'idle' | 'syncing' | 'synced' | 'error' | 'offline';

interface SyncContextType {
  token: string | null;
  status: SyncStatus;
  login: (token: string) => Promise<boolean>;
  logout: () => void;
  triggerSync: () => void;
}

const SyncContext = createContext<SyncContextType>(null!);
export const useSyncContext = () => useContext(SyncContext);

// Keys for local data (shared with Tag/Annotation contexts)
const ANNO_KEY = 'doc-annotations-v2';
const TAG_KEY = 'doc-user-tags';

function getLocalData(): SyncData {
  const annotations = JSON.parse(localStorage.getItem(ANNO_KEY) || '[]');
  const tags = JSON.parse(localStorage.getItem(TAG_KEY) || '{}');
  return { annotations, tags, updatedAt: Date.now() };
}

function setLocalData(data: SyncData) {
  localStorage.setItem(ANNO_KEY, JSON.stringify(data.annotations));
  localStorage.setItem(TAG_KEY, JSON.stringify(data.tags));
}

export function SyncProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [status, setStatus] = useState<SyncStatus>('idle');
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // Load token on mount
  useEffect(() => {
    const t = getToken();
    if (t) setTokenState(t);
  }, []);

  const doSync = useCallback(async (t: string) => {
    setStatus('syncing');
    try {
      // Pull remote
      const remote = await pullData(t);
      const local = getLocalData();

      if (remote && remote.updatedAt > local.updatedAt) {
        // Remote is newer — merge: remote wins, but keep local-only items
        const mergedAnnos = mergeById(remote.annotations, local.annotations);
        const mergedTags = mergeTags(remote.tags, local.tags);
        const merged = { annotations: mergedAnnos, tags: mergedTags, updatedAt: Date.now() };
        setLocalData(merged);
        await pushData(t, merged);
        // Trigger re-render by dispatching storage event
        window.dispatchEvent(new Event('sync-updated'));
      } else {
        // Local is newer or same — push
        await pushData(t, local);
      }
      setStatus('synced');
    } catch {
      setStatus('error');
    }
  }, []);

  // Auto-sync on login and periodically
  useEffect(() => {
    if (!token) return;
    doSync(token);
    const interval = setInterval(() => doSync(token), 60000); // sync every 60s
    return () => clearInterval(interval);
  }, [token, doSync]);

  // Listen for local data changes and debounce push
  useEffect(() => {
    if (!token) return;
    const handler = () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        pushData(token, getLocalData()).then(ok => {
          setStatus(ok ? 'synced' : 'error');
        });
      }, 2000);
    };
    window.addEventListener('storage-changed', handler);
    return () => window.removeEventListener('storage-changed', handler);
  }, [token]);

  const login = useCallback(async (t: string) => {
    const valid = await validateToken(t);
    if (!valid) return false;
    saveToken(t);
    setTokenState(t);
    return true;
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    setStatus('idle');
  }, []);

  const triggerSync = useCallback(() => {
    if (token) doSync(token);
  }, [token, doSync]);

  return (
    <SyncContext.Provider value={{ token, status, login, logout, triggerSync }}>
      {children}
    </SyncContext.Provider>
  );
}

// Merge helpers
function mergeById(remote: any[], local: any[]): any[] {
  const map = new Map<string, any>();
  remote.forEach(a => map.set(a.id, a));
  local.forEach(a => { if (!map.has(a.id)) map.set(a.id, a); });
  return Array.from(map.values());
}

function mergeTags(remote: Record<string, string[]>, local: Record<string, string[]>): Record<string, string[]> {
  const result: Record<string, string[]> = { ...local };
  for (const [slug, tags] of Object.entries(remote)) {
    const existing = new Set(result[slug] || []);
    tags.forEach(t => existing.add(t));
    result[slug] = Array.from(existing);
  }
  return result;
}
