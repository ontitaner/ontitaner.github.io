// @AI_GENERATED
import { useRef, useEffect } from 'react';
import dynamic from 'next/dynamic';
import TabBar from './TabBar';
import TagEditor from './TagEditor';
import ScrollToTop from './ScrollToTop';
import DocAnnotations from './DocAnnotations';
import ReadingProgress from './ReadingProgress';
import CodeCopy from './CodeCopy';
import CodeLangLabel from './CodeLangLabel';
import HeadingAnchors from './HeadingAnchors';
import TableOfContents from './TableOfContents';
import ReaderControls from './ReaderControls';
import ExportPdf from './ExportPdf';
import ReadingMode from './ReadingMode';
import ThemeToggle from './ThemeToggle';
import { IconSearch } from './Icons';
import { useTabContext } from '@/lib/TabContext';
import { DocMeta } from '@/lib/markdown';
import { DocData } from '@/lib/docData';

const Mermaid = dynamic(() => import('./Mermaid'), { ssr: false });

interface DocPanelProps {
  panel: 'left' | 'right';
  documents: Record<string, DocData>;
  docs?: DocMeta[];
  onOpenDoc?: (slug: string, title: string, panel?: 'left' | 'right') => Promise<void>;
  onDirectory?: (collection: string) => void;
  onSearchOpen?: () => void;
}

function DocContent({ doc, contentRef, onOpenDoc }: { doc: DocData; contentRef: React.RefObject<HTMLDivElement>; onOpenDoc?: (slug: string, title: string) => void }) {
  const strippedHtml = doc.htmlContent.replace(/^(\s*<h1[^>]*>.*?<\/h1>\s*)/i, '');
  const parts = strippedHtml.split(/((?:<p>)?MERMAID_PLACEHOLDER_\d+(?:<\/p>)?)/);

  useEffect(() => {
    const element = contentRef.current;
    if (!element || !onOpenDoc) return;
    const handler = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const link = target.closest('a');
      if (!link) return;
      const href = link.getAttribute('href') || '';
      const match = href.match(/^\.\/([a-z0-9_-]+)(\.md)?$/i);
      if (match) {
        event.preventDefault();
        onOpenDoc(match[1], match[1]);
      }
    };
    element.addEventListener('click', handler);
    return () => element.removeEventListener('click', handler);
  }, [contentRef, onOpenDoc]);

  return <div className="doc-content" ref={contentRef}>{parts.map((part, index) => {
    const match = part.match(/MERMAID_PLACEHOLDER_(\d+)/);
    if (match) return <Mermaid key={index} chart={doc.mermaidBlocks[parseInt(match[1], 10)]} />;
    return part.trim() ? <div key={index} dangerouslySetInnerHTML={{ __html: part }} /> : null;
  })}</div>;
}

export default function DocPanel({ panel, documents, docs, onOpenDoc, onDirectory, onSearchOpen }: DocPanelProps) {
  const { activeLeft, activeRight, moveToPanel, tabs } = useTabContext();
  const activeSlug = panel === 'left' ? activeLeft : activeRight;
  const panelTabs = tabs.filter(tab => tab.panel === panel);
  const scrollRef = useRef<HTMLDivElement>(null!);
  const contentRef = useRef<HTMLDivElement>(null!);
  const doc = activeSlug ? documents[activeSlug] : null;

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    const slug = event.dataTransfer.getData('text/plain');
    if (slug) moveToPanel(slug, panel);
  };

  if (panelTabs.length === 0 && panel === 'right') return <div className="doc-panel drop-zone" onDrop={handleDrop} onDragOver={event => event.preventDefault()}><div className="drop-hint">拖拽标签到此处分屏查看</div></div>;

  return (
    <div className="doc-panel" onDrop={handleDrop} onDragOver={event => event.preventDefault()}>
      <TabBar panel={panel} />
      {doc ? <>
        <ReadingProgress scrollRef={scrollRef} />
        <div className="doc-scroll" ref={scrollRef} style={{ position: 'relative' }}>
          <div className="doc-header"><div><h1>{doc.title}</h1>{doc.date && <span className="doc-date">{doc.date}</span>}</div><div className="doc-toolbar">{onSearchOpen && <button className="doc-toolbar-btn" onClick={onSearchOpen} title="搜索 Ctrl+K" aria-label="搜索"><IconSearch size={14} /></button>}<ThemeToggle /><ReadingMode /><ExportPdf title={doc.title} scrollRef={scrollRef} /></div></div>
          <TagEditor slug={doc.slug} />
          {docs && onOpenDoc && onDirectory && <ReaderControls currentSlug={doc.slug} docs={docs} onOpen={(slug, title) => onOpenDoc(slug, title, panel)} onDirectory={onDirectory} />}
          <DocContent doc={doc} contentRef={contentRef} onOpenDoc={onOpenDoc ? (slug, title) => { void onOpenDoc(slug, title, panel); } : undefined} />
          <DocAnnotations slug={doc.slug} scrollRef={scrollRef} />
          <CodeCopy containerRef={contentRef} />
          <CodeLangLabel containerRef={contentRef} />
          <HeadingAnchors containerRef={contentRef} />
          <ScrollToTop scrollRef={scrollRef} />
        </div>
        <TableOfContents scrollRef={scrollRef} slug={doc.slug} />
      </> : <div className="empty-panel">正在加载文章…</div>}
    </div>
  );
}
// @AI_GENERATED: end