'use client';

import { useEffect, useState } from 'react';
import { Toaster as SonnerToaster } from 'sonner';

/** App-wide toast surface, clay-styled and theme-aware. */
export function Toaster() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const sync = () => setTheme(document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  return (
    <SonnerToaster
      theme={theme}
      position="top-center"
      richColors
      toastOptions={{
        style: {
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-clay)',
          border: 'none',
          background: 'var(--card)',
          color: 'var(--foreground)',
        },
      }}
    />
  );
}
