'use client';

import { MotionConfig } from 'motion/react';

/**
 * App-wide motion settings. reducedMotion="user" makes every motion component
 * respect the OS "reduce motion" setting — disabling transform/layout
 * animations (incl. infinite scale/translate loops) for those users, while the
 * CSS @media block in globals.css covers CSS transitions.
 */
export function MotionProvider({ children }: { children: React.ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}
