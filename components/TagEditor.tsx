import { useState, useRef } from 'react';
import { useTagContext } from '@/lib/TagContext';
import { IconX, IconPlus, IconTag } from './Icons';

export default function TagEditor({ slug }: { slug: string }) {
  const { getTags, addTag, removeTag, allTags } = useTagContext();
  const tags = getTags(slug);
  const [input, setInput] = useState('');
  const [showSuggest, setShowSuggest] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const suggestions = allTags.filter(
    t => !tags.includes(t) && t.toLowerCase().includes(input.toLowerCase())
  );

  const handleAdd = (tag: string) => {
    const t = tag.trim();
    if (!t) return;
    addTag(slug, t);
    setInput('');
    setShowSuggest(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && input.trim()) {
      e.preventDefault();
      handleAdd(input);
    }
  };

  return (
    <div className="tag-editor">
      <div className="tag-editor-tags">
        {tags.map(t => (
          <span key={t} className="tag-pill">
            <IconTag size={11} />
            {t}
            <button onClick={() => removeTag(slug, t)}><IconX size={10} /></button>
          </span>
        ))}
        <div className="tag-input-wrap">
          <span className="tag-input-icon"><IconPlus size={11} /></span>
          <input
            ref={inputRef}
            type="text"
            value={input}
            placeholder="添加标签"
            onChange={e => { setInput(e.target.value); setShowSuggest(true); }}
            onFocus={() => setShowSuggest(true)}
            onBlur={() => setTimeout(() => setShowSuggest(false), 150)}
            onKeyDown={handleKeyDown}
          />
          {showSuggest && input && suggestions.length > 0 && (
            <div className="tag-suggest">
              {suggestions.slice(0, 6).map(s => (
                <div key={s} className="tag-suggest-item" onMouseDown={() => handleAdd(s)}>
                  <IconTag size={11} /> {s}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
