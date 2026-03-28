import { useState, useMemo } from 'react';
import { useTabContext } from '@/lib/TabContext';
import { useTagContext } from '@/lib/TagContext';
import { DocMeta } from '@/lib/markdown';
import { IconBolt, IconSearch, IconX, IconDoc, IconChevron, IconFolder, IconTag, IconHome } from './Icons';
import SyncButton from './SyncButton';
import ThemeToggle from './ThemeToggle';
import siteConfig from '@/site.config';

export default function Sidebar({ docs, onSearchOpen }: { docs: DocMeta[]; onSearchOpen?: () => void }) {
  const { openTab, activeLeft, activeRight, tabs } = useTabContext();
  const { getTags, allTags, docsByTag, removeTagGlobal } = useTagContext();
  const [search, setSearch] = useState('');
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [mini, setMini] = useState(false);

  // Sync mini state to body for CSS
  const toggleMini = () => {
    setMini(prev => {
      const next = !prev;
      document.body.setAttribute('data-sidebar', next ? 'mini' : 'full');
      return next;
    });
  };

  const isActive = (slug: string) => slug === activeLeft || slug === activeRight;
  const isOpen = (slug: string) => tabs.some(t => t.slug === slug);

  const filtered = useMemo(() => {
    let list = docs;
    if (activeTag) {
      const slugs = new Set(docsByTag(activeTag));
      list = list.filter(d => slugs.has(d.slug));
    }
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(d =>
        d.title.toLowerCase().includes(q) ||
        getTags(d.slug).some(t => t.toLowerCase().includes(q))
      );
    }
    return list;
  }, [docs, search, activeTag, getTags, docsByTag]);

  const grouped = useMemo(() => {
    if (activeTag || search) return null;
    const map = new Map<string, DocMeta[]>();
    const untagged: DocMeta[] = [];
    filtered.forEach(d => {
      const userTags = getTags(d.slug);
      if (userTags.length === 0) { untagged.push(d); return; }
      userTags.forEach(t => {
        if (!map.has(t)) map.set(t, []);
        map.get(t)!.push(d);
      });
    });
    return { map, untagged };
  }, [filtered, activeTag, search, getTags]);

  const toggleGroup = (tag: string) => {
    setCollapsed(prev => ({ ...prev, [tag]: !prev[tag] }));
  };

  const renderItem = (doc: DocMeta) => (
    <li key={doc.slug} className="nav-item">
      <a
        href="#"
        className={`nav-link ${isActive(doc.slug) ? 'nav-active' : ''} ${isOpen(doc.slug) ? 'nav-open' : ''}`}
        onClick={e => { e.preventDefault(); openTab(doc.slug, doc.title); }}
      >
        <span className="nav-icon"><IconDoc size={15} /></span>
        <span className="nav-text">{doc.title}</span>
        {isOpen(doc.slug) && <span className="nav-dot" />}
      </a>
    </li>
  );

  return (
    <nav className={`sidebar ${mini ? 'sidebar-mini' : ''}`}>
      <div className="sidebar-brand">
        <div className="brand-icon" onClick={() => window.dispatchEvent(new Event('lock-screen'))} style={{ cursor: 'pointer' }} title="锁定"><IconBolt size={16} /></div>
        {!mini && <span className="brand-text">{siteConfig.title}</span>}
        {!mini && (
          <div className="brand-actions">
            <button className="brand-btn" onClick={onSearchOpen} title="搜索 Ctrl+K"><IconSearch size={15} /></button>
            <ThemeToggle />
            <SyncButton />
          </div>
        )}
      </div>

      {!mini && (
        <>
          <div className="sidebar-filter">
            <input
              type="text"
              placeholder="过滤文档..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="sidebar-filter-input"
            />
            {search && <button className="filter-clear" onClick={() => setSearch('')}><IconX size={10} /></button>}
          </div>

          {allTags.length > 0 && (
        <div className="sidebar-tag-bar">
          <button
            className={`stag ${!activeTag ? 'stag-on' : ''}`}
            onClick={() => setActiveTag(null)}
          >全部</button>
          {allTags.map(tag => (
            <button
              key={tag}
              className={`stag ${activeTag === tag ? 'stag-on' : ''}`}
              onClick={() => setActiveTag(activeTag === tag ? null : tag)}
            >
              <IconTag size={10} /> {tag}
              <span
                className="stag-del"
                onClick={(e) => {
                  e.stopPropagation();
                  if (activeTag === tag) setActiveTag(null);
                  removeTagGlobal(tag);
                }}
              >
                <IconX size={9} />
              </span>
            </button>
          ))}
        </div>
      )}
        </>
      )}

      <div className="sidebar-nav">
        {mini ? (
          <ul className="nav-list">
            {docs.map(doc => (
              <li key={doc.slug} className="nav-item">
                <a
                  href="#"
                  className={`nav-link ${isActive(doc.slug) ? 'nav-active' : ''}`}
                  onClick={e => { e.preventDefault(); openTab(doc.slug, doc.title); }}
                  title={doc.title}
                >
                  <span className="nav-icon"><IconDoc size={15} /></span>
                </a>
              </li>
            ))}
          </ul>
        ) : (
          <>
        {(activeTag || search) ? (
          <ul className="nav-list">{filtered.map(renderItem)}</ul>
        ) : grouped && grouped.map.size > 0 ? (
          <>
            {Array.from(grouped.map.entries()).map(([tag, tagDocs]) => (
              <div key={tag} className="nav-group">
                <button className="nav-group-header" onClick={() => toggleGroup(tag)}>
                  <IconChevron size={12} open={!collapsed[tag]} />
                  <span className="nav-group-icon"><IconFolder size={13} /></span>
                  <span className="nav-group-name">{tag}</span>
                  <span className="nav-group-count">{tagDocs.length}</span>
                </button>
                {!collapsed[tag] && <ul className="nav-list">{tagDocs.map(renderItem)}</ul>}
              </div>
            ))}
            {grouped.untagged.length > 0 && (
              <div className="nav-group">
                <button className="nav-group-header" onClick={() => toggleGroup('__untagged')}>
                  <IconChevron size={12} open={!collapsed['__untagged']} />
                  <span className="nav-group-icon"><IconFolder size={13} /></span>
                  <span className="nav-group-name">未分类</span>
                  <span className="nav-group-count">{grouped.untagged.length}</span>
                </button>
                {!collapsed['__untagged'] && <ul className="nav-list">{grouped.untagged.map(renderItem)}</ul>}
              </div>
            )}
          </>
        ) : (
          <ul className="nav-list">{filtered.map(renderItem)}</ul>
        )}
        {filtered.length === 0 && <div className="nav-empty">无匹配结果</div>}
          </>
        )}
      </div>

      <button className="sidebar-collapse-btn" onClick={toggleMini} title={mini ? '展开侧边栏' : '收起侧边栏'}>
        <IconChevron size={14} open={!mini} />
      </button>
    </nav>
  );
}
