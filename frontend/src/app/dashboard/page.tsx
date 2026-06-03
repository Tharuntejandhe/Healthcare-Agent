"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'motion/react';
import { toast } from 'sonner';
import {
  FileText,
  FlaskConical,
  Activity,
  Upload,
  Trash2,
  FolderOpen,
  MessageCircleHeart,
  ExternalLink,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { AnimatedNumber } from '@/components/ui/AnimatedNumber';
import { Reveal, Stagger, StaggerItem } from '@/components/ui/Reveal';
import { AppShell } from '@/components/layout/AppShell';
import { springClay } from '@/lib/motion';
import { API_BASE_URL, listDocuments, type ApiDocument } from '@/lib/api';
import { purgeLegacyPhi } from '@/lib/auth';
import { useAuth, useUser } from '@clerk/nextjs';
import styles from './dashboard.module.css';

interface Report {
  id: string;
  name: string;
  date: string;
  status: 'completed' | 'pending';
  type: string;
  url?: string;
  blobName?: string;
}

function toReport(doc: ApiDocument): Report {
  return {
    id: String(doc.id),
    name: doc.filename,
    date: doc.created_at ? doc.created_at.split('T')[0] : '',
    status: 'completed',
    type: doc.chunks_indexed ? 'AI Indexed' : 'Stored',
    url: doc.url ?? undefined,
    blobName: doc.blob_name,
  };
}

export default function Dashboard() {
  const router = useRouter();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();
  const [reports, setReports] = useState<Report[]>([]);
  const [isMounted, setIsMounted] = useState(false);
  const [riskData, setRiskData] = useState<any>(null);
  const [isLoadingRisk, setIsLoadingRisk] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    purgeLegacyPhi();

    const fetchUserAndReports = async () => {
      if (!isLoaded) return;
      if (!isSignedIn) {
        router.push('/login');
        return;
      }
      try {
        const token = await getToken();
        if (!token) return;

        // Reports come from the server (DB), never browser storage.
        const docs = await listDocuments(token);
        setReports(docs.map(toReport));
      } catch (e) {
        console.error('Error fetching reports:', e);
      }
    };

    fetchUserAndReports();
    fetchRiskAssessment();
  }, [router, isLoaded, isSignedIn, getToken]);

  const fetchRiskAssessment = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      setIsLoadingRisk(true);
      const res = await fetch(`${API_BASE_URL}/api/v1/risk/my-risk`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setRiskData(await res.json());
    } catch (e) {
      console.error('Error fetching risk assessment:', e);
    } finally {
      setIsLoadingRisk(false);
    }
  };

  const handleDelete = (report: Report) => {
    toast('Delete this report?', {
      description: report.name,
      action: {
        label: 'Delete',
        onClick: async () => {
          try {
            if (report.blobName) {
              const token = await getToken();
              const res = await fetch(`${API_BASE_URL}/api/v1/documents/${report.blobName}`, {
                method: 'DELETE',
                headers: { Authorization: `Bearer ${token}` },
              });
              if (!res.ok) console.warn('Remote delete failed; removing locally.');
            }
            setReports((prev) => prev.filter((r) => r.id !== report.id));
            toast.success('Report deleted');
          } catch (error) {
            console.error('Delete error:', error);
            setReports((prev) => prev.filter((r) => r.id !== report.id));
          }
        },
      },
    });
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const isPdf = file.type === 'application/pdf';
    const isImage = file.type.startsWith('image/');
    if (!isPdf && !isImage) {
      toast.error('Upload a PDF, or a photo (JPEG/PNG) of your report.');
      e.target.value = '';
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    const uploadPromise = (async () => {
      const token = await getToken();
      const res = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData?.error?.message || errorData?.detail || 'Upload failed.');
      }
      const data = await res.json();
      const newReport: Report = {
        id: Date.now().toString(),
        name: file.name,
        date: new Date().toISOString().split('T')[0],
        status: 'completed',
        type: 'AI Indexed',
        url: data.azure_url,
        blobName: data.blob_name,
      };
      setReports((prev) => [newReport, ...prev]);
      return data;
    })();

    toast.promise(uploadPromise, {
      loading: 'Uploading & indexing your report…',
      success: 'Report uploaded and indexed!',
      error: (err) => `Upload failed: ${err.message}`,
    });

    try {
      await uploadPromise;
    } catch {
      /* toast already surfaced the error */
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const openReport = async (report: Report) => {
    if (!report.url) {
      toast('Report is still being processed.');
      return;
    }
    if (report.url.startsWith('http')) {
      window.open(report.url, '_blank');
      return;
    }
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE_URL}${report.url}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to fetch file');
      const blob = await res.blob();
      window.open(URL.createObjectURL(blob), '_blank');
    } catch (err) {
      console.error('Error opening local file:', err);
      toast.error('Could not open report. Your session may have expired.');
    }
  };

  if (!isMounted) return null;

  const indexedCount = reports.filter((r) => r.type === 'AI Indexed').length;
  const riskStatus = isLoadingRisk
    ? 'Analyzing…'
    : reports.length === 0
      ? 'PENDING'
      : riskData?.overall_status || 'N/A';
  const riskColor =
    reports.length === 0
      ? 'var(--muted-foreground)'
      : riskData?.overall_status === 'CRITICAL'
        ? 'var(--error)'
        : riskData?.overall_status === 'HEALTHY'
          ? 'var(--success)'
          : 'var(--foreground)';

  return (
    <AppShell>
      {/* Header */}
      <Reveal inView={false} className={styles.header}>
        <div className={styles.welcome}>
          <h1>Patient Dashboard</h1>
          <p>Welcome back, {user?.firstName || user?.emailAddresses[0]?.emailAddress?.split('@')[0] || 'Member'}</p>
        </div>
        <input
          type="file"
          id="report-upload"
          className={styles.uploadInput}
          onChange={handleFileUpload}
          accept=".pdf,image/*"
        />
        <label htmlFor="report-upload">
          <Button as="span" variant="primary" isLoading={isUploading} size="large">
            <Upload size={18} />
            {isUploading ? 'Uploading…' : 'Upload report'}
          </Button>
        </label>
      </Reveal>

      {/* Stats */}
      <Stagger className={styles.statsGrid} stagger={0.09} inView={false} delay={0.05}>
        <StaggerItem>
          <Card className={styles.statCard}>
            <span className={styles.statIcon} style={{ background: 'var(--primary-light)', color: 'var(--primary)' }}>
              <FileText size={26} />
            </span>
            <div className={styles.statInfo}>
              <h3>Total reports</h3>
              <div className={styles.statValue}><AnimatedNumber value={reports.length} /></div>
            </div>
          </Card>
        </StaggerItem>
        <StaggerItem>
          <Card className={styles.statCard}>
            <span className={styles.statIcon} style={{ background: 'var(--success-soft)', color: 'var(--success)' }}>
              <FlaskConical size={26} />
            </span>
            <div className={styles.statInfo}>
              <h3>AI indexed</h3>
              <div className={styles.statValue}><AnimatedNumber value={indexedCount} /></div>
            </div>
          </Card>
        </StaggerItem>
        <StaggerItem>
          <Card className={styles.statCard}>
            <span className={styles.statIcon} style={{ background: 'hsla(var(--accent-hue), 78%, 60%, 0.16)', color: 'var(--info)' }}>
              <Activity size={26} />
            </span>
            <div className={styles.statInfo}>
              <h3>Risk status</h3>
              <div className={styles.statValueText} style={{ color: riskColor }}>{riskStatus}</div>
            </div>
          </Card>
        </StaggerItem>
      </Stagger>

      {/* Section */}
      <div className={styles.sectionTitle}>
        <h2>Recent medical files</h2>
        {reports.length > 0 && (
          <Button as={Link} href="/analysis" variant="ghost" size="small">
            View analytics
          </Button>
        )}
      </div>

      {reports.length === 0 ? (
        <Reveal>
          <Card padding="large">
            <div className={styles.empty}>
              <span className={styles.emptyIcon}><FolderOpen size={40} /></span>
              <h2>Your clinical vault is empty</h2>
              <p>Upload your medical reports to begin AI-powered orchestration, risk scoring and insights.</p>
              <label htmlFor="report-upload">
                <Button as="span" variant="primary"><Upload size={18} /> Add your first report</Button>
              </label>
            </div>
          </Card>
        </Reveal>
      ) : (
        <Stagger className={styles.reportsGrid} stagger={0.07}>
          {reports.map((report) => (
            <StaggerItem key={report.id} style={{ height: '100%' }}>
              <Card hoverable className={styles.reportCard}>
                <div className={styles.reportHeader}>
                  <span className={styles.reportType}><FileText size={22} /></span>
                  <Badge tone={report.status === 'completed' ? 'success' : 'warning'} dot>
                    {report.status}
                  </Badge>
                </div>
                <div className={styles.reportTitle}>
                  <h3>{report.name}</h3>
                  <div className={styles.reportMeta}>
                    <span>{report.type}</span>
                    <span>•</span>
                    <span>{report.date}</span>
                  </div>
                </div>
                <div className={styles.reportFooter}>
                  <Button variant="primary" size="small" fullWidth onClick={() => openReport(report)}>
                    <ExternalLink size={15} /> View
                  </Button>
                  <Button variant="outline" size="small" onClick={() => handleDelete(report)} aria-label="Delete report">
                    <Trash2 size={15} />
                  </Button>
                </div>
              </Card>
            </StaggerItem>
          ))}
        </Stagger>
      )}

      {/* Floating consultation FAB */}
      <motion.div
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ ...springClay, delay: 0.4 }}
        whileHover={{ scale: 1.08, rotate: -4 }}
        whileTap={{ scale: 0.9 }}
        className={styles.floatingChat}
        style={{ position: 'fixed' }}
      >
        <Link href="/chat" aria-label="Launch AI consultation" title="Launch AI consultation" style={{ display: 'inline-flex' }}>
          <MessageCircleHeart size={28} />
        </Link>
      </motion.div>
    </AppShell>
  );
}
