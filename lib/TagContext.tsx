import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';

interface TagStore {
  // slug -> tags[]
  [slug: string]: string[];
}

interface TagContextType {
  getTags: (slug: string) => string[];
  addTag: (slug: string, tag: string) => void;
  removeTag: (slug: string, tag: string) => void;
  removeTagGlobal: (tag: string) => void;
  allTags: string[];
  docsByTag: (tag: string) => string[];
}

const TagContext = createContext<TagContextType>(null!);
export const useTagContext = () => useContext(TagContext);

const STORAGE_KEY = 'doc-user-tags';

function loadTags(): TagStore {
  if (typeof window === 'undefined') return {};
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  } catch { return {}; }
}

function saveTags(store: TagStore) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  if (typeof window !== 'undefined') window.dispatchEvent(new Event('storage-changed'));
}

export function TagProvider({ children }: { children: ReactNode }) {
  const [store, setStore] = useState<TagStore>({});

  useEffect(() => { setStore(loadTags()); }, []);

  // Reload when sync pulls new data
  useEffect(() => {
    const handler = () => setStore(loadTags());
    window.addEventListener('sync-updated', handler);
    return () => window.removeEventListener('sync-updated', handler);
  }, []);

  const getTags = useCallback((slug: string) => store[slug] || [], [store]);

  const addTag = useCallback((slug: string, tag: string) => {
    setStore(prev => {
      const tags = prev[slug] || [];
      if (tags.includes(tag)) return prev;
      const next = { ...prev, [slug]: [...tags, tag] };
      saveTags(next);
      return next;
    });
  }, []);

  const removeTag = useCallback((slug: string, tag: string) => {
    setStore(prev => {
      const tags = (prev[slug] || []).filter(t => t !== tag);
      const next = { ...prev, [slug]: tags };
      if (tags.length === 0) delete next[slug];
      saveTags(next);
      return next;
    });
  }, []);

  const removeTagGlobal = useCallback((tag: string) => {
    setStore(prev => {
      const next: TagStore = {};
      for (const [slug, tags] of Object.entries(prev)) {
        const filtered = tags.filter(t => t !== tag);
        if (filtered.length > 0) next[slug] = filtered;
      }
      saveTags(next);
      return next;
    });
  }, []);

  const allTags = Array.from(new Set(Object.values(store).flat())).sort();

  const docsByTag = useCallback((tag: string) => {
    return Object.entries(store)
      .filter(([, tags]) => tags.includes(tag))
      .map(([slug]) => slug);
  }, [store]);

  return (
    <TagContext.Provider value={{ getTags, addTag, removeTag, removeTagGlobal, allTags, docsByTag }}>
      {children}
    </TagContext.Provider>
  );
}
