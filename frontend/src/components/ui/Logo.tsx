'use client';

import Link from 'next/link';
import { motion } from 'motion/react';
import { Activity } from 'lucide-react';
import { cn } from '@/lib/cn';
import { springClay } from '@/lib/motion';
import styles from './Logo.module.css';

interface LogoProps {
  href?: string;
  withWordmark?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Logo({ href = '/', withWordmark = true, size = 'md', className }: LogoProps) {
  const mark = (
    <motion.span
      className={cn(styles.mark, styles[size])}
      whileHover={{ rotate: -8, scale: 1.06 }}
      transition={springClay}
      aria-hidden="true"
    >
      <Activity strokeWidth={2.5} />
    </motion.span>
  );

  const content = (
    <span className={cn(styles.logo, className)}>
      {mark}
      {withWordmark && <span className={cn(styles.word, styles[`word_${size}`])}>MediHealth</span>}
    </span>
  );

  if (href) {
    return (
      <Link href={href} aria-label="MediHealth home" className={styles.link}>
        {content}
      </Link>
    );
  }
  return content;
}
