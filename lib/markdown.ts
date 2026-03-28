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

const docsDir = path.join(process.cwd(), 'docs');

export interface DocMeta {
  slug: string;
  title: string;
  order?: number;
  date?: string;
  icon?: string;
}

export function getAllDocs(): DocMeta[] {
  if (!fs.existsSync(docsDir)) return [];
  const files = fs.readdirSync(docsDir).filter((f) => f.endsWith('.md'));
  return files
    .map((filename) => {
      const slug = filename.replace(/\.md$/, '');
      const fullPath = path.join(docsDir, filename);
      const content = fs.readFileSync(fullPath, 'utf-8');
      const { data } = matter(content);
      const stat = fs.statSync(fullPath);
      return {
        slug,
        title: (data.title as string) || slug,
        order: (data.order as number) ?? 999,
        date: (data.date as string) || stat.mtime.toISOString().slice(0, 10),
        icon: (data.icon as string) || undefined,
      };
    })
    .sort((a, b) => (a.order ?? 999) - (b.order ?? 999));
}

const MERMAID_MARKER = 'MERMAID_PLACEHOLDER_';

export async function getDocBySlug(slug: string) {
  const filePath = path.join(docsDir, `${slug}.md`);
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

  const htmlContent = result.toString();

  const stat = fs.statSync(filePath);

  return {
    slug,
    title: (data.title as string) || slug,
    date: (data.date as string) || stat.mtime.toISOString().slice(0, 10),
    icon: (data.icon as string) || undefined,
    htmlContent,
    mermaidBlocks,
  };
}
