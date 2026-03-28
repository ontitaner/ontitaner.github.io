const TOKEN_KEY = 'gist-sync-token';
const GIST_ID_KEY = 'gist-sync-id';
const GIST_FILENAME = 'tech-docs-data.json';
const GIST_DESC = 'Tech Docs - synced data (annotations, tags)';

export interface SyncData {
  annotations: any[];
  tags: Record<string, string[]>;
  updatedAt: number;
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(GIST_ID_KEY);
}

export function getGistId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(GIST_ID_KEY);
}

function headers(token: string) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'Content-Type': 'application/json',
  };
}

// Find existing gist or create new one
async function ensureGist(token: string): Promise<string> {
  const existing = localStorage.getItem(GIST_ID_KEY);
  if (existing) {
    // Verify it still exists
    const res = await fetch(`https://api.github.com/gists/${existing}`, { headers: headers(token) });
    if (res.ok) return existing;
    localStorage.removeItem(GIST_ID_KEY);
  }

  // Search user's gists for our file
  const listRes = await fetch('https://api.github.com/gists?per_page=100', { headers: headers(token) });
  if (!listRes.ok) throw new Error(`GitHub API error: ${listRes.status}`);
  const gists = await listRes.json();
  for (const g of gists) {
    if (g.files && g.files[GIST_FILENAME]) {
      localStorage.setItem(GIST_ID_KEY, g.id);
      return g.id;
    }
  }

  // Create new gist
  const createRes = await fetch('https://api.github.com/gists', {
    method: 'POST',
    headers: headers(token),
    body: JSON.stringify({
      description: GIST_DESC,
      public: false,
      files: { [GIST_FILENAME]: { content: JSON.stringify({ annotations: [], tags: {}, updatedAt: Date.now() }) } },
    }),
  });
  if (!createRes.ok) throw new Error(`Create gist failed: ${createRes.status}`);
  const created = await createRes.json();
  localStorage.setItem(GIST_ID_KEY, created.id);
  return created.id;
}

export async function pullData(token: string): Promise<SyncData | null> {
  try {
    const gistId = await ensureGist(token);
    const res = await fetch(`https://api.github.com/gists/${gistId}`, { headers: headers(token) });
    if (!res.ok) return null;
    const gist = await res.json();
    const file = gist.files?.[GIST_FILENAME];
    if (!file?.content) return null;
    return JSON.parse(file.content);
  } catch (e) {
    console.error('Gist pull failed:', e);
    return null;
  }
}

export async function pushData(token: string, data: SyncData): Promise<boolean> {
  try {
    const gistId = await ensureGist(token);
    const res = await fetch(`https://api.github.com/gists/${gistId}`, {
      method: 'PATCH',
      headers: headers(token),
      body: JSON.stringify({
        files: { [GIST_FILENAME]: { content: JSON.stringify({ ...data, updatedAt: Date.now() }) } },
      }),
    });
    return res.ok;
  } catch (e) {
    console.error('Gist push failed:', e);
    return false;
  }
}

export async function validateToken(token: string): Promise<boolean> {
  try {
    const res = await fetch('https://api.github.com/user', { headers: headers(token) });
    return res.ok;
  } catch {
    return false;
  }
}
