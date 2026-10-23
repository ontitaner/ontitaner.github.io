// @AI_GENERATED
import { useState } from 'react';

// 沉浸阅读：切 body[data-immersive]，CSS 隐藏 sidebar/tab-bar/hamburger，内容铺满。
// 复用本仓已有的 body data-* 切换模式（见 Sidebar 的 data-sidebar）。
export default function ReadingMode() {
  const [on, setOn] = useState(false);

  const toggle = () => {
    const next = !on;
    document.body.setAttribute('data-immersive', next ? 'on' : 'off');
    setOn(next);
  };

  return (
    <button
      className={`export-btn ${on ? 'reading-on' : ''}`}
      onClick={toggle}
      title={on ? '退出沉浸阅读' : '沉浸阅读'}
      aria-label={on ? '退出沉浸阅读' : '沉浸阅读'}
    >
      {on ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 9L3 3m0 0v4m0-4h4M15 9l6-6m0 0v4m0-4h-4M9 15l-6 6m0 0v-4m0 4h4m11-4l-6 6m6 0v-4m0 4h-4"/></svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3M3 16v3a2 2 0 002 2h3m13-5v3a2 2 0 01-2 2h-3"/></svg>
      )}
    </button>
  );
}
