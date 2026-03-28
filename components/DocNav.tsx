import { DocMeta } from '@/lib/markdown';
import { IconChevron } from './Icons';

interface Props {
  currentSlug: string;
  docs: DocMeta[];
  onOpen: (slug: string, title: string) => void;
}

export default function DocNav({ currentSlug, docs, onOpen }: Props) {
  const idx = docs.findIndex(d => d.slug === currentSlug);
  if (idx === -1) return null;
  const prev = idx > 0 ? docs[idx - 1] : null;
  const next = idx < docs.length - 1 ? docs[idx + 1] : null;

  if (!prev && !next) return null;

  return (
    <div className="doc-nav">
      {prev ? (
        <button className="doc-nav-btn doc-nav-prev" onClick={() => onOpen(prev.slug, prev.title)}>
          <span className="doc-nav-arrow"><IconChevron size={14} /></span>
          <div className="doc-nav-info">
            <span className="doc-nav-label">上一篇</span>
            <span className="doc-nav-title">{prev.title}</span>
          </div>
        </button>
      ) : <div />}
      {next ? (
        <button className="doc-nav-btn doc-nav-next" onClick={() => onOpen(next.slug, next.title)}>
          <div className="doc-nav-info" style={{ textAlign: 'right' }}>
            <span className="doc-nav-label">下一篇</span>
            <span className="doc-nav-title">{next.title}</span>
          </div>
          <span className="doc-nav-arrow doc-nav-arrow-right"><IconChevron size={14} open /></span>
        </button>
      ) : <div />}
    </div>
  );
}
