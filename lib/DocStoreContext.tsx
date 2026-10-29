// @AI_GENERATED: Client cache for build-generated document JSON
import { createContext, ReactNode, useCallback, useContext, useRef, useState } from 'react';
import { DocData } from './docData';

interface DocStoreValue {
  documents: Record<string, DocData>;
  loadDoc: (slug: string) => Promise<DocData>;
}

const DocStoreContext = createContext<DocStoreValue | null>(null);

function docDataUrl(slug: string): string {
  return `/docs-data/${slug.split('/').map(encodeURIComponent).join('/')}.json`;
}

function isDocData(value: unknown): value is DocData {
  if (!value || typeof value !== 'object') return false;
  const doc = value as Partial<DocData>;
  return typeof doc.slug === 'string' && typeof doc.title === 'string' &&
    typeof doc.htmlContent === 'string' && Array.isArray(doc.mermaidBlocks);
}

export function DocStoreProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<Record<string, DocData>>({});
  const pending = useRef(new Map<string, Promise<DocData>>());

  const loadDoc = useCallback(async (slug: string): Promise<DocData> => {
    const cached = documents[slug];
    if (cached) return cached;

    const existing = pending.current.get(slug);
    if (existing) return existing;

    const request = fetch(docDataUrl(slug))
      .then(async response => {
        if (!response.ok) throw new Error(`无法加载文章（${response.status}）`);
        const data: unknown = await response.json();
        if (!isDocData(data) || data.slug !== slug) throw new Error('文章数据格式无效');
        setDocuments(current => ({ ...current, [slug]: data }));
        return data;
      })
      .finally(() => pending.current.delete(slug));

    pending.current.set(slug, request);
    return request;
  }, [documents]);

  return <DocStoreContext.Provider value={{ documents, loadDoc }}>{children}</DocStoreContext.Provider>;
}

export function useDocStore(): DocStoreValue {
  const value = useContext(DocStoreContext);
  if (!value) throw new Error('useDocStore 必须在 DocStoreProvider 内使用');
  return value;
}
// @AI_GENERATED: end
