// @AI_GENERATED
import { GetStaticPaths, GetStaticProps } from 'next';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useTabContext } from '@/lib/TabContext';
import { useDocStore } from '@/lib/DocStoreContext';
import { getAllDocs, DocMeta } from '@/lib/markdown';

interface DocPageProps {
  slug: string;
  title: string;
  docs: DocMeta[];
}

export default function DocPage({ slug, title }: DocPageProps) {
  const { openTab } = useTabContext();
  const { loadDoc } = useDocStore();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void loadDoc(slug)
      .then(doc => {
        if (cancelled) return;
        openTab(doc.slug, doc.title || title);
        void router.replace('/');
      })
      .catch(loadError => {
        console.error(loadError);
        if (!cancelled) setError('文章加载失败，请返回首页后重试。');
      });
    return () => { cancelled = true; };
  }, [loadDoc, openTab, router, slug, title]);

  return <main className="doc-route-status">{error || '正在加载文章…'}</main>;
}

export const getStaticPaths: GetStaticPaths = async () => {
  const docs = getAllDocs();
  return { paths: docs.map(doc => ({ params: { slug: doc.slug.split('/') } })), fallback: false };
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const slug = (params?.slug as string[]).join('/');
  const doc = getAllDocs().find(item => item.slug === slug);
  if (!doc) return { notFound: true };
  return { props: { slug: doc.slug, title: doc.title, docs: getAllDocs() } };
};
// @AI_GENERATED: end
