// @AI_GENERATED
import { GetStaticProps } from 'next';
import { useEffect, useMemo, useState } from 'react';
import DocPanel from '@/components/DocPanel';
import SearchModal from '@/components/SearchModal';
import { useTabContext } from '@/lib/TabContext';
import { useDocStore } from '@/lib/DocStoreContext';
import { getAllDocs, DocMeta } from '@/lib/markdown';
import { IconBolt, IconDoc, IconSearch } from '@/components/Icons';
import siteConfig from '@/site.config';

interface HomeProps {
  docs: DocMeta[];
}

interface CollectionCard {
  collection: string;
  name: string;
  description?: string;
  icon?: string;
  level?: string;
  cover?: string | null;
  docs: DocMeta[];
}

function chapterOrder(doc: DocMeta): number {
  const match = doc.title.match(/^(\d+)_/);
  return match ? Number(match[1]) : Number.MAX_SAFE_INTEGER;
}

function displayTitle(title: string): string {
  return title.replace(/^\d+_/, '');
}

export default function Home({ docs }: HomeProps) {
  const { tabs, splitMode, openTab } = useTabContext();
  const { documents, loadDoc } = useDocStore();
  const [searchOpen, setSearchOpen] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [loadingSlug, setLoadingSlug] = useState<string | null>(null);
  const hasOpenTabs = tabs.length > 0;

  const collections = useMemo(() => {
    const grouped = new Map<string, CollectionCard>();
    docs.forEach(doc => {
      const existing = grouped.get(doc.collection);
      if (existing) {
        existing.docs.push(doc);
        return;
      }
      grouped.set(doc.collection, {
        collection: doc.collection,
        name: doc.collectionName,
        description: doc.collectionDescription,
        icon: doc.collectionIcon,
        level: doc.collectionLevel,
        cover: doc.collectionCover,
        docs: [doc],
      });
    });
    return Array.from(grouped.values()).map(collection => ({
      ...collection,
      docs: collection.docs.sort((a, b) => chapterOrder(a) - chapterOrder(b) || a.title.localeCompare(b.title)),
    }));
  }, [docs]);

  const activeCollection = collections.find(collection => collection.collection === selectedCollection) || null;

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const handleOpenDoc = async (slug: string, title: string, panel: 'left' | 'right' = 'left') => {
    setLoadingSlug(slug);
    try {
      const doc = await loadDoc(slug);
      setSelectedCollection(null);
      openTab(slug, doc.title || title, panel);
    } catch (error) {
      console.error(`加载文章失败：${slug}`, error);
    } finally {
      setLoadingSlug(current => current === slug ? null : current);
    }
  };

  const handleDirectory = (collection: string) => {
    setSelectedCollection(collection);
  };

  return (
    <div className="layout">
      <div className={`panels-container ${splitMode ? 'split' : ''} ${hasOpenTabs || activeCollection ? 'panels-reader' : 'panels-home'}`}>
        {activeCollection ? (
          <main className="collection-page">
            <button className="collection-back" onClick={() => setSelectedCollection(null)}>← 所有课程</button>
            <header className="collection-page-header">
              <span className="collection-page-icon" aria-hidden="true">{activeCollection.icon || <IconDoc size={28} />}</span>
              <div>
                <h1>{activeCollection.name}</h1>
                {activeCollection.description && <p>{activeCollection.description}</p>}
                <span>{activeCollection.docs.length} 篇文章{activeCollection.level ? ` · ${activeCollection.level}` : ''}</span>
              </div>
            </header>
            <section className="chapter-grid" aria-label={`${activeCollection.name}文章目录`} aria-busy={Boolean(loadingSlug)}>
              {activeCollection.docs.map((doc, index) => (
                <button key={doc.slug} className="chapter-card" onClick={() => void handleOpenDoc(doc.slug, doc.title)} disabled={Boolean(loadingSlug)}>
                  <span className="chapter-card-order">{chapterOrder(doc) === Number.MAX_SAFE_INTEGER ? '附' : String(chapterOrder(doc)).padStart(2, '0')}</span>
                  <span className="chapter-card-title">{loadingSlug === doc.slug ? '正在加载…' : displayTitle(doc.title)}</span>
                  <span className="chapter-card-meta">第 {index + 1} 篇</span>
                  <span className="chapter-card-arrow" aria-hidden="true">→</span>
                </button>
              ))}
            </section>
          </main>
        ) : hasOpenTabs ? (
          <>
            <DocPanel panel="left" documents={documents} docs={docs} onOpenDoc={handleOpenDoc} onDirectory={handleDirectory} />
            {splitMode && <div className="panel-divider" />}
            {splitMode && <DocPanel panel="right" documents={documents} docs={docs} onOpenDoc={handleOpenDoc} onDirectory={handleDirectory} />}
          </>
        ) : (
          <main className="poster-home">
            <header className="poster-home-header">
              <div className="poster-home-brand"><IconBolt size={20} /><span>{siteConfig.title}</span></div>
              <button className="poster-search" onClick={() => setSearchOpen(true)} aria-label="搜索"><IconSearch size={18} /></button>
            </header>
            <div className="poster-home-intro">
              <h1>课程目录</h1>
              <p>选择一套课程，浏览按章节序号排列的全部文章。</p>
            </div>
            <section className="collection-poster-grid" aria-label="课程列表">
              {collections.map(collection => (
                <button key={collection.collection} className="collection-poster" onClick={() => setSelectedCollection(collection.collection)} aria-label={`浏览${collection.name}`}>
                  {collection.cover ? (
                    <img className="collection-poster-image" src={`/collections/${collection.collection}/${collection.cover}`} alt="" />
                  ) : (
                    <div className="collection-poster-placeholder" data-collection={collection.collection}>
                      <span aria-hidden="true">{collection.icon || '◈'}</span>
                    </div>
                  )}
                  <div className="collection-poster-overlay">
                    <strong>{collection.name}</strong>
                    {collection.level && <span>{collection.level}</span>}
                  </div>
                </button>
              ))}
            </section>
          </main>
        )}
      </div>
      <SearchModal onOpen={handleOpenDoc} isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}

export const getStaticProps: GetStaticProps = async () => ({ props: { docs: getAllDocs() } });
// @AI_GENERATED: end
