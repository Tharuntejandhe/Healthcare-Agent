"use client";

import { ReactNode } from "react";
import { motion } from "motion/react";
import { Check, HeartPulse, ShieldCheck, Users } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { springClay } from "@/lib/motion";
import styles from "@/app/auth.module.css";

interface AuthShellProps {
  eyebrow: string;
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}

const FEATURES: { title: string; body: string; icon: typeof Check }[] = [
  { title: "Clinical-grade reasoning", body: "Triage, risk scoring and document Q&A grounded in your records.", icon: HeartPulse },
  { title: "Private by default", body: "Your data stays in your tenant. No third-party prompts.", icon: ShieldCheck },
  { title: "Built for teams", body: "From intake to follow-up — one shared source of truth.", icon: Users },
];

export function AuthShell({ eyebrow, title, subtitle, children, footer }: AuthShellProps) {
  return (
    <div className={styles.wrapper}>
      <aside className={styles.brandPanel}>
        <div className={styles.brandContent}>
          <Logo size="md" href="/" />

          <div>
            <motion.h2
              className={styles.brandHeadline}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springClay, delay: 0.1 }}
            >
              Care that listens, reasons, and acts.
            </motion.h2>
            <motion.p
              className={styles.brandTagline}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...springClay, delay: 0.18 }}
            >
              MediHealth orchestrates intake, vision triage and personalized follow-up in one place — so your
              team spends time on patients, not paperwork.
            </motion.p>

            <div className={styles.brandFeatures}>
              {FEATURES.map((f, i) => {
                const Icon = f.icon;
                return (
                  <motion.div
                    key={f.title}
                    className={styles.brandFeature}
                    initial={{ opacity: 0, x: -16 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ ...springClay, delay: 0.26 + i * 0.08 }}
                  >
                    <span className={styles.brandCheck}>
                      <Icon size={15} strokeWidth={2.4} />
                    </span>
                    <div>
                      <div className={styles.brandFeatureTitle}>{f.title}</div>
                      <div className={styles.brandFeatureBody}>{f.body}</div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>

          <div className={styles.brandFooter}>© 2026 MediHealth — All rights reserved.</div>
        </div>
      </aside>

      <main className={styles.formPanel}>
        <div className={styles.themeToggleWrap}>
          <ThemeToggle />
        </div>

        <motion.div
          className={styles.authCard}
          initial={{ opacity: 0, y: 26, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={springClay}
        >
          <header className={styles.header}>
            <div className={styles.eyebrow}>{eyebrow}</div>
            <h1 className={styles.title}>{title}</h1>
            <p className={styles.subtitle}>{subtitle}</p>
          </header>

          {children}

          {footer ? <div className={styles.footer}>{footer}</div> : null}
        </motion.div>
      </main>
    </div>
  );
}
