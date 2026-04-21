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

- Docs are `.md` files in `/docs/`. `lib/markdown.ts` reads them at build time with `gray-matter` + `unified` (remark → rehype pipeline with syntax highlighting).
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

### Doc frontmatter

```yaml
---
title: My Doc
order: 1        # sidebar sort order (default 999)
date: 2024-01-01
icon: 🚀        # optional emoji shown in sidebar
---
```

Internal doc links use `./slug` or `./slug.md` syntax and are intercepted client-side to open as tabs instead of navigating.
