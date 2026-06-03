import React from 'react';
import { cn } from '@/lib/cn';
import styles from './Badge.module.css';

interface BadgeProps {
  children: React.ReactNode;
  tone?: 'neutral' | 'primary' | 'success' | 'warning' | 'error' | 'info';
  icon?: React.ReactNode;
  dot?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, tone = 'neutral', icon, dot, className }) => (
  <span className={cn(styles.badge, styles[tone], className)}>
    {dot && <span className={styles.dot} />}
    {icon && <span className={styles.icon}>{icon}</span>}
    {children}
  </span>
);
