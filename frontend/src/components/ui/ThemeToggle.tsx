'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Moon, Sun } from 'lucide-react';
import { springClay } from '@/lib/motion';

const baseStyle: React.CSSProperties = {
  width: 42,
  height: 42,
  borderRadius: 9999,
  background: 'var(--card)',
  color: 'var(--foreground)',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  cursor: 'pointer',
  border: 'none',
  boxShadow: 'var(--shadow-clay-sm)',
  overflow: 'hidden',
};

export function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const saved = (localStorage.getItem('theme') as 'light' | 'dark' | null) ?? null;
    const initial: 'light' | 'dark' =
      saved ?? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    setTheme(initial);
    document.documentElement.classList.toggle('dark', initial === 'dark');
    setMounted(true);
  }, []);

  const toggle = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    localStorage.setItem('theme', next);
    document.documentElement.classList.toggle('dark', next === 'dark');
  };

  if (!mounted) {
    return <button type="button" aria-label="Toggle theme" style={baseStyle} />;
  }

  return (
    <motion.button
      type="button"
      aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
      onClick={toggle}
      style={baseStyle}
      whileHover={{ scale: 1.08, boxShadow: 'var(--shadow-clay)' }}
      whileTap={{ scale: 0.9 }}
      transition={springClay}
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={theme}
          initial={{ y: 18, opacity: 0, rotate: -40 }}
          animate={{ y: 0, opacity: 1, rotate: 0 }}
          exit={{ y: -18, opacity: 0, rotate: 40 }}
          transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
          style={{ display: 'inline-flex' }}
        >
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </motion.span>
      </AnimatePresence>
    </motion.button>
  );
}
