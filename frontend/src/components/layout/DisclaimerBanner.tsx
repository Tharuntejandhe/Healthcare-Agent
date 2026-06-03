'use client';

import { Info } from 'lucide-react';

/**
 * Persistent, always-visible safety notice for the authenticated app. Keeps the
 * "not a medical diagnosis" message in front of the user on every screen, not
 * just buried at the end of an AI reply.
 */
export function DisclaimerBanner() {
  return (
    <div
      role="note"
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.55rem',
        margin: '2rem 0 0.5rem',
        padding: '0.75rem 1rem',
        borderRadius: 'var(--radius-md, 14px)',
        background: 'var(--muted, rgba(127,127,127,0.08))',
        color: 'var(--muted-foreground, #667085)',
        fontSize: '0.78rem',
        lineHeight: 1.5,
      }}
    >
      <Info size={15} style={{ flexShrink: 0, marginTop: '0.1rem' }} aria-hidden />
      <span>
        MediHealth provides AI-generated information for educational purposes only. It is{' '}
        <strong>not a medical diagnosis</strong> and not a substitute for professional medical
        advice. Always consult a qualified clinician, and call your local emergency number for
        urgent symptoms.
      </span>
    </div>
  );
}
