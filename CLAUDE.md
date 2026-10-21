# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev       # Start dev server (run manually, do not use via tool)
npm run build     # Build for production (outputs to /out for static export)
npm ci            # Install dependencies
```

No test suite is configured. TypeScript type checking: `npx tsc --noEmit`.

## Architecture

This is a **Next.js 14 static-export docs site** deployed to GitHub Pages via `.github/workflows/deploy.yml`. `next.config.mjs` sets `output: 'export'`, so all pages are pre-rendered to `/out`.

### Data flow

- Docs live under `/public/collections/<collection>/`. One subdirectory = one collection. `lib/markdown.ts` recursively scans it at build time with `gray-matter` + `unified` (remark → rehype pipeline with syntax highlighting). The slug is the path relative to `collections` without `.md` (e.g. `ems-python-learning/00_导读`); the title is the filename; sidebar order is filename-ascending within a collection. Source `.md` need no frontmatter.
- Images/attachments sit beside the `.md` inside the collection folder and are served from `/public`. Source markdown keeps relative links (`img/x.png`) so local-editor preview works; at build time `rewriteRelativeSrc` in `lib/markdown.ts` rewrites `<img src>` to the absolute `/collections/<dir>/...` path (the SPA injects HTML at URL `/`, so relatives would otherwise break). `.md` cross-links are left untouched — they work in a local editor, dead on the site.
- A collection may add an optional `collection.json` (`{ "name", "order" }`) to set its display name and inter-collection order; absent, it falls back to the directory name and 999.
- Adding a new collection = drop a folder into `/public/collections/`; no code or config change. `scripts/publish.mjs` (WeChat ZIP → `/docs`) is now an orphaned pipeline — the renderer only scans `/public/collections/`.
- Mermaid diagrams are extracted before the remark pipeline, stored as `mermaidBlocks[]`, and re-injected client-side via `MERMAID_PLACEHOLDER_N` markers. The `Mermaid` component is dynamically imported (`ssr: false`).
- `getStaticProps` in `pages/index.tsx` pre-builds all docs into `allDocs: Record<slug, DocData>` and passes them as props — no runtime file I/O.

### Context providers (in `_app.tsx` nesting order)

| Provider | File | Responsibility |
|---|---|---|
| `ThemeProvider` | `lib/ThemeContext.tsx` | Dark/light theme |
| `SyncProvider` | `lib/SyncContext.tsx` | GitHub Gist sync (pull/push annotations+tags) |
| `AnnotationProvider` | `lib/AnnotationContext.tsx` | Per-doc annotations stored in `localStorage` |
| `TagProvider` | `lib/TagContext.tsx` | User-defined tags per doc, stored in `localStorage` |
| `TabProvider` | `lib/TabContext.tsx` | Open tabs, active tab per panel, split-screen state |

### Tab / split-screen model

`TabContext` manages two panels (`left` / `right`). Each tab has a `panel` assignment. `splitMode` is true when any right-panel tab exists. Tabs can be dragged between panels via HTML5 drag-and-drop in `DocPanel`.

### Sync

`lib/gistSync.ts` syncs annotations and tags to a private GitHub Gist using a personal access token stored in `localStorage`. `SyncContext` auto-syncs on login and every 60 s, with a 2 s debounce on local changes. Merge strategy: remote wins on conflict, local-only items are preserved.

### Lock screen

`components/LockScreen.tsx` wraps the entire app. Auth state is stored in `sessionStorage` (cleared on tab close). Password is verified client-side via SHA-256 against a hardcoded hash (`PASSWORD_HASH`). To change the password, update the hash in that file.

### Site config

`site.config.ts` — change `title` and `icon` here to rebrand the site.

### Collections (authoring convention)

Source `.md` need no frontmatter — title = filename, sidebar order = filename-ascending within the collection. Use a sortable filename prefix (`00_`, `01_`, …) to control order. Files/dirs starting with `_` are not published.

```
public/collections/<collection>/
├── 00_intro.md          # title "00_intro", shown first
├── 01_foo.md
├── img/…                # relative img/ links in the md resolve here on-site
├── lab/ figures/…       # any other assets, published as downloadable files
└── collection.json      # optional: { "name": "显示名", "order": 10 }
```

Internal `.md` cross-links are left as-is: they work in a local editor but are dead on the published site (by design — the site is a tab SPA, not per-doc URLs).
