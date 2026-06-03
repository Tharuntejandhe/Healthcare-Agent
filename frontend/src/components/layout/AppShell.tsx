'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Menu, X } from 'lucide-react';
import { Sidebar } from './Sidebar';
import { DisclaimerBanner } from './DisclaimerBanner';
import { Logo } from '@/components/ui/Logo';
import { IconButton } from '@/components/ui/IconButton';
import { IdleTimeout } from '@/components/providers/IdleTimeout';
import { overlayFade } from '@/lib/motion';
import styles from './AppShell.module.css';

interface AppShellProps {
  children: React.ReactNode;
}

/** Responsive authenticated layout: clay sidebar rail on desktop, drawer on mobile. */
export function AppShell({ children }: AppShellProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className={styles.shell}>
      {/* Auto-logoff on inactivity (HIPAA-aligned automatic logoff). */}
      <IdleTimeout />

      {/* Desktop sidebar */}
      <aside className={styles.sidebar}>
        <Sidebar />
      </aside>

      {/* Mobile top bar */}
      <header className={styles.mobileBar}>
        <Logo size="sm" />
        <IconButton aria-label="Open menu" onClick={() => setOpen(true)}>
          <Menu size={20} />
        </IconButton>
      </header>

      {/* Mobile drawer */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              className={styles.scrim}
              variants={overlayFade}
              initial="hidden"
              animate="show"
              exit="exit"
              onClick={() => setOpen(false)}
            />
            <motion.aside
              className={styles.drawer}
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', stiffness: 320, damping: 34 }}
            >
              <div className={styles.drawerClose}>
                <IconButton aria-label="Close menu" onClick={() => setOpen(false)} variant="ghost">
                  <X size={20} />
                </IconButton>
              </div>
              <Sidebar onNavigate={() => setOpen(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <main className={styles.main}>
        {children}
        <DisclaimerBanner />
      </main>
    </div>
  );
}
