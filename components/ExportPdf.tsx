import { RefObject } from 'react';

function IconDownload({ size = 14 }: { size?: number }) {
  const s = { display: 'inline-block', verticalAlign: 'middle', fill: 'none', stroke: 'currentColor' } as const;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={s} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

interface Props {
  title: string;
  scrollRef: RefObject<HTMLDivElement>;
}

export default function ExportPdf({ title, scrollRef }: Props) {
  const handleExport = () => {
    const el = scrollRef.current;
    if (!el) return;

    // Clone the content to avoid modifying the original
    const clone = el.cloneNode(true) as HTMLElement;

    // Remove UI elements that shouldn't be in PDF
    const removeSelectors = [
      '.tag-editor', '.copy-btn', '.anno-marker', '.anno-pin',
      '.anno-card', '.anno-ctx-menu', '.scroll-top-btn',
      '.doc-date', '.export-btn', '.reading-progress', '.toc', '.toc-toggle',
      '.doc-header', '.doc-nav', '.heading-anchor', '.code-lang-label',
      '.anno-card-editing', '.anno-pin-new'
    ];
    removeSelectors.forEach(sel => {
      clone.querySelectorAll(sel).forEach(node => node.remove());
    });

    // Get all Mermaid SVGs and inline their content
    clone.querySelectorAll('.mermaid-wrapper').forEach(wrapper => {
      const svg = wrapper.querySelector('svg');
      if (svg) {
        // Keep the SVG with explicit dimensions
        const w = svg.getAttribute('width') || svg.style.width || '100%';
        svg.setAttribute('width', '100%');
        svg.style.maxWidth = '700px';
        svg.style.height = 'auto';
        // Replace wrapper with just the SVG
        const div = document.createElement('div');
        div.style.margin = '16px 0';
        div.style.textAlign = 'center';
        div.appendChild(svg.cloneNode(true));
        wrapper.replaceWith(div);
      }
    });

    const content = `<h1>${title}</h1>` + clone.innerHTML;

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    printWindow.document.write(`<!DOCTYPE html>
<html><head><title>${title}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 40px 50px;
    color: #1a1a1a;
    line-height: 1.8;
    max-width: 850px;
    margin: 0 auto;
  }
  h1 { font-size: 1.8em; border-bottom: 2px solid #e1e4e8; padding-bottom: 10px; margin-bottom: 20px; }
  h2 { font-size: 1.4em; margin-top: 28px; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 6px; }
  h3 { font-size: 1.15em; margin-top: 20px; margin-bottom: 8px; }
  p { margin-bottom: 12px; }
  ul, ol { margin-bottom: 12px; padding-left: 24px; }
  li { margin-bottom: 4px; }
  pre {
    background: #f6f8fa;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 14px;
    overflow-x: auto;
    font-size: 12px;
    margin-bottom: 14px;
    white-space: pre-wrap;
    word-break: break-all;
  }
  code { background: #f0f2f5; padding: 2px 5px; border-radius: 3px; font-size: 0.88em; font-family: Consolas, monospace; }
  pre code { background: none; padding: 0; font-size: 1em; }
  table { border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 0.9em; }
  th, td { border: 1px solid #d0d7de; padding: 8px 10px; text-align: left; }
  th { background: #f6f8fa; font-weight: 600; }
  blockquote { border-left: 4px solid #0969da; padding: 10px 16px; margin: 14px 0; background: #f6f8fa; border-radius: 0 6px 6px 0; }
  blockquote p { margin-bottom: 0; }
  img { max-width: 100%; }
  hr { border: none; height: 1px; background: #e1e4e8; margin: 20px 0; }
  svg { max-width: 100%; height: auto; }
  del { color: #888; }
  input[type="checkbox"] { margin-right: 6px; }
  @media print {
    body { padding: 20px; }
    pre { white-space: pre-wrap; word-break: break-all; }
  }
</style>
</head><body>${content}</body></html>`);

    printWindow.document.close();
    setTimeout(() => printWindow.print(), 600);
  };

  return (
    <button className="export-btn" onClick={handleExport} title="导出 PDF">
      <IconDownload size={14} />
    </button>
  );
}
