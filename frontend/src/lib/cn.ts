import { clsx, type ClassValue } from "clsx";

/**
 * Tiny className combiner. Filters falsy values and joins CSS-module classes
 * with conditional ones. Used everywhere in place of manual array.join().
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
