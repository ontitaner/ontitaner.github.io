import { useState, useEffect, RefObject } from 'react';

export default function ReadingProgress({ scrollRef }: { scrollRef: RefObject<HTMLDivElement> }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = el;
      const max = scrollHeight - clientHeight;
      setProgress(max > 0 ? (scrollTop / max) * 100 : 0);
    };
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, [scrollRef]);

  return <div className="reading-progress" style={{ width: `${progress}%` }} />;
}
