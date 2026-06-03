'use client';

import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { getToken, logout } from '@/lib/auth';

/**
 * Automatic logoff after a period of inactivity.
 *
 * Health apps are expected to terminate an idle session (HIPAA Technical
 * Safeguard §164.312(a)(2)(iii)). On timeout we revoke the token server-side
 * and bounce to /login, so an unattended/shared device can't be used later.
 */
export function IdleTimeout({ timeoutMs = 15 * 60 * 1000 }: { timeoutMs?: number }) {
  const router = useRouter();
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const signOut = async () => {
      if (!getToken()) return;
      await logout();
      toast('Signed out', { description: 'You were logged out due to inactivity.' });
      router.push('/login');
    };

    const reset = () => {
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(signOut, timeoutMs);
    };

    const events = ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart', 'visibilitychange'];
    events.forEach((e) => window.addEventListener(e, reset, { passive: true }));
    reset();

    return () => {
      if (timer.current) clearTimeout(timer.current);
      events.forEach((e) => window.removeEventListener(e, reset));
    };
  }, [router, timeoutMs]);

  return null;
}
