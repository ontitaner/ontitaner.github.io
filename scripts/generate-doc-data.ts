// @AI_GENERATED: Build static per-document JSON and deferred search index
import fs from 'fs';
import path from 'path';
import { getAllDocs, getDocBySlug } from '../lib/markdown';
import { SearchIndexEntry } from '../lib/docData';

const outputDir = path.join(process.cwd(), 'public', 'docs-data');

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
}

async function main() {
  fs.rmSync(outputDir, { recursive: true, force: true });
  fs.mkdirSync(outputDir, { recursive: true });

  const docs = getAllDocs();
  const searchIndex: SearchIndexEntry[] = [];

  for (const meta of docs) {
    const doc = await getDocBySlug(meta.slug);
    const outputFile = path.join(outputDir, ...meta.slug.split('/')) + '.json';
    fs.mkdirSync(path.dirname(outputFile), { recursive: true });
    fs.writeFileSync(outputFile, JSON.stringify(doc));
    searchIndex.push({ slug: doc.slug, title: doc.title, text: stripHtml(doc.htmlContent) });
  }

  fs.writeFileSync(path.join(outputDir, 'search-index.json'), JSON.stringify(searchIndex));
  console.log(`Generated ${docs.length} document payloads in ${outputDir}`);
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
// @AI_GENERATED: end
