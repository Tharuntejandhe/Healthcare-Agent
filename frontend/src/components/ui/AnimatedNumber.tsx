'use client';

import { useEffect, useRef } from 'react';
import { animate, useInView } from 'motion/react';

interface AnimatedNumberProps {
  value: number;
  duration?: number;
  className?: string;
}

/** Counts up to `value` once it scrolls into view. */
export function AnimatedNumber({ value, duration = 1.1, className }: AnimatedNumberProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.6 });

  useEffect(() => {
    if (!inView || !ref.current) return;
    const node = ref.current;
    const controls = animate(0, value, {
      duration,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => {
        node.textContent = Math.round(v).toLocaleString();
      },
    });
    return () => controls.stop();
  }, [inView, value, duration]);

  return (
    <span ref={ref} className={className}>
      0
    </span>
  );
}
