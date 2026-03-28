import { useState, useEffect, useRef, useCallback } from 'react';
import { IconSearch, IconX, IconDoc } from './Icons';

interface DocData {
  slug: string;
  title: string;
  htmlContent: string;
}

interface SearchResult {
  slug: string;
  title: string;
  snippet: string;
  icon?: string;
}

interface Props {
  allDocs: Record<string, DocData>;
  onOpen: (slug: string, title: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
}

function getSnippet(text: string, query: string): string {
  const lower = text.toLowerCase();
  const idx = lower.indexOf(query.toLowerCase());
  if (idx === -1) return text.slice(0, 120) + '...';
  const start = Math.max(0, idx - 40);
  const end = Math.min(text.length, idx + query.length + 80);
  return (start > 0 ? '...' : '') + text.slice(start, end) + (end < text.length ? '...' : '');
}

export default function SearchModal({ allDocs, onOpen, isOpen, onClose }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) { setQuery(''); setResults([]); setSelected(0); setTimeout(() => inputRef.current?.focus(), 50); }
  }, [isOpen]);

  // Keyboard shortcut Ctrl+K is handled in index.tsx

  const search = useCallback((q: string) => {
    setQuery(q);
    if (!q.trim()) { setResults([]); return; }
    const r: SearchResult[] = [];
    for (const [slug, doc] of Object.entries(allDocs)) {
      const plain = stripHtml(doc.htmlContent);
      const titleMatch = doc.title.toLowerCase().includes(q.toLowerCase());
      const contentMatch = plain.toLowerCase().includes(q.toLowerCase());
      if (titleMatch || contentMatch) {
        r.push({ slug, title: doc.title, snippet: getSnippet(plain, q) });
      }
    }
    setResults(r);
    setSelected(0);
  }, [allDocs]);

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelected(s => Math.min(s + 1, results.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
    if (e.key === 'Enter' && results[selected]) {
      onOpen(results[selected].slug, results[selected].title);
      onClose();
    }
    if (e.key === 'Escape') onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="search-overlay" onClick={onClose}>
      <div className="search-modal" onClick={e => e.stopPropagation()}>
        <div className="search-header">
          <IconSearch size={16} />
          <input
            ref={inputRef}
            type="text"
            placeholder="搜索文档内容..."
            value={query}
            onChange={e => search(e.target.value)}
            onKeyDown={handleKey}
          />
          <kbd className="search-kbd">ESC</kbd>
        </div>
        {results.length > 0 && (
          <div className="search-results">
            {results.map((r, i) => (
              <div
                key={r.slug}
                className={`search-result ${i === selected ? 'search-result-active' : ''}`}
                onClick={() => { onOpen(r.slug, r.title); onClose(); }}
                onMouseEnter={() => setSelected(i)}
              >
                <span className="search-result-icon"><IconDoc size={14} /></span>
                <div className="search-result-body">
                  <div className="search-result-title">{r.title}</div>
                  <div className="search-result-snippet">{r.snippet}</div>
                </div>
              </div>
            ))}
          </div>
        )}
        {query && results.length === 0 && (
          <div className="search-empty">无匹配结果</div>
        )}
      </div>
    </div>
  );
}
