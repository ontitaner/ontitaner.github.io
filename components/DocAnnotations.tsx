import { useState, useEffect, useCallback, useRef } from 'react';
import { useAnnotations, Annotation } from '@/lib/AnnotationContext';
import { IconAnnotation, IconTrash } from './Icons';

function IconEdit({ size = 13 }: { size?: number }) {
  const s = { display: 'inline-block', verticalAlign: 'middle', fill: 'none', stroke: 'currentColor' } as const;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={s} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  );
}

interface Props {
  slug: string;
  scrollRef: React.RefObject<HTMLDivElement>;
}

export default function DocAnnotations({ slug, scrollRef }: Props) {
  const { getAnnotations, addAnnotation, removeAnnotation, updateAnnotation } = useAnnotations();
  const annotations = getAnnotations(slug);

  const [menu, setMenu] = useState<{ x: number; y: number; posY: number } | null>(null);
  const [newEditor, setNewEditor] = useState<{ posY: number } | null>(null);
  const [note, setNote] = useState('');
  // openId: which annotation card is open (click to toggle)
  const [openId, setOpenId] = useState<string | null>(null);
  // editing: which annotation is in edit mode
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const newRef = useRef<HTMLTextAreaElement>(null);
  const editRef = useRef<HTMLTextAreaElement>(null);

  // Right-click
  const handleContextMenu = useCallback((e: MouseEvent) => {
    const el = scrollRef.current;
    if (!el) return;
    const target = e.target as HTMLElement;
    if (!target.closest('.doc-content')) return;
    e.preventDefault();
    const rect = el.getBoundingClientRect();
    const posY = e.clientY - rect.top + el.scrollTop;
    setMenu({ x: e.clientX - rect.left, y: posY, posY });
  }, [scrollRef]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener('contextmenu', handleContextMenu);
    return () => el.removeEventListener('contextmenu', handleContextMenu);
  }, [scrollRef, handleContextMenu]);

  // Close menu on any click
  useEffect(() => {
    if (!menu) return;
    const close = () => setMenu(null);
    window.addEventListener('click', close);
    return () => window.removeEventListener('click', close);
  }, [menu]);

  // Close open card when clicking outside
  useEffect(() => {
    if (!openId && !editingId) return;
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.closest('.anno-marker')) return; // clicking inside a marker
      setOpenId(null);
      setEditingId(null);
    };
    window.addEventListener('mousedown', handleClick);
    return () => window.removeEventListener('mousedown', handleClick);
  }, [openId, editingId]);

  const startNew = () => {
    if (!menu) return;
    setNewEditor({ posY: menu.posY });
    setNote('');
    setMenu(null);
    setOpenId(null);
    setEditingId(null);
    setTimeout(() => newRef.current?.focus(), 50);
  };

  const saveNew = () => {
    if (note.trim() && newEditor) {
      addAnnotation(slug, note.trim(), newEditor.posY);
    }
    setNewEditor(null);
    setNote('');
  };

  const toggleOpen = (id: string) => {
    if (editingId) return; // don't toggle while editing
    setOpenId(prev => prev === id ? null : id);
    setEditingId(null);
  };

  const startEdit = (a: Annotation) => {
    setEditingId(a.id);
    setEditText(a.note);
    setOpenId(a.id); // keep card open
    setTimeout(() => editRef.current?.focus(), 50);
  };

  const saveEdit = () => {
    if (editingId && editText.trim()) {
      updateAnnotation(editingId, editText.trim());
    }
    setEditingId(null);
    // keep card open to see result
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditText('');
  };

  const handleDelete = (id: string) => {
    removeAnnotation(id);
    setOpenId(null);
    setEditingId(null);
  };

  return (
    <>
      {annotations.map(a => {
        const isOpen = openId === a.id;
        const isEditing = editingId === a.id;

        return (
          <div key={a.id} className="anno-marker" style={{ top: a.posY }}>
            {/* Pin */}
            <div
              className={`anno-pin ${isOpen ? 'anno-pin-active' : ''}`}
              onClick={() => toggleOpen(a.id)}
            >
              <IconAnnotation size={12} />
            </div>

            {/* Card: view or edit mode */}
            {isOpen && (
              <div className="anno-card" onClick={e => e.stopPropagation()}>
                {isEditing ? (
                  <>
                    <textarea
                      ref={editRef}
                      rows={3}
                      value={editText}
                      onChange={e => setEditText(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) saveEdit(); if (e.key === 'Escape') cancelEdit(); }}
                    />
                    <div className="anno-card-actions">
                      <button className="anno-cancel" onClick={cancelEdit}>取消</button>
                      <button className="anno-save" onClick={saveEdit}>保存</button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="anno-card-note">{a.note}</div>
                    <div className="anno-card-actions">
                      <span className="anno-card-time">
                        {new Date(a.createdAt).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </span>
                      <div className="anno-card-btns">
                        <button className="anno-btn anno-btn-edit" onClick={() => startEdit(a)} title="编辑">
                          <IconEdit size={12} />
                        </button>
                        <button className="anno-btn anno-btn-del" onClick={() => handleDelete(a.id)} title="删除">
                          <IconTrash size={12} />
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        );
      })}

      {/* Context menu */}
      {menu && (
        <div className="anno-ctx-menu" style={{ left: menu.x, top: menu.y }}>
          <button className="anno-ctx-item" onClick={startNew}>
            <IconAnnotation size={14} />
            <span>添加批注</span>
          </button>
        </div>
      )}

      {/* New annotation editor */}
      {newEditor && (
        <div className="anno-marker" style={{ top: newEditor.posY }}>
          <div className="anno-pin anno-pin-new"><IconAnnotation size={12} /></div>
          <div className="anno-card anno-card-editing" onClick={e => e.stopPropagation()}>
            <textarea
              ref={newRef}
              rows={3}
              placeholder="写下批注... (Ctrl+Enter 保存)"
              value={note}
              onChange={e => setNote(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) saveNew(); if (e.key === 'Escape') setNewEditor(null); }}
            />
            <div className="anno-card-actions">
              <button className="anno-cancel" onClick={() => setNewEditor(null)}>取消</button>
              <button className="anno-save" onClick={saveNew}>保存</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
