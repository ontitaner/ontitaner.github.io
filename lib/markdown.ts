// @AI_GENERATED
import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeRaw from 'rehype-raw';
import rehypeHighlight from 'rehype-highlight';
import rehypeStringify from 'rehype-stringify';

// 文章集合根目录：一个子目录 = 一个集合，整体托管在 public 下可被静态伺服
const collectionsDir = path.join(process.cwd(), 'public', 'collections');

export interface DocMeta {
  slug: string;            // 相对 collections 的路径（不含 .md），如 ems-python-learning/00_导读
  title: string;           // = 文件名（不含 .md）
  collection: string;      // 集合目录名（slug 首段）
  collectionName: string;  // collection.json.name 或目录名
  collectionOrder: number; // collection.json.order 或 999
  collectionDescription?: string;
  collectionIcon?: string;
  collectionLevel?: string;
  collectionCover?: string | null;
  date?: string;
  icon?: string | null;
}

interface CollectionConf {
  name?: string;
  order?: number;
  description?: string;
  icon?: string;
  level?: string;
  cover?: string;
}

function readCollectionConf(dir: string): CollectionConf {
  const f = path.join(collectionsDir, dir, 'collection.json');
  if (!fs.existsSync(f)) return {};
  try { return JSON.parse(fs.readFileSync(f, 'utf-8')); } catch { return {}; }
}

// 递归收集集合内所有 .md，跳过 _ 开头的文件/目录
function walkMd(abs: string, rel: string, out: string[]) {
  for (const name of fs.readdirSync(abs)) {
    if (name.startsWith('_')) continue;
    const childAbs = path.join(abs, name);
    const childRel = rel ? `${rel}/${name}` : name;
    if (fs.statSync(childAbs).isDirectory()) walkMd(childAbs, childRel, out);
    else if (name.endsWith('.md')) out.push(childRel);
  }
}

export function getAllDocs(): DocMeta[] {
  if (!fs.existsSync(collectionsDir)) return [];
  const collections = fs.readdirSync(collectionsDir)
    .filter((d) => !d.startsWith('_') && fs.statSync(path.join(collectionsDir, d)).isDirectory());

  const confCache = new Map<string, CollectionConf>();
  const docs: DocMeta[] = [];

  for (const collection of collections) {
    const conf = readCollectionConf(collection);
    confCache.set(collection, conf);
    const relFiles: string[] = [];
    walkMd(path.join(collectionsDir, collection), collection, relFiles);
    for (const rel of relFiles) {
      const slug = rel.replace(/\.md$/, '');
      const title = path.basename(slug);
      const stat = fs.statSync(path.join(collectionsDir, rel));
      docs.push({
        slug,
        title,
        collection,
        collectionName: conf.name || collection,
        collectionOrder: conf.order ?? 999,
        collectionDescription: conf.description,
        collectionIcon: conf.icon,
        collectionLevel: conf.level,
        collectionCover: conf.cover || null,
        date: stat.mtime.toISOString().slice(0, 10),
        icon: null,
      });
    }
  }

  // 集合间按 order→目录名；集合内按文件名（slug 含集合前缀，字符串序即可）
  return docs.sort((a, b) =>
    a.collectionOrder - b.collectionOrder ||
    (a.collection < b.collection ? -1 : a.collection > b.collection ? 1 : 0) ||
    (a.slug < b.slug ? -1 : a.slug > b.slug ? 1 : 0)
  );
}

const MERMAID_MARKER = 'MERMAID_PLACEHOLDER_';

// 构建期把相对图片 src 改写成 /collections 绝对路径（源 md 不动）。
// SPA 注入 HTML 时页面 URL 恒为 /，相对路径会错位，故必须绝对化。
function rewriteRelativeSrc(html: string, slug: string): string {
  const dir = slug.split('/').slice(0, -1).join('/'); // md 文件所在目录（相对 collections）
  return html.replace(/(<img\b[^>]*?\ssrc=")([^"]+)(")/gi, (full, pre, src, post) => {
    if (/^(https?:|data:|\/|#)/i.test(src)) return full; // 已是绝对/外链/内联，跳过
    const clean = src.replace(/^\.\//, '');
    return `${pre}/collections/${dir}/${clean}${post}`;
  });
}

export async function getDocBySlug(slug: string) {
  const filePath = path.join(collectionsDir, `${slug}.md`);
  const fileContent = fs.readFileSync(filePath, 'utf-8');
  const { data, content } = matter(fileContent);

  // Extract mermaid code blocks before processing
  const mermaidBlocks: string[] = [];
  const contentWithPlaceholders = content.replace(
    /```mermaid\s*\r?\n([\s\S]*?)```/g,
    (_match, code) => {
      const idx = mermaidBlocks.length;
      mermaidBlocks.push(code.trim());
      return `\n\n${MERMAID_MARKER}${idx}\n\n`;
    }
  );

  const result = await unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(rehypeRaw)
    .use(rehypeHighlight, { detect: true, ignoreMissing: true })
    .use(rehypeStringify)
    .process(contentWithPlaceholders);

  const htmlContent = rewriteRelativeSrc(result.toString(), slug);

  const stat = fs.statSync(filePath);

  return {
    slug,
    title: (data.title as string) || path.basename(slug),
    date: (data.date as string) || stat.mtime.toISOString().slice(0, 10),
    icon: (data.icon as string) || null,
    htmlContent,
    mermaidBlocks,
  };
}
// @AI_GENERATED: end
