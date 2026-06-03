import type { Variants, Transition } from "motion/react";

/**
 * Shared motion vocabulary for MediHealth.
 * Keeps micro-interactions consistent across every page and component.
 * All consumers are client components ('use client'); this file only exports
 * plain config objects so it can be imported anywhere.
 */

/* ---- Spring presets ---- */
export const springSoft: Transition = { type: "spring", stiffness: 260, damping: 24, mass: 0.9 };
export const springSnappy: Transition = { type: "spring", stiffness: 420, damping: 30 };
export const springClay: Transition = { type: "spring", stiffness: 300, damping: 18, mass: 0.8 };

/* ---- Tactile press / hover used on clay surfaces ---- */
export const tapPress = { scale: 0.96 } as const;
export const tapPressSm = { scale: 0.92 } as const;
export const hoverLift = { y: -4, scale: 1.015 } as const;
export const hoverPop = { scale: 1.06 } as const;

/* ---- Entrance variants ---- */
export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 22 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.6, ease: "easeOut" } },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.92 },
  show: { opacity: 1, scale: 1, transition: { ...springClay } },
};

export const popIn: Variants = {
  hidden: { opacity: 0, scale: 0.6 },
  show: { opacity: 1, scale: 1, transition: { ...springClay } },
};

/* ---- Stagger container ---- */
export const staggerContainer = (stagger = 0.08, delay = 0): Variants => ({
  hidden: {},
  show: { transition: { staggerChildren: stagger, delayChildren: delay } },
});

/* Children of staggerContainer use this */
export const staggerItem: Variants = fadeInUp;

/* ---- Chat bubble entrance ---- */
export const bubbleIn: Variants = {
  hidden: { opacity: 0, y: 14, scale: 0.96 },
  show: { opacity: 1, y: 0, scale: 1, transition: { ...springSoft } },
};

/* ---- Modal / overlay ---- */
export const overlayFade: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.2 } },
  exit: { opacity: 0, transition: { duration: 0.18 } },
};

export const modalPop: Variants = {
  hidden: { opacity: 0, scale: 0.9, y: 16 },
  show: { opacity: 1, scale: 1, y: 0, transition: { ...springClay } },
  exit: { opacity: 0, scale: 0.95, y: 8, transition: { duration: 0.16 } },
};
