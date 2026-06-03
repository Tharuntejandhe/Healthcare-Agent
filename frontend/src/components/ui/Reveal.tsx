'use client';

import React from 'react';
import { motion, type HTMLMotionProps } from 'motion/react';
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/motion';

interface RevealProps extends Omit<HTMLMotionProps<'div'>, 'ref'> {
  /** Seconds to delay the entrance. */
  delay?: number;
  /** Animate when scrolled into view (default) vs. immediately on mount. */
  inView?: boolean;
  as?: keyof typeof motion;
}

/** Fade + rise entrance for a single block. */
export const Reveal: React.FC<RevealProps> = ({ children, delay = 0, inView = true, className, ...props }) => {
  const animateProps = inView
    ? { whileInView: 'show' as const, viewport: { once: true, amount: 0.2 } }
    : { animate: 'show' as const };
  return (
    <motion.div
      className={className}
      variants={fadeInUp}
      initial="hidden"
      transition={{ delay }}
      {...animateProps}
      {...props}
    >
      {children}
    </motion.div>
  );
};

interface StaggerProps extends Omit<HTMLMotionProps<'div'>, 'ref'> {
  stagger?: number;
  delay?: number;
  inView?: boolean;
}

/** Container that staggers the entrance of its <StaggerItem> children. */
export const Stagger: React.FC<StaggerProps> = ({
  children,
  stagger = 0.08,
  delay = 0,
  inView = true,
  className,
  ...props
}) => {
  const animateProps = inView
    ? { whileInView: 'show' as const, viewport: { once: true, amount: 0.15 } }
    : { animate: 'show' as const };
  return (
    <motion.div
      className={className}
      variants={staggerContainer(stagger, delay)}
      initial="hidden"
      {...animateProps}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const StaggerItem: React.FC<Omit<HTMLMotionProps<'div'>, 'ref'>> = ({
  children,
  className,
  ...props
}) => (
  <motion.div className={className} variants={staggerItem} {...props}>
    {children}
  </motion.div>
);
