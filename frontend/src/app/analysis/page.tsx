"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import {
  FlaskConical,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart as PieChartIcon,
  Sparkles,
  ArrowLeft,
  ActivitySquare,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { Skeleton } from '@/components/ui/Skeleton';
import { AnimatedNumber } from '@/components/ui/AnimatedNumber';
import { Reveal, Stagger, StaggerItem } from '@/components/ui/Reveal';
import { AppShell } from '@/components/layout/AppShell';
import { API_BASE_URL } from '@/lib/api';
import styles from './analysis.module.css';

interface LabParameter {
  test_name: string;
  value: number;
  unit: string;
  status: 'NORMAL' | 'HIGH' | 'LOW';
  category: string;
}

interface AnalysisData {
  summary: string;
  stats: {
    total_tests: number;
    high_values: number;
    low_values: number;
    normal_values: number;
  };
  aggregated_data: LabParameter[];
}

// Chart palette — concrete hex matched to clay tokens.
const CLAY = {
  primary: '#14a890',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  muted: '#94a3a0',
} as const;

const COLORS = [CLAY.success, CLAY.error, CLAY.warning]; // Normal, High, Low

export default function AnalysisPage() {
  const [data, setData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`${API_BASE_URL}/api/v1/documents/analytical-report`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!res.ok) {
          throw new Error('Failed to fetch analysis');
        }

        const result = await res.json();
        // Only a full success payload carries stats + aggregated_data. Any other
        // status (empty / error) must NOT be set as data or the charts crash on
        // the missing fields — show the friendly message instead.
        if (result.status === 'success' && result.stats && Array.isArray(result.aggregated_data)) {
          setData(result);
        } else {
          setError(result.summary || 'No analysis available yet. Upload medical reports to unlock analytics.');
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, []);

  if (loading) {
    return (
      <AppShell>
        <Reveal inView={false} className={styles.headingBlock}>
          <h1 className={styles.pageTitle}>Health Analysis</h1>
          <p className={styles.pageSubtitle}>Synthesizing your lab history into a single view…</p>
        </Reveal>

        <div className={styles.loadingRow}>
          <Spinner size={22} />
          <span>Analyzing your medical history…</span>
        </div>

        <div className={styles.statsGrid}>
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className={styles.statCard}>
              <Skeleton width={52} height={52} radius="var(--radius-md)" />
              <div className={styles.statInfo}>
                <Skeleton width="60%" height={12} radius="var(--radius-full)" />
                <Skeleton width="40%" height={26} radius="var(--radius-sm)" style={{ marginTop: '0.5rem' }} />
              </div>
            </Card>
          ))}
        </div>

        <div className={styles.chartsGrid}>
          <Card className={styles.chartCard}>
            <Skeleton width="50%" height={18} radius="var(--radius-full)" />
            <Skeleton width="100%" height={280} radius="var(--radius-md)" style={{ marginTop: '1.2rem' }} />
          </Card>
          <Card className={styles.chartCard}>
            <Skeleton width="50%" height={18} radius="var(--radius-full)" />
            <Skeleton width="100%" height={280} radius="var(--radius-md)" style={{ marginTop: '1.2rem' }} />
          </Card>
        </div>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell>
        <Reveal inView={false} className={styles.headingBlock}>
          <h1 className={styles.pageTitle}>Health Analysis</h1>
          <p className={styles.pageSubtitle}>AI-driven insights from your lab reports.</p>
        </Reveal>

        <Reveal>
          <Card padding="large">
            <div className={styles.empty}>
              <span className={styles.emptyIcon}><ActivitySquare size={40} /></span>
              <h2>Analysis unavailable</h2>
              <p>{error || 'No data available yet. Upload medical reports to unlock AI-powered analytics.'}</p>
              <Button as={Link} href="/dashboard" variant="primary">
                <ArrowLeft size={18} /> Return to dashboard
              </Button>
            </div>
          </Card>
        </Reveal>
      </AppShell>
    );
  }

  // Prepare data for charts
  const pieData = [
    { name: 'Normal', value: data.stats.normal_values },
    { name: 'High', value: data.stats.high_values },
    { name: 'Low', value: data.stats.low_values },
  ].filter(item => item.value > 0);

  // Group by category for bar chart
  const categories: Record<string, number> = {};
  data.aggregated_data.forEach(item => {
    categories[item.category] = (categories[item.category] || 0) + 1;
  });
  const barData = Object.keys(categories).map(cat => ({
    name: cat,
    count: categories[cat]
  }));

  const stats = [
    {
      label: 'Total tests',
      value: data.stats.total_tests,
      icon: <FlaskConical size={24} />,
      tone: 'primary' as const,
      iconBg: 'var(--primary-light)',
      iconColor: 'var(--primary)',
      badge: 'Tracked',
    },
    {
      label: 'Normal',
      value: data.stats.normal_values,
      icon: <CheckCircle2 size={24} />,
      tone: 'success' as const,
      iconBg: 'var(--success-soft)',
      iconColor: 'var(--success)',
      badge: 'In range',
    },
    {
      label: 'High',
      value: data.stats.high_values,
      icon: <TrendingUp size={24} />,
      tone: 'error' as const,
      iconBg: 'var(--error-soft)',
      iconColor: 'var(--error)',
      badge: 'Above range',
    },
    {
      label: 'Low',
      value: data.stats.low_values,
      icon: <TrendingDown size={24} />,
      tone: 'warning' as const,
      iconBg: 'var(--warning-soft)',
      iconColor: 'var(--warning)',
      badge: 'Below range',
    },
  ];

  return (
    <AppShell>
      <Reveal inView={false} className={styles.headingBlock}>
        <h1 className={styles.pageTitle}>Comprehensive Health Analysis</h1>
        <p className={styles.pageSubtitle}>
          AI-aggregated lab parameters across your uploaded reports.
        </p>
      </Reveal>

      {/* Stats */}
      <Stagger className={styles.statsGrid} stagger={0.09} inView={false} delay={0.05}>
        {stats.map((s) => (
          <StaggerItem key={s.label}>
            <Card hoverable className={styles.statCard}>
              <span
                className={styles.statIcon}
                style={{ background: s.iconBg, color: s.iconColor }}
              >
                {s.icon}
              </span>
              <div className={styles.statInfo}>
                <div className={styles.statTop}>
                  <h3>{s.label}</h3>
                  <Badge tone={s.tone}>{s.badge}</Badge>
                </div>
                <div className={styles.statValue}>
                  <AnimatedNumber value={s.value} />
                </div>
              </div>
            </Card>
          </StaggerItem>
        ))}
      </Stagger>

      {/* Charts */}
      <div className={styles.chartsGrid}>
        <Reveal>
          <Card className={styles.chartCard}>
            <div className={styles.chartHead}>
              <span className={styles.chartIcon}><BarChart3 size={20} /></span>
              <h2>Test distribution by category</h2>
            </div>
            <div className={styles.chartBody}>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={barData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={CLAY.muted} strokeOpacity={0.35} />
                  <XAxis dataKey="name" tick={{ fill: CLAY.muted, fontSize: 12 }} tickLine={false} axisLine={{ stroke: CLAY.muted, strokeOpacity: 0.4 }} />
                  <YAxis allowDecimals={false} tick={{ fill: CLAY.muted, fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip
                    cursor={{ fill: CLAY.primary, fillOpacity: 0.06 }}
                    contentStyle={{
                      background: 'var(--card)',
                      border: 'none',
                      borderRadius: 'var(--radius-md)',
                      boxShadow: 'var(--shadow-clay-sm)',
                      color: 'var(--foreground)',
                    }}
                    labelStyle={{ color: 'var(--muted-foreground)', fontWeight: 600 }}
                  />
                  <Bar dataKey="count" fill={CLAY.primary} radius={[8, 8, 0, 0]} maxBarSize={56} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Reveal>

        <Reveal delay={0.08}>
          <Card className={styles.chartCard}>
            <div className={styles.chartHead}>
              <span className={styles.chartIcon}><PieChartIcon size={20} /></span>
              <h2>Health status overview</h2>
            </div>
            <div className={styles.chartBody}>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={62}
                    outerRadius={92}
                    paddingAngle={4}
                    dataKey="value"
                    stroke="var(--card)"
                    strokeWidth={3}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: 'var(--card)',
                      border: 'none',
                      borderRadius: 'var(--radius-md)',
                      boxShadow: 'var(--shadow-clay-sm)',
                      color: 'var(--foreground)',
                    }}
                  />
                  <Legend
                    iconType="circle"
                    wrapperStyle={{ fontSize: 13, color: 'var(--muted-foreground)' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Reveal>
      </div>

      {/* AI summary */}
      <Reveal delay={0.1}>
        <Card padding="large" className={styles.summaryCard}>
          <div className={styles.summaryHead}>
            <span className={styles.summaryIcon}><Sparkles size={20} /></span>
            <div>
              <h2>Executive medical summary</h2>
              <p>Generated from your aggregated lab data.</p>
            </div>
          </div>
          <div className={styles.summaryContent}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {data.summary}
            </ReactMarkdown>
          </div>
        </Card>
      </Reveal>
    </AppShell>
  );
}
