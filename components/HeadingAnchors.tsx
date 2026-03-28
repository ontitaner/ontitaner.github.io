import { useEffect, RefObject } from 'react';

export default function HeadingAnchors({ containerRef }: { containerRef: RefObject<HTMLDivElement> }) {
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const addAnchors = () => {
      el.querySelectorAll('h2, h3').forEach((h, i) => {
        if (h.querySelector('.heading-anchor')) return;
        const id = h.id || `heading-${i}`;
        if (!h.id) h.id = id;
        (h as HTMLElement).style.position = 'relative';
        const link = document.createElement('a');
        link.className = 'heading-anchor';
        link.href = `#${id}`;
        link.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>';
        link.onclick = (e) => {
          e.preventDefault();
          navigator.clipboard.writeText(window.location.origin + window.location.pathname + `#${id}`);
          link.classList.add('heading-anchor-copied');
          setTimeout(() => link.classList.remove('heading-anchor-copied'), 1500);
        };
        h.appendChild(link);
      });
    };

    const timer = setTimeout(addAnchors, 400);
    return () => clearTimeout(timer);
  }, [containerRef]);

  return null;
}
