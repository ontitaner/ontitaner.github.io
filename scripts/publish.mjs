// @AI_GENERATED
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { execSync } from 'child_process';
import AdmZip from 'adm-zip';

// Paths (relative to this script's location in ontitaner.github.io/scripts/)
const PAGES_DIR = path.resolve(import.meta.dirname, '..');
const WORKSPACE_ROOT = path.resolve(PAGES_DIR, '..', '..');
const ZIP_PATH = path.join(WORKSPACE_ROOT, 'sub_module', 'wechat', 'data', 'download', 'book.zip');
const DOCS_DIR = path.join(PAGES_DIR, 'docs');
const PUBLIC_DIR = path.join(PAGES_DIR, 'public');

function main() {
  // 1. Verify zip exists
  if (!fs.existsSync(ZIP_PATH)) {
    console.error(`Error: book.zip not found at ${ZIP_PATH}`);
    process.exit(1);
  }

  // 2. Extract zip
  const zip = new AdmZip(ZIP_PATH);
  const entries = zip.getEntries();

  // 3. Read content.md
  const contentEntry = entries.find(e => e.entryName === 'content.md');
  if (!contentEntry) {
    console.error('Error: content.md not found in zip');
    process.exit(1);
  }

  const content = contentEntry.getData().toString('utf-8');

  // 4. Extract title from first line (# Title)
  const titleMatch = content.match(/^#\s+(.+)$/m);
  const title = titleMatch ? titleMatch[1].trim() : 'Untitled';
  console.log(`Title: ${title}`);

  // 5. Generate slug: YYYY-MM-DD-<6char hash>
  const today = new Date().toISOString().slice(0, 10);
  const hash = crypto.createHash('md5').update(content).digest('hex').slice(0, 6);
  const slug = `${today}-${hash}`;
  console.log(`Slug: ${slug}`);

  // 6. Collect image entries
  const imageEntries = entries.filter(e => e.entryName.startsWith('images/') && !e.isDirectory);

  // 7. Build image URL mapping and replace in content
  const imagesTargetDir = path.join(PUBLIC_DIR, 'images', 'wechat', slug);
  fs.mkdirSync(imagesTargetDir, { recursive: true });

  let processedContent = content;

  // Map external URLs to local image files by order of appearance
  const imgPattern = /!\[([^\]]*)\]\(([^)]+)\)/g;
  const allMatches = [...content.matchAll(imgPattern)];

  const urlToLocalMap = new Map();
  for (let i = 0; i < allMatches.length; i++) {
    if (i < imageEntries.length) {
      const localFilename = path.basename(imageEntries[i].entryName);
      urlToLocalMap.set(allMatches[i][2], localFilename);
    }
  }

  // Replace URLs in content
  processedContent = content.replace(imgPattern, (full, alt, url) => {
    const localFilename = urlToLocalMap.get(url);
    if (localFilename) {
      return `![${alt}](/images/wechat/${slug}/${localFilename})`;
    }
    return full;
  });

  // 8. Remove the title line from body (will be in frontmatter)
  processedContent = processedContent.replace(/^#\s+.+\n\n?/, '');

  // 9. Add frontmatter
  const frontmatter = `---
title: "${title.replace(/"/g, '\\"')}"
date: '${today}'
icon: 📄
---

`;
  const finalContent = frontmatter + processedContent;

  // 10. Write markdown file
  fs.mkdirSync(DOCS_DIR, { recursive: true });
  const mdPath = path.join(DOCS_DIR, `${slug}.md`);
  fs.writeFileSync(mdPath, finalContent, 'utf-8');
  console.log(`Written: ${mdPath}`);

  // 11. Extract images to public directory
  for (const imgEntry of imageEntries) {
    const filename = path.basename(imgEntry.entryName);
    const targetPath = path.join(imagesTargetDir, filename);
    fs.writeFileSync(targetPath, imgEntry.getData());
  }
  console.log(`Images: ${imageEntries.length} files -> ${imagesTargetDir}`);

  // 12. Git add, commit, push
  try {
    execSync('git add .', { cwd: PAGES_DIR, stdio: 'inherit' });
    execSync(`git commit -m "publish: ${title}"`, { cwd: PAGES_DIR, stdio: 'inherit' });
    execSync('git push', { cwd: PAGES_DIR, stdio: 'inherit' });
    console.log('Git push complete. GitHub Actions will deploy shortly.');
  } catch (err) {
    console.error('Git operation failed:', err.message);
    process.exit(1);
  }

  console.log('Done!');
}

main();
// @AI_GENERATED: end
