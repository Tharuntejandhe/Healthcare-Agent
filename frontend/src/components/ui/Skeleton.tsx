import React from 'react';
import { cn } from '@/lib/cn';
import styles from './Skeleton.module.css';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  radius?: string | number;
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({ width, height, radius, className, style }) => (
  <span
    aria-hidden="true"
    className={cn(styles.skeleton, className)}
    style={{ width, height, borderRadius: radius, ...style }}
  />
);
