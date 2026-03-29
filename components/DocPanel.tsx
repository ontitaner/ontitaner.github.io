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
import DocNav from './DocNav';
import ExportPdf from './ExportPdf';
import { useTabContext } from '@/lib/TabContext';
import { DocMeta } from '@/lib/markdown';

const Mermaid = dynamic(() => import('./Mermaid'), { ssr: false });

interface DocData {
  slug: string;
  title: string;
  date?: string;
  icon?: string | null;
  htmlContent: string;
  mermaidBlocks: string[];
}

interface DocPanelProps {
  panel: 'left' | 'right';
  allDocs: Record<string, DocData>;
  docs?: DocMeta[];
  onOpenDoc?: (slug: string, title: string) => void;
}

function DocContent({ doc, contentRef, onOpenDoc }: { doc: DocData; contentRef: React.RefObject<HTMLDivElement>; onOpenDoc?: (slug: string, title: string) => void }) {
  // Strip the first H1 from HTML to avoid duplication with the doc header
  const strippedHtml = doc.htmlContent.replace(/^(\s*<h1[^>]*>.*?<\/h1>\s*)/i, '');
  const parts = strippedHtml.split(
    /((?:<p>)?MERMAID_PLACEHOLDER_\d+(?:<\/p>)?)/
  );

  // Handle internal doc links
  useEffect(() => {
    const el = contentRef.current;
    if (!el || !onOpenDoc) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest('a');
      if (!link) return;
      const href = link.getAttribute('href') || '';
      // Match ./slug or ./slug.md patterns
      const match = href.match(/^\.\/([a-z0-9_-]+)(\.md)?$/i);
      if (match) {
        e.preventDefault();
        onOpenDoc(match[1], match[1]);
      }
    };
    el.addEventListener('click', handler);
    return () => el.removeEventListener('click', handler);
  }, [contentRef, onOpenDoc]);

  return (
    <div className="doc-content" ref={contentRef}>
      {parts.map((part, i) => {
        const match = part.match(/MERMAID_PLACEHOLDER_(\d+)/);
        if (match) {
          const idx = parseInt(match[1], 10);
          return <Mermaid key={i} chart={doc.mermaidBlocks[idx]} />;
        }
        if (!part.trim()) return null;
        return <div key={i} dangerouslySetInnerHTML={{ __html: part }} />;
      })}
    </div>
  );
}

export default function DocPanel({ panel, allDocs, docs, onOpenDoc }: DocPanelProps) {
  const { activeLeft, activeRight, moveToPanel, tabs } = useTabContext();
  const activeSlug = panel === 'left' ? activeLeft : activeRight;
  const panelTabs = tabs.filter(t => t.panel === panel);
  const scrollRef = useRef<HTMLDivElement>(null!);
  const contentRef = useRef<HTMLDivElement>(null!);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const slug = e.dataTransfer.getData('text/plain');
    if (slug) moveToPanel(slug, panel);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  if (panelTabs.length === 0 && panel === 'right') {
    return (
      <div className="doc-panel drop-zone" onDrop={handleDrop} onDragOver={handleDragOver}>
        <div className="drop-hint">拖拽标签到此处分屏查看</div>
      </div>
    );
  }

  const doc = activeSlug ? allDocs[activeSlug] : null;

  return (
    <div className="doc-panel" onDrop={handleDrop} onDragOver={handleDragOver}>
      <TabBar panel={panel} />
      {doc ? (
        <>
          <ReadingProgress scrollRef={scrollRef} />
          <div className="doc-scroll" ref={scrollRef} style={{ position: 'relative' }}>
            <div className="doc-header">
              <div>
                <h1>{doc.title}</h1>
                {doc.date && <span className="doc-date">{doc.date}</span>}
              </div>
              <ExportPdf title={doc.title} scrollRef={scrollRef} />
            </div>
            <TagEditor slug={doc.slug} />
            <DocContent doc={doc} contentRef={contentRef} onOpenDoc={onOpenDoc} />
            {docs && onOpenDoc && <DocNav currentSlug={doc.slug} docs={docs} onOpen={onOpenDoc} />}
            <DocAnnotations slug={doc.slug} scrollRef={scrollRef} />
            <CodeCopy containerRef={contentRef} />
            <CodeLangLabel containerRef={contentRef} />
            <HeadingAnchors containerRef={contentRef} />
            <ScrollToTop scrollRef={scrollRef} />
          </div>
          <TableOfContents scrollRef={scrollRef} slug={doc.slug} />
        </>
      ) : (
        <div className="empty-panel">选择一个文档开始阅读</div>
      )}
    </div>
  );
}
