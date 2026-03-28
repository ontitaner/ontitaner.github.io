import { useEffect, RefObject } from 'react';

export default function CodeCopy({ containerRef }: { containerRef: RefObject<HTMLDivElement> }) {
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const addButtons = () => {
      el.querySelectorAll('pre').forEach(pre => {
        if (pre.querySelector('.copy-btn')) return;
        const btn = document.createElement('button');
        btn.className = 'copy-btn';
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>';
        btn.onclick = () => {
          const code = pre.querySelector('code');
          if (code) {
            navigator.clipboard.writeText(code.textContent || '');
            btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
            setTimeout(() => {
              btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>';
            }, 1500);
          }
        };
        pre.style.position = 'relative';
        pre.appendChild(btn);
      });
    };

    const timer = setTimeout(addButtons, 200);
    const observer = new MutationObserver(addButtons);
    observer.observe(el, { childList: true, subtree: true });
    return () => { clearTimeout(timer); observer.disconnect(); };
  }, [containerRef]);

  return null;
}
