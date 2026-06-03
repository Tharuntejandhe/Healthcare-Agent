import Link from 'next/link';
import { SignInButton, SignUpButton, Show, UserButton } from '@clerk/nextjs';
import {
  Sparkles,
  Stethoscope,
  ScanLine,
  Mic,
  BarChart3,
  ShieldCheck,
  BrainCircuit,
  CheckCircle2,
  FileText,
  MessagesSquare,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Logo } from '@/components/ui/Logo';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { Reveal, Stagger, StaggerItem } from '@/components/ui/Reveal';
import styles from './page.module.css';

const PREVIEW = [
  {
    title: 'Medical Analysis',
    body: 'RAG-grounded analysis of your medical records, returning clinically-precise, source-cited insight.',
    icon: Stethoscope,
    bg: 'var(--gradient-brand)',
  },
  {
    title: 'Real-time Insights',
    body: 'Instant lab-report processing with visual trend tracking, so nothing important slips by.',
    icon: BarChart3,
    bg: 'linear-gradient(135deg, hsl(158,66%,46%), hsl(172,70%,46%))',
  },
  {
    title: 'Secure & Compliant',
    body: 'Per-tenant data isolation and HIPAA-ready handling. Your records never leave your space.',
    icon: ShieldCheck,
    bg: 'var(--gradient-accent)',
  },
];

const FEATURES = [
  { title: 'Multi-agent reasoning', body: 'Junior, senior and specialist agents collaborate on every case for second-opinion depth.', icon: BrainCircuit },
  { title: 'Vision triage', body: 'Snap or upload a photo of an injury and get structured, careful first-look guidance.', icon: ScanLine },
  { title: 'Voice consultations', body: 'Speak naturally — speech-to-text turns conversation into a documented exchange.', icon: Mic },
  { title: 'Lab analytics', body: 'Bloodwork and panels parsed into charts, ranges and plain-language summaries.', icon: BarChart3 },
  { title: 'Document Q&A', body: 'Ask questions against your own reports; answers are grounded in your data, not guesses.', icon: FileText },
  { title: 'Private by default', body: 'Tenant isolation, no third-party prompt sharing, full audit trail on every request.', icon: ShieldCheck },
];

const STEPS = [
  { title: 'Upload your reports', body: 'Drop in lab PDFs and records. We index them privately, just for you.' },
  { title: 'Ask anything', body: 'Chat, speak, or share a photo. Agents reason over your own data in real time.' },
  { title: 'Act with clarity', body: 'Get risk scoring, trends and next-step guidance you can actually use.' },
];

export default function Home() {
  return (
    <div className={styles.page}>
      {/* Nav */}
      <nav className={styles.nav}>
        <div className={`${styles.container} ${styles.navInner}`}>
          <Logo size="md" />
          <div className={styles.navLinks}>
            <Show when="signed-out">
              <SignInButton mode="modal">
                <button className={styles.navLogin}>Sign in</button>
              </SignInButton>
              <SignUpButton mode="modal">
                <Button size="small" pill>Get started</Button>
              </SignUpButton>
            </Show>
            <Show when="signed-in">
              <Button as={Link} href="/dashboard" size="small" pill>Dashboard</Button>
              <UserButton />
            </Show>
            <ThemeToggle />
          </div>
        </div>
      </nav>

      {/* Hero */}
      <header className={`${styles.container} ${styles.hero}`}>
        <Reveal inView={false}>
          <span className={styles.eyebrow}>
            <Sparkles /> Revolutionizing medical diagnostics
          </span>
        </Reveal>
        <Reveal inView={false} delay={0.06}>
          <h1 className={styles.title}>
            Intelligent AI agents for <span className={styles.grad}>healthcare excellence</span>
          </h1>
        </Reveal>
        <Reveal inView={false} delay={0.12}>
          <p className={styles.subtitle}>
            MediHealth orchestrates multi-turn medical agents to deliver high-precision diagnostics,
            report analysis and clinical decision support — grounded in your own records.
          </p>
        </Reveal>
        <Reveal inView={false} delay={0.18}>
          <div className={styles.ctas}>
            <Button as={Link} href="/sign-up" size="large" pill>
              Start free
            </Button>
            <Button as={Link} href="/chat" variant="secondary" size="large" pill>
              Live demo
            </Button>
          </div>
        </Reveal>
        <Reveal inView={false} delay={0.24}>
          <div className={styles.trust}>
            <span className={styles.trustItem}><CheckCircle2 /> No credit card</span>
            <span className={styles.trustItem}><CheckCircle2 /> HIPAA-ready</span>
            <span className={styles.trustItem}><CheckCircle2 /> Private by default</span>
          </div>
        </Reveal>

        {/* Floating preview cards */}
        <Stagger className={styles.previewGrid} stagger={0.1} delay={0.3} inView={false}>
          {PREVIEW.map((p) => {
            const Icon = p.icon;
            return (
              <StaggerItem key={p.title} style={{ height: '100%' }}>
                <Card hoverable padding="large" className={styles.previewCard}>
                  <span className={styles.previewIcon} style={{ background: p.bg }}>
                    <Icon />
                  </span>
                  <h3>{p.title}</h3>
                  <p>{p.body}</p>
                </Card>
              </StaggerItem>
            );
          })}
        </Stagger>
      </header>

      {/* Capabilities */}
      <section className={`${styles.container} ${styles.section}`}>
        <Reveal className={styles.sectionHead}>
          <span className={styles.sectionEyebrow}>Capabilities</span>
          <h2 className={styles.sectionTitle}>One platform, every modality of care</h2>
          <p className={styles.sectionSub}>
            Reasoning, vision, voice and analytics — woven into a single, calm workflow.
          </p>
        </Reveal>
        <Stagger className={styles.features} stagger={0.07}>
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <StaggerItem key={f.title} style={{ height: '100%' }}>
                <Card hoverable className={styles.feature}>
                  <span className={styles.featureIcon}>
                    <Icon size={22} />
                  </span>
                  <h3>{f.title}</h3>
                  <p>{f.body}</p>
                </Card>
              </StaggerItem>
            );
          })}
        </Stagger>
      </section>

      {/* How it works */}
      <section className={`${styles.container} ${styles.section}`}>
        <Reveal className={styles.sectionHead}>
          <span className={styles.sectionEyebrow}>How it works</span>
          <h2 className={styles.sectionTitle}>From records to clarity in three steps</h2>
        </Reveal>
        <Stagger className={styles.steps} stagger={0.1}>
          {STEPS.map((s, i) => (
            <StaggerItem key={s.title} style={{ height: '100%' }}>
              <Card className={styles.step}>
                <span className={styles.stepNum}>{i + 1}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </Card>
            </StaggerItem>
          ))}
        </Stagger>
      </section>

      {/* CTA band */}
      <section className={`${styles.container} ${styles.section}`}>
        <Reveal>
          <div className={styles.ctaBand}>
            <h2>Ready to meet your care companion?</h2>
            <p>Create an account in seconds and start a conversation with your own health data.</p>
            <Button as={Link} href="/sign-up" variant="secondary" size="large" pill>
              <MessagesSquare size={18} /> Get started free
            </Button>
          </div>
        </Reveal>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={`${styles.container} ${styles.footerInner}`}>
          <Logo size="sm" />
          <span className={styles.footerCopy}>© 2026 MediHealth Solutions. All rights reserved.</span>
        </div>
      </footer>
    </div>
  );
}
