import React from 'react';
import { cn } from '@/lib/cn';
import styles from './Button.module.css';

type ButtonOwnProps = {
  variant?: 'primary' | 'outline' | 'ghost' | 'secondary';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
  isLoading?: boolean;
  pill?: boolean;
  children?: React.ReactNode;
  className?: string;
};

/**
 * Polymorphic clay button. Renders a <button> by default, or any element /
 * component passed via `as` (e.g. Next's Link, or 'span' inside a <label>),
 * forwarding that target's props with full type-safety.
 */
type ButtonProps<C extends React.ElementType> = ButtonOwnProps & {
  as?: C;
} & Omit<React.ComponentPropsWithoutRef<C>, keyof ButtonOwnProps | 'as'>;

export function Button<C extends React.ElementType = 'button'>({
  as,
  children,
  variant = 'primary',
  size = 'medium',
  fullWidth = false,
  isLoading = false,
  pill = false,
  className = '',
  disabled,
  ...props
}: ButtonProps<C>) {
  const Component = as || 'button';
  const isButton = Component === 'button';
  return (
    <Component
      className={cn(
        styles.button,
        styles[variant],
        styles[size],
        fullWidth && styles.fullWidth,
        pill && styles.pill,
        isLoading && styles.loading,
        className,
      )}
      disabled={isButton ? disabled || isLoading : undefined}
      aria-busy={isLoading || undefined}
      aria-disabled={!isButton && isLoading ? true : undefined}
      {...props}
    >
      {children}
    </Component>
  );
}
