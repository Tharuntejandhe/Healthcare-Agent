'use client';

import React from 'react';
import { motion, type HTMLMotionProps } from 'motion/react';
import { cn } from '@/lib/cn';
import { springClay } from '@/lib/motion';
import styles from './IconButton.module.css';

interface IconButtonProps extends Omit<HTMLMotionProps<'button'>, 'ref'> {
  variant?: 'default' | 'primary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  /** Required for accessibility on icon-only controls. */
  'aria-label': string;
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ variant = 'default', size = 'md', className = '', children, disabled, ...props }, ref) => (
    <motion.button
      ref={ref}
      type="button"
      className={cn(styles.btn, styles[variant], styles[size], className)}
      disabled={disabled}
      whileHover={disabled ? undefined : { scale: 1.08, boxShadow: 'var(--shadow-clay)' }}
      whileTap={disabled ? undefined : { scale: 0.88 }}
      transition={springClay}
      {...props}
    >
      {children}
    </motion.button>
  ),
);

IconButton.displayName = 'IconButton';
