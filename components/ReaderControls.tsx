// @AI_GENERATED
import { useMemo, useState } from 'react';
import { DocMeta } from '@/lib/markdown';

interface ReaderControlsProps {
  currentSlug: string;
  docs: DocMeta[];
  onOpen: (slug: string, title: string) => void;
  onDirectory: (collection: string) => void;
}

function orderValue(doc: DocMeta): number {
  const match = doc.title.match(/^(\d+)_/);
  return match ? Number(match[1]) : Number.MAX_SAFE_INTEGER;
}

export default function ReaderControls({ currentSlug, docs, onOpen, onDirectory }: ReaderControlsProps) {
  const [expanded, setExpanded] = useState(false);
  const current = docs.find(doc => doc.slug === currentSlug);
  const chapters = useMemo(() => {
    if (!current) return [];
    return docs
      .filter(doc => doc.collection === current.collection)
      .sort((a, b) => orderValue(a) - orderValue(b) || a.title.localeCompare(b.title));
  }, [current, docs]);
  const index = chapters.findIndex(doc => doc.slug === currentSlug);
  const previous = index > 0 ? chapters[index - 1] : null;
  const next = index >= 0 && index < chapters.length - 1 ? chapters[index + 1] : null;

  if (!current) return null;

  return (
    <div
      className={`reader-controls ${expanded ? 'reader-controls-expanded' : ''}`}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      <button
        className="reader-control-btn"
        disabled={!previous}
        onClick={() => previous && onOpen(previous.slug, previous.title)}
        aria-label="前一篇"
      >
        {'<'}
      </button>
      <button
        className="reader-control-btn reader-control-directory"
        onClick={() => onDirectory(current.collection)}
        aria-label="返回目录"
      >
        ▦
      </button>
      <button
        className="reader-control-btn"
        disabled={!next}
        onClick={() => next && onOpen(next.slug, next.title)}
        aria-label="后一篇"
      >
        {'>'}
      </button>
    </div>
  );
}
// @AI_GENERATED: end
