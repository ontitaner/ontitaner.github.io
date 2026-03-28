import { useState } from 'react';
import { useTabContext } from '@/lib/TabContext';
import { IconX, IconSplitRight, IconSplitLeft, IconDoc } from './Icons';

interface TabBarProps {
  panel: 'left' | 'right';
}

export default function TabBar({ panel }: TabBarProps) {
  const { tabs, activeLeft, activeRight, closeTab, setActive, moveToPanel, splitMode } = useTabContext();
  const panelTabs = tabs.filter(t => t.panel === panel);
  const activeSlug = panel === 'left' ? activeLeft : activeRight;
  const otherPanel = panel === 'left' ? 'right' : 'left';
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number; slug: string } | null>(null);

  const handleCtx = (e: React.MouseEvent, slug: string) => {
    e.preventDefault();
    setCtxMenu({ x: e.clientX, y: e.clientY, slug });
  };

  const closeOthers = (slug: string) => {
    panelTabs.filter(t => t.slug !== slug).forEach(t => closeTab(t.slug));
    setCtxMenu(null);
  };

  const closeRight = (slug: string) => {
    const idx = panelTabs.findIndex(t => t.slug === slug);
    panelTabs.slice(idx + 1).forEach(t => closeTab(t.slug));
    setCtxMenu(null);
  };

  const closeAll = () => {
    panelTabs.forEach(t => closeTab(t.slug));
    setCtxMenu(null);
  };

  if (panelTabs.length === 0) return null;

  return (
    <>
      <div className="tab-bar">
        {panelTabs.map(tab => (
          <div
            key={tab.slug}
            className={`tab-item ${tab.slug === activeSlug ? 'tab-active' : ''}`}
            onClick={() => setActive(tab.slug, panel)}
            onContextMenu={e => handleCtx(e, tab.slug)}
            draggable
            onDragStart={e => e.dataTransfer.setData('text/plain', tab.slug)}
          >
            <span className="tab-icon"><IconDoc size={13} /></span>
            <span className="tab-title">{tab.title}</span>
            <button className="tab-close" onClick={e => { e.stopPropagation(); closeTab(tab.slug); }}>
              <IconX size={11} />
            </button>
          </div>
        ))}
        <button
          className="tab-split-btn"
          title={splitMode ? `移到${otherPanel === 'left' ? '左' : '右'}侧` : '分屏查看'}
          onClick={() => { if (activeSlug) moveToPanel(activeSlug, otherPanel); }}
        >
          {panel === 'left' ? <IconSplitRight size={15} /> : <IconSplitLeft size={15} />}
        </button>
      </div>

      {ctxMenu && (
        <>
          <div className="tab-ctx-overlay" onClick={() => setCtxMenu(null)} />
          <div className="tab-ctx-menu" style={{ left: ctxMenu.x, top: ctxMenu.y }}>
            <button onClick={() => { closeTab(ctxMenu.slug); setCtxMenu(null); }}>关闭</button>
            <button onClick={() => closeOthers(ctxMenu.slug)}>关闭其他</button>
            <button onClick={() => closeRight(ctxMenu.slug)}>关闭右侧</button>
            <button onClick={closeAll}>关闭所有</button>
          </div>
        </>
      )}
    </>
  );
}
