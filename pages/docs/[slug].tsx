import { GetStaticPaths, GetStaticProps } from 'next';
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useTabContext } from '@/lib/TabContext';
import { getAllDocs, getDocBySlug, DocMeta } from '@/lib/markdown';
import Sidebar from '@/components/Sidebar';
import DocPanel from '@/components/DocPanel';

interface DocData {
  slug: string;
  title: string;
  date?: string;
  icon?: string;
  htmlContent: string;
  mermaidBlocks: string[];
}

interface DocPageProps {
  doc: DocData;
  docs: DocMeta[];
  allDocs: Record<string, DocData>;
}

export default function DocPage({ doc, docs, allDocs }: DocPageProps) {
  const { openTab, tabs } = useTabContext();
  const router = useRouter();

  useEffect(() => {
    openTab(doc.slug, doc.title);
    router.replace('/', undefined, { shallow: true });
  }, [doc.slug, doc.title]);

  return (
    <div className="layout">
      <Sidebar docs={docs} />
      <div className="panels-container">
        <DocPanel panel="left" allDocs={allDocs} />
      </div>
    </div>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const docs = getAllDocs();
  return {
    paths: docs.map((d) => ({ params: { slug: d.slug } })),
    fallback: false,
  };
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const slug = params?.slug as string;
  const doc = await getDocBySlug(slug);
  const docs = getAllDocs();
  const allDocs: Record<string, DocData> = {};
  for (const d of docs) {
    allDocs[d.slug] = await getDocBySlug(d.slug);
  }
  return { props: { doc, docs, allDocs } };
};
