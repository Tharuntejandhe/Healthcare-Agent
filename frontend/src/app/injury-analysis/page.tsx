'use client';

import { ScanSearch, ShieldAlert } from 'lucide-react';
import InjuryAnalyzer from '@/components/vision/InjuryAnalyzer';
import { AppShell } from '@/components/layout/AppShell';
import { Reveal } from '@/components/ui/Reveal';
import styles from './injury.module.css';

export default function InjuryAnalysisPage() {
  return (
    <AppShell>
      <Reveal inView={false} className={styles.header}>
        <span className={styles.headerIcon}>
          <ScanSearch size={26} />
        </span>
        <div className={styles.headerText}>
          <h1>Injury Context Analysis</h1>
          <p>Upload a photo of the affected area for an AI-assisted visual assessment.</p>
        </div>
      </Reveal>

      <Reveal inView={false} delay={0.08} className={styles.disclaimerBanner}>
        <ShieldAlert size={18} className={styles.disclaimerBannerIcon} />
        <span>
          This tool offers informational guidance only and is not a medical diagnosis.
          For emergencies, contact a doctor or emergency services immediately.
        </span>
      </Reveal>

      <InjuryAnalyzer />
    </AppShell>
  );
}
