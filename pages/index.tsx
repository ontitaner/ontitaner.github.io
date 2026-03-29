import { GetStaticProps } from 'next';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import DocPanel from '@/components/DocPanel';
import SearchModal from '@/components/SearchModal';
import { useTabContext } from '@/lib/TabContext';
import { getAllDocs, getDocBySlug, DocMeta } from '@/lib/markdown';
import { IconBolt, IconDoc, IconSplitRight, IconTag } from '@/components/Icons';
import siteConfig from '@/site.config';

interface DocData {
  slug: string;
  title: string;
  date?: string;
  icon?: string | null;
  htmlContent: string;
  mermaidBlocks: string[];
}

interface HomeProps {
  docs: DocMeta[];
  allDocs: Record<string, DocData>;
}

export default function Home({ docs, allDocs }: HomeProps) {
  const { tabs, splitMode, openTab } = useTabContext();
  const hasOpenTabs = tabs.length > 0;
  const [searchOpen, setSearchOpen] = useState(false);

  // Ctrl+K shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); setSearchOpen(true); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const handleOpenDoc = (slug: string, title: string) => {
    const doc = allDocs[slug];
    if (doc) openTab(slug, doc.title);
  };

  return (
    <div className="layout">
      <Sidebar docs={docs} onSearchOpen={() => setSearchOpen(true)} />
      <div className={`panels-container ${splitMode ? 'split' : ''}`}>
        {!hasOpenTabs ? (
          <div className="main-content">
            <div className="home-hero">
              <div className="hero-icon"><IconBolt size={40} /></div>
              <h1>{siteConfig.title}</h1>
              <p>点击左侧文档开始阅读，Ctrl+K 全文搜索</p>
              <div className="hero-stats">
                <div className="hero-stat"><span className="hero-stat-num">{docs.length}</span><span>篇文档</span></div>
              </div>
              <div className="hero-features">
                <div className="hero-feat"><span className="hero-feat-icon"><IconDoc size={18} /></span><span>Markdown 文档</span></div>
                <div className="hero-feat"><span className="hero-feat-icon"><IconSplitRight size={18} /></span><span>分屏对比</span></div>
                <div className="hero-feat"><span className="hero-feat-icon"><IconTag size={18} /></span><span>标签归类</span></div>
              </div>
            </div>
            <div className="home-cards">
              {docs.map(doc => (
                <button key={doc.slug} className="home-card" onClick={() => openTab(doc.slug, doc.title)}>
                  <span className="card-icon"><IconDoc size={20} /></span>
                  <div className="card-body">
                    <span className="card-title">{doc.title}</span>
                    {doc.date && <span className="card-date">{doc.date}</span>}
                  </div>
                  <span className="card-arrow">→</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            <DocPanel panel="left" allDocs={allDocs} docs={docs} onOpenDoc={handleOpenDoc} />
            {splitMode && <div className="panel-divider" />}
            {splitMode && <DocPanel panel="right" allDocs={allDocs} docs={docs} onOpenDoc={handleOpenDoc} />}
          </>
        )}
      </div>
      <SearchModal allDocs={allDocs} onOpen={handleOpenDoc} isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  const docs = getAllDocs();
  const allDocs: Record<string, DocData> = {};
  for (const doc of docs) { allDocs[doc.slug] = await getDocBySlug(doc.slug); }
  return { props: { docs, allDocs } };
};
