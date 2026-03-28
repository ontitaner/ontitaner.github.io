import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export interface Tab {
  slug: string;
  title: string;
  panel: 'left' | 'right';
}

interface TabContextType {
  tabs: Tab[];
  activeLeft: string | null;
  activeRight: string | null;
  splitMode: boolean;
  openTab: (slug: string, title: string, panel?: 'left' | 'right') => void;
  closeTab: (slug: string) => void;
  setActive: (slug: string, panel: 'left' | 'right') => void;
  moveToPanel: (slug: string, panel: 'left' | 'right') => void;
  toggleSplit: () => void;
}

const TabContext = createContext<TabContextType>(null!);

export function useTabContext() {
  return useContext(TabContext);
}

export function TabProvider({ children }: { children: ReactNode }) {
  const [tabs, setTabs] = useState<Tab[]>([]);
  const [activeLeft, setActiveLeft] = useState<string | null>(null);
  const [activeRight, setActiveRight] = useState<string | null>(null);
  const [splitMode, setSplitMode] = useState(false);

  const openTab = useCallback((slug: string, title: string, panel: 'left' | 'right' = 'left') => {
    setTabs(prev => {
      const exists = prev.find(t => t.slug === slug);
      if (exists) {
        // Already open, just activate it
        if (exists.panel === 'left') setActiveLeft(slug);
        else setActiveRight(slug);
        return prev;
      }
      return [...prev, { slug, title, panel }];
    });
    if (panel === 'left') setActiveLeft(slug);
    else {
      setActiveRight(slug);
      setSplitMode(true);
    }
  }, []);

  const closeTab = useCallback((slug: string) => {
    setTabs(prev => {
      const remaining = prev.filter(t => t.slug !== slug);
      const closed = prev.find(t => t.slug === slug);
      if (closed) {
        const samePanelTabs = remaining.filter(t => t.panel === closed.panel);
        if (closed.panel === 'left') {
          setActiveLeft(samePanelTabs.length > 0 ? samePanelTabs[samePanelTabs.length - 1].slug : null);
        } else {
          if (samePanelTabs.length === 0) {
            setSplitMode(false);
            setActiveRight(null);
          } else {
            setActiveRight(samePanelTabs[samePanelTabs.length - 1].slug);
          }
        }
      }
      return remaining;
    });
  }, []);

  const setActive = useCallback((slug: string, panel: 'left' | 'right') => {
    if (panel === 'left') setActiveLeft(slug);
    else setActiveRight(slug);
  }, []);

  const moveToPanel = useCallback((slug: string, panel: 'left' | 'right') => {
    const sourcePanel = panel === 'right' ? 'left' : 'right';

    setTabs(prev => {
      const updated = prev.map(t => t.slug === slug ? { ...t, panel } : t);
      const remainingInSource = updated.filter(t => t.panel === sourcePanel);

      // Fix source panel active
      if (sourcePanel === 'left') {
        setActiveLeft(cur => cur === slug ? (remainingInSource.length > 0 ? remainingInSource[remainingInSource.length - 1].slug : null) : cur);
      } else {
        setActiveRight(cur => {
          if (cur === slug) {
            if (remainingInSource.length === 0) { setSplitMode(false); return null; }
            return remainingInSource[remainingInSource.length - 1].slug;
          }
          return cur;
        });
      }

      return updated;
    });

    // Set target panel active
    if (panel === 'left') setActiveLeft(slug);
    else { setActiveRight(slug); setSplitMode(true); }
  }, []);

  const toggleSplit = useCallback(() => {
    setSplitMode(prev => {
      if (prev) {
        // Merge right tabs to left
        setTabs(ts => ts.map(t => ({ ...t, panel: 'left' as const })));
        setActiveRight(null);
      }
      return !prev;
    });
  }, []);

  return (
    <TabContext.Provider value={{ tabs, activeLeft, activeRight, splitMode, openTab, closeTab, setActive, moveToPanel, toggleSplit }}>
      {children}
    </TabContext.Provider>
  );
}
