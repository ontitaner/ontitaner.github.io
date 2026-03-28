import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';

export interface Annotation {
  id: string;
  slug: string;
  note: string;
  // Position relative to scroll container top (px from top of content)
  posY: number;
  createdAt: number;
}

interface AnnotationContextType {
  getAnnotations: (slug: string) => Annotation[];
  addAnnotation: (slug: string, note: string, posY: number) => void;
  removeAnnotation: (id: string) => void;
  updateAnnotation: (id: string, note: string) => void;
}

const AnnotationContext = createContext<AnnotationContextType>(null!);
export const useAnnotations = () => useContext(AnnotationContext);

const STORAGE_KEY = 'doc-annotations-v2';

function load(): Annotation[] {
  if (typeof window === 'undefined') return [];
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
  catch { return []; }
}

function save(list: Annotation[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  if (typeof window !== 'undefined') window.dispatchEvent(new Event('storage-changed'));
}

export function AnnotationProvider({ children }: { children: ReactNode }) {
  const [list, setList] = useState<Annotation[]>([]);

  useEffect(() => { setList(load()); }, []);

  // Reload when sync pulls new data
  useEffect(() => {
    const handler = () => setList(load());
    window.addEventListener('sync-updated', handler);
    return () => window.removeEventListener('sync-updated', handler);
  }, []);

  const getAnnotations = useCallback(
    (slug: string) => list.filter(a => a.slug === slug).sort((a, b) => a.posY - b.posY),
    [list]
  );

  const addAnnotation = useCallback((slug: string, note: string, posY: number) => {
    const a: Annotation = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      slug,
      note,
      posY,
      createdAt: Date.now(),
    };
    setList(prev => {
      const next = [...prev, a];
      save(next);
      return next;
    });
  }, []);

  const removeAnnotation = useCallback((id: string) => {
    setList(prev => {
      const next = prev.filter(a => a.id !== id);
      save(next);
      return next;
    });
  }, []);

  const updateAnnotation = useCallback((id: string, note: string) => {
    setList(prev => {
      const next = prev.map(a => a.id === id ? { ...a, note } : a);
      save(next);
      return next;
    });
  }, []);

  return (
    <AnnotationContext.Provider value={{ getAnnotations, addAnnotation, removeAnnotation, updateAnnotation }}>
      {children}
    </AnnotationContext.Provider>
  );
}
