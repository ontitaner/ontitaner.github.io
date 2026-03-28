import { useEffect, useRef, useState } from 'react';

interface MermaidProps {
  chart: string;
}

function getTheme(): 'dark' | 'default' {
  if (typeof document === 'undefined') return 'dark';
  return document.documentElement.getAttribute('data-theme') === 'light' ? 'default' : 'dark';
}

function getThemeVars(isDark: boolean) {
  return isDark ? {
    primaryColor: '#1f6feb',
    primaryTextColor: '#e6edf3',
    primaryBorderColor: '#30363d',
    lineColor: '#8b949e',
    secondaryColor: '#161b22',
    tertiaryColor: '#1c2128',
    noteBkgColor: '#161b22',
    noteTextColor: '#e6edf3',
  } : {
    primaryColor: '#0969da',
    primaryTextColor: '#1b1f24',
    primaryBorderColor: '#d0d7de',
    lineColor: '#59636e',
    secondaryColor: '#f6f8fa',
    tertiaryColor: '#eef1f5',
    noteBkgColor: '#f6f8fa',
    noteTextColor: '#1b1f24',
  };
}

export default function Mermaid({ chart }: MermaidProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState('');

  useEffect(() => {
    let cancelled = false;

    const render = () => {
      import('mermaid').then((m) => {
        const mermaid = m.default;
        const isDark = getTheme() === 'dark';
        mermaid.initialize({
          startOnLoad: false,
          theme: isDark ? 'dark' : 'default',
          themeVariables: getThemeVars(isDark),
        });
        const id = 'mermaid-' + Math.random().toString(36).slice(2, 9);
        mermaid.render(id, chart).then(({ svg }) => {
          if (!cancelled) setSvg(svg);
        });
      });
    };

    render();

    // Re-render when theme changes
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.attributeName === 'data-theme') { render(); break; }
      }
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

    return () => { cancelled = true; observer.disconnect(); };
  }, [chart]);

  return (
    <div className="mermaid-wrapper">
      <div ref={ref} dangerouslySetInnerHTML={{ __html: svg }} />
    </div>
  );
}
