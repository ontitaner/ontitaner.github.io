// @AI_GENERATED: Deferred full-text search index loading
import { useState, useEffect, useRef, useCallback } from 'react';
import { IconSearch, IconDoc } from './Icons';
import { SearchIndexEntry } from '@/lib/docData';

interface SearchResult {
  slug: string;
  title: string;
  snippet: string;
}

interface Props {
  onOpen: (slug: string, title: string) => Promise<void>;
  isOpen: boolean;
  onClose: () => void;
}

function getSnippet(text: string, query: string): string {
  const lower = text.toLowerCase();
  const idx = lower.indexOf(query.toLowerCase());
  if (idx === -1) return text.slice(0, 120) + '...';
  const start = Math.max(0, idx - 40);
  const end = Math.min(text.length, idx + query.length + 80);
  return (start > 0 ? '...' : '') + text.slice(start, end) + (end < text.length ? '...' : '');
}

export default function SearchModal({ onOpen, isOpen, onClose }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [entries, setEntries] = useState<SearchIndexEntry[] | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    setQuery('');
    setResults([]);
    setSelected(0);
    setTimeout(() => inputRef.current?.focus(), 50);
    if (entries) return;

    fetch('/docs-data/search-index.json')
      .then(async response => {
        if (!response.ok) throw new Error(`搜索索引加载失败（${response.status}）`);
        const data: unknown = await response.json();
        if (!Array.isArray(data)) throw new Error('搜索索引格式无效');
        setEntries(data as SearchIndexEntry[]);
      })
      .catch(error => {
        console.error(error);
        setLoadError(true);
      });
  }, [entries, isOpen]);

  const search = useCallback((q: string) => {
    setQuery(q);
    if (!q.trim() || !entries) {
      setResults([]);
      return;
    }
    const normalized = q.toLowerCase();
    setResults(entries
      .filter(entry => entry.title.toLowerCase().includes(normalized) || entry.text.toLowerCase().includes(normalized))
      .map(entry => ({ slug: entry.slug, title: entry.title, snippet: getSnippet(entry.text, q) })));
    setSelected(0);
  }, [entries]);

  const handleOpen = (result: SearchResult) => {
    void onOpen(result.slug, result.title);
    onClose();
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelected(s => Math.min(s + 1, results.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
    if (e.key === 'Enter' && results[selected]) handleOpen(results[selected]);
    if (e.key === 'Escape') onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="search-overlay" onClick={onClose}>
      <div className="search-modal" onClick={e => e.stopPropagation()}>
        <div className="search-header">
          <IconSearch size={16} />
          <input ref={inputRef} type="text" placeholder="搜索文档内容..." value={query} onChange={e => search(e.target.value)} onKeyDown={handleKey} />
          <kbd className="search-kbd">ESC</kbd>
        </div>
        {!entries && !loadError && <div className="search-empty">正在加载搜索索引…</div>}
        {loadError && <div className="search-empty">搜索索引加载失败，请刷新页面后重试</div>}
        {results.length > 0 && (
          <div className="search-results">
            {results.map((result, index) => (
              <div key={result.slug} className={`search-result ${index === selected ? 'search-result-active' : ''}`} onClick={() => handleOpen(result)} onMouseEnter={() => setSelected(index)}>
                <span className="search-result-icon"><IconDoc size={14} /></span>
                <div className="search-result-body">
                  <div className="search-result-title">{result.title}</div>
                  <div className="search-result-snippet">{result.snippet}</div>
                </div>
              </div>
            ))}
          </div>
        )}
        {entries && query && results.length === 0 && <div className="search-empty">无匹配结果</div>}
      </div>
    </div>
  );
}
// @AI_GENERATED: end
