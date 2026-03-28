import { useState, useEffect, useCallback, useRef } from 'react';
import ParticleNetwork from './ParticleNetwork';

// SHA-256 hash of the password — change this to your own
// Default password: "techdocs" → hash below
const PASSWORD_HASH = '3d3220088ad12dc1dde47c9a226232f29bb5b9718eb71c169c2157469fd2340f'; // "ontitaner_ai"
const AUTH_KEY = 'auth-unlocked';

async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}

function IconLock({ size = 48 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0110 0v4" />
      <circle cx="12" cy="16" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}

function IconUnlock({ size = 48 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 019.9-1" />
      <circle cx="12" cy="16" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}

interface Props {
  children: React.ReactNode;
}

export default function LockScreen({ children }: Props) {
  const [unlocked, setUnlocked] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [shaking, setShaking] = useState(false);
  const [unlocking, setUnlocking] = useState(false);
  const [mounted, setMounted] = useState(false);
  const dosRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    setMounted(true);
    if (sessionStorage.getItem(AUTH_KEY) === 'true') {
      setUnlocked(true);
    }
  }, []);

  // DOS typing effect — uses ref to avoid re-renders
  useEffect(() => {
    if (!mounted || unlocked) return;
    const el = dosRef.current;
    if (!el) return;

    const startDate = new Date('2017-06-02');
    const now = new Date();
    const days = Math.floor((now.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
    const lines = [
      '> SYSTEM ONLINE',
      `> UPTIME: ${days} DAYS`,
    ];

    let lineIdx = 0;
    let charIdx = 0;
    let output = '';
    let blinkId: NodeJS.Timeout;

    const typingTimer = setInterval(() => {
      if (lineIdx >= lines.length) { clearInterval(typingTimer); return; }
      const line = lines[lineIdx];
      if (charIdx <= line.length) {
        el.textContent = output + line.slice(0, charIdx) + '█';
        charIdx++;
      } else {
        output += line + '\n';
        lineIdx++;
        charIdx = 0;
      }
    }, 25);

    // Show hero text + start cursor blink after typing
    const totalTime = lines.join('').length * 25 + 500;

    const heroEl = el.parentElement?.querySelector('.lock-dos-hero') as HTMLElement | null;
    const afterTimer = setTimeout(() => {
      clearInterval(typingTimer);
      if (heroEl) {
        heroEl.innerHTML = `未被AI替代的第 <span class="lock-dos-number">${days}</span> 天`;
        heroEl.style.opacity = '1';
        heroEl.style.transform = 'translateY(0)';
      }
      let visible = true;
      blinkId = setInterval(() => {
        visible = !visible;
        const text = el.textContent || '';
        if (visible && !text.endsWith('█')) el.textContent = text + '█';
        else if (!visible && text.endsWith('█')) el.textContent = text.slice(0, -1);
      }, 530);
    }, totalTime);

    return () => { clearInterval(typingTimer); clearTimeout(afterTimer); clearInterval(blinkId); };
  }, [mounted, unlocked]);

  // Listen for lock event from sidebar
  useEffect(() => {
    const handler = () => {
      sessionStorage.removeItem(AUTH_KEY);
      setUnlocked(false);
      setPassword('');
      setUnlocking(false);
      setError('');
    };
    window.addEventListener('lock-screen', handler);
    return () => window.removeEventListener('lock-screen', handler);
  }, []);

  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus input when lock screen shows
  useEffect(() => {
    if (mounted && !unlocked) {
      setTimeout(() => inputRef.current?.focus(), 600);
    }
  }, [mounted, unlocked]);

  const handleSubmit = useCallback(async () => {
    if (!password.trim()) {
      setError('请输入密码');
      setShaking(true);
      setTimeout(() => { setShaking(false); inputRef.current?.focus(); }, 500);
      return;
    }
    const hash = await sha256(password);
    if (hash === PASSWORD_HASH) {
      setUnlocking(true);
      setError('');
      setTimeout(() => {
        sessionStorage.setItem(AUTH_KEY, 'true');
        setUnlocked(true);
      }, 800);
    } else {
      setError('密码错误，请重试');
      setShaking(true);
      setTimeout(() => { setShaking(false); inputRef.current?.focus(); }, 500);
      setPassword('');
    }
  }, [password]);

  if (!mounted) return null;
  if (unlocked) return <>{children}</>;

  return (
    <div className="lock-screen">
      <ParticleNetwork />

      <div className="lock-dos-bg">
        <pre className="lock-dos-text" ref={dosRef}></pre>
        <div className="lock-dos-hero"></div>
      </div>

      <div className={`lock-card ${unlocking ? 'lock-unlocking' : ''}`}>
        <div className={shaking ? 'lock-shake' : ''}>
        <div className={`lock-icon ${unlocking ? 'lock-icon-open' : ''}`}>
          {unlocking ? <IconUnlock size={40} /> : <IconLock size={40} />}
        </div>

        <h1 className="lock-title">Tech Docs</h1>
        <p className="lock-subtitle">请输入访问密码</p>

        <div className="lock-input-wrap">
          <input
            ref={inputRef}
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={e => { setPassword(e.target.value); setError(''); }}
            onKeyDown={e => { if (e.key === 'Enter') handleSubmit(); }}
            className={error ? 'lock-input-error' : ''}
          />
        </div>

        {error && <div className="lock-error">{error}</div>}

        <button className="lock-btn" onClick={handleSubmit} disabled={unlocking}>
          {unlocking ? '验证通过...' : '解锁'}
        </button>

        <div className="lock-hint">提示：关闭浏览器标签页后需重新验证</div>
        </div>
      </div>
    </div>
  );
}
