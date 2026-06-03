'use client';

import { motion } from 'motion/react';

interface SpinnerProps {
  size?: number;
  className?: string;
  label?: string;
}

/** Clay-styled loading spinner with a soft track + brand arc. */
export function Spinner({ size = 28, className, label = 'Loading' }: SpinnerProps) {
  return (
    <span role="status" aria-label={label} className={className} style={{ display: 'inline-flex' }}>
      <motion.svg
        width={size}
        height={size}
        viewBox="0 0 50 50"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, ease: 'linear', duration: 0.9 }}
      >
        <circle cx="25" cy="25" r="20" fill="none" stroke="var(--muted)" strokeWidth="6" />
        <circle
          cx="25"
          cy="25"
          r="20"
          fill="none"
          stroke="var(--primary)"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray="90 150"
        />
      </motion.svg>
    </span>
  );
}
