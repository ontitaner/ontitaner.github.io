import { useState, useEffect, RefObject } from 'react';
import { IconArrowUp } from './Icons';

interface Props {
  scrollRef: RefObject<HTMLDivElement>;
}

export default function ScrollToTop({ scrollRef }: Props) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => setVisible(el.scrollTop > 400);
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, [scrollRef]);

  if (!visible) return null;

  return (
    <button
      className="scroll-top-btn"
      onClick={() => scrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' })}
      aria-label="回到顶部"
    >
      <IconArrowUp size={20} />
    </button>
  );
}
