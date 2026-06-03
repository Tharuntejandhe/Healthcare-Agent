'use client';

import React from 'react';
import { motion, type HTMLMotionProps } from 'motion/react';
import { cn } from '@/lib/cn';
import { springSoft } from '@/lib/motion';
import styles from './Card.module.css';

type CardVariant = 'default' | 'glass' | 'outline' | 'flat' | 'inset';

interface CardProps extends Omit<HTMLMotionProps<'div'>, 'ref'> {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'small' | 'medium' | 'large';
  variant?: CardVariant;
  /** Lift + brighten on hover (spring). */
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  padding = 'medium',
  variant = 'default',
  hoverable = false,
  ...props
}) => {
  const interactive = hoverable || !!props.onClick;
  return (
    <motion.div
      className={cn(
        styles.card,
        styles[padding],
        styles[variant],
        interactive && styles.interactive,
        className,
      )}
      whileHover={hoverable ? { y: -5, boxShadow: 'var(--shadow-clay-raised)' } : undefined}
      whileTap={props.onClick ? { scale: 0.99 } : undefined}
      transition={springSoft}
      {...props}
    >
      {children}
    </motion.div>
  );
};
