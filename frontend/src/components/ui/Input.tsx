import React, { forwardRef } from 'react';
import { cn } from '@/lib/cn';
import styles from './Input.module.css';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  /** Optional leading icon (e.g. a lucide icon element). */
  icon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, icon, className = '', id, ...props }, ref) => {
    const inputId = id || props.name;
    return (
      <div className={styles.container}>
        {label && (
          <label className={styles.label} htmlFor={inputId}>
            {label}
          </label>
        )}
        <div className={styles.field}>
          {icon && <span className={styles.icon}>{icon}</span>}
          <input
            id={inputId}
            ref={ref}
            aria-invalid={error ? true : undefined}
            className={cn(styles.input, icon && styles.hasIcon, error && styles.error, className)}
            {...props}
          />
        </div>
        {error ? (
          <span className={styles.errorMessage}>{error}</span>
        ) : hint ? (
          <span className={styles.hint}>{hint}</span>
        ) : null}
      </div>
    );
  },
);

Input.displayName = 'Input';
