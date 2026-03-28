import { useEffect, RefObject } from 'react';

export default function CodeLangLabel({ containerRef }: { containerRef: RefObject<HTMLDivElement> }) {
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const addLabels = () => {
      el.querySelectorAll('pre code').forEach(code => {
        const pre = code.parentElement;
        if (!pre || pre.querySelector('.code-lang-label')) return;
        // Extract language from class like "hljs language-python"
        const cls = Array.from(code.classList).find(c => c.startsWith('language-'));
        if (!cls) return;
        const lang = cls.replace('language-', '').toUpperCase();
        const label = document.createElement('span');
        label.className = 'code-lang-label';
        label.textContent = lang;
        pre.appendChild(label);
      });
    };

    const timer = setTimeout(addLabels, 300);
    const observer = new MutationObserver(addLabels);
    observer.observe(el, { childList: true, subtree: true });
    return () => { clearTimeout(timer); observer.disconnect(); };
  }, [containerRef]);

  return null;
}
