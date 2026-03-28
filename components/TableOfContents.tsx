import { useState, useEffect, RefObject } from 'react';

interface TocItem { id: string; text: string; level: number; }

function IconList({ size = 16 }: { size?: number }) {
  const s = { display: 'inline-block', verticalAlign: 'middle', fill: 'none', stroke: 'currentColor' } as const;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={s} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>
      <line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
    </svg>
  );
}

export default function TableOfContents({ scrollRef, slug }: { scrollRef: RefObject<HTMLDivElement>; slug?: string }) {
  const [items, setItems] = useState<TocItem[]>([]);
  const [activeId, setActiveId] = useState('');
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    setItems([]);
    setActiveId('');
    setExpanded(false);
    const timer = setTimeout(() => {
      const headings = el.querySelectorAll('h2, h3');
      const toc: TocItem[] = [];
      headings.forEach((h, i) => {
        const id = h.id || `heading-${i}`;
        if (!h.id) h.id = id;
        toc.push({ id, text: h.textContent || '', level: parseInt(h.tagName[1]) });
      });
      setItems(toc);
    }, 400);
    return () => clearTimeout(timer);
  }, [scrollRef, slug]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || items.length === 0) return;
    const onScroll = () => {
      let current = '';
      for (const item of items) {
        const heading = document.getElementById(item.id);
        if (heading && heading.getBoundingClientRect().top < 120) current = item.id;
      }
      setActiveId(current);
    };
    el.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => el.removeEventListener('scroll', onScroll);
  }, [scrollRef, items]);

  if (items.length < 2) return null;

  const scrollTo = (id: string) => {
    const el = scrollRef.current;
    const heading = document.getElementById(id);
    if (!heading || !el) return;
    const containerRect = el.getBoundingClientRect();
    const headingRect = heading.getBoundingClientRect();
    const offset = headingRect.top - containerRect.top + el.scrollTop - 20;
    el.scrollTo({ top: offset, behavior: 'smooth' });
  };

  if (!expanded) {
    return (
      <button className="toc-toggle" onClick={() => setExpanded(true)} title="展开目录">
        <IconList size={16} />
      </button>
    );
  }

  return (
    <div className="toc">
      <div className="toc-header">
        <span className="toc-title">目录</span>
        <button className="toc-close" onClick={() => setExpanded(false)}>×</button>
      </div>
      {items.map(item => (
        <a
          key={item.id}
          className={`toc-item ${item.level === 3 ? 'toc-sub' : ''} ${activeId === item.id ? 'toc-active' : ''}`}
          onClick={() => scrollTo(item.id)}
        >
          {item.text}
        </a>
      ))}
    </div>
  );
}
