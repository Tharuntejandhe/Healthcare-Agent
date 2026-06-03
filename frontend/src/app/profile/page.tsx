"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'motion/react';
import { toast } from 'sonner';
import {
  User,
  Mail,
  Calendar,
  Phone,
  Droplet,
  Ruler,
  Weight,
  HeartPulse,
  AlertTriangle,
  ShieldAlert,
  Pencil,
  Check,
  X,
  LogOut,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Reveal, Stagger, StaggerItem } from '@/components/ui/Reveal';
import { AppShell } from '@/components/layout/AppShell';
import { springClay } from '@/lib/motion';
import { API_BASE_URL } from '@/lib/api';
import { useAuth, useUser } from '@clerk/nextjs';
import styles from './profile.module.css';

interface UserProfile {
  full_name: string;
  email: string;
  mobile?: string;
  blood_group?: string;
  dob?: string;
  gender?: string;
  height?: string;
  weight?: string;
  emergency_contact?: string;
  allergies?: string;
}

type ProfileField = keyof UserProfile;

export default function Profile() {
  const router = useRouter();
  const { getToken, signOut, isLoaded, isSignedIn } = useAuth();
  const { user: clerkUser } = useUser();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [editForm, setEditForm] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
      if (!isLoaded) return;
      if (!isSignedIn) {
        router.push('/login');
        return;
      }
      try {
        const token = await getToken();
        if (!token) return;

        const res = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!res.ok) {
          throw new Error('Failed to fetch user');
        }

        const data = await res.json();
        const userData = {
          full_name: data.full_name || clerkUser?.fullName || 'Medical Patient',
          email: data.email || clerkUser?.primaryEmailAddress?.emailAddress,
          mobile: data.mobile || '+1 (555) 012-3456',
          blood_group: data.blood_group || 'O Positive',
          dob: data.dob || '1990-01-01',
          gender: data.gender || 'Male',
          height: data.height || "5'11\"",
          weight: data.weight || '75 kg',
          emergency_contact: data.emergency_contact || '+1 (555) 999-8888',
          allergies: data.allergies || 'None reported'
        };
        setUser(userData);
        setEditForm(userData);
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, [router, isLoaded, isSignedIn, getToken, clerkUser]);

  const handleLogout = async () => {
    await signOut();
    router.push('/login');
  };

  const handleSave = async () => {
    if (!editForm) return;
    setIsSaving(true);

    // Simulate API call
    setTimeout(() => {
      setUser(editForm);
      setIsEditing(false);
      setIsSaving(false);
      toast.success('Medical profile updated', {
        description: 'Your clinical details have been saved.',
      });
    }, 1000);
  };

  const handleCancel = () => {
    setEditForm(user);
    setIsEditing(false);
  };

  const updateField = (field: ProfileField) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      setEditForm((prev) => (prev ? { ...prev, [field]: e.target.value } : null));

  if (isLoading) {
    return (
      <AppShell>
        <div className={styles.headerRow}>
          <div>
            <h1 className={styles.pageTitle}>Medical Identity</h1>
            <p className={styles.pageSubtitle}>Your personal health record</p>
          </div>
        </div>
        <Card padding="large" className={styles.heroCard}>
          <div className={styles.heroInner}>
            <Skeleton width={104} height={104} radius="var(--radius-full)" />
            <div className={styles.heroText}>
              <Skeleton width={220} height={28} radius="var(--radius-sm)" />
              <Skeleton width={160} height={20} radius="var(--radius-full)" style={{ marginTop: '0.75rem' }} />
            </div>
          </div>
        </Card>
        <div className={styles.sectionsGrid}>
          {[0, 1, 2].map((i) => (
            <Card key={i} padding="large">
              <Skeleton width="40%" height={18} radius="var(--radius-sm)" />
              <div style={{ marginTop: '1.4rem', display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
                {[0, 1].map((j) => (
                  <Skeleton key={j} width="100%" height={48} radius="var(--radius-md)" />
                ))}
              </div>
            </Card>
          ))}
        </div>
      </AppShell>
    );
  }

  type Row = {
    field: ProfileField;
    label: string;
    icon: React.ReactNode;
    type?: string;
    readOnly?: boolean;
    valueClassName?: string;
  };

  type Section = {
    title: string;
    icon: React.ReactNode;
    tone: string;
    rows: Row[];
  };

  const sections: Section[] = [
    {
      title: 'Personal information',
      icon: <User size={18} />,
      tone: 'var(--primary)',
      rows: [
        { field: 'email', label: 'Email address', icon: <Mail size={17} />, readOnly: true, valueClassName: styles.muted },
        { field: 'dob', label: 'Date of birth', icon: <Calendar size={17} />, type: 'date' },
        { field: 'gender', label: 'Gender', icon: <User size={17} /> },
        { field: 'mobile', label: 'Mobile number', icon: <Phone size={17} /> },
      ],
    },
    {
      title: 'Clinical metrics',
      icon: <HeartPulse size={18} />,
      tone: 'var(--success)',
      rows: [
        { field: 'blood_group', label: 'Blood group', icon: <Droplet size={17} /> },
        { field: 'height', label: 'Height', icon: <Ruler size={17} /> },
        { field: 'weight', label: 'Weight', icon: <Weight size={17} /> },
        { field: 'allergies', label: 'Allergies', icon: <AlertTriangle size={17} /> },
      ],
    },
    {
      title: 'Emergency contact',
      icon: <ShieldAlert size={18} />,
      tone: 'var(--error)',
      rows: [
        { field: 'emergency_contact', label: 'Primary contact', icon: <Phone size={17} /> },
      ],
    },
  ];

  return (
    <AppShell>
      {/* Page header */}
      <Reveal inView={false} className={styles.headerRow}>
        <div>
          <h1 className={styles.pageTitle}>Medical Identity</h1>
          <p className={styles.pageSubtitle}>Your personal health record</p>
        </div>
        <AnimatePresence mode="wait" initial={false}>
          {!isEditing ? (
            <motion.div
              key="edit"
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.92 }}
              transition={springClay}
            >
              <Button variant="primary" onClick={() => setIsEditing(true)}>
                <Pencil size={17} /> Edit profile
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="actions"
              className={styles.headerActions}
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.92 }}
              transition={springClay}
            >
              <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
                <X size={17} /> Cancel
              </Button>
              <Button variant="primary" onClick={handleSave} isLoading={isSaving}>
                <Check size={17} /> Save
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </Reveal>

      {/* Hero / avatar */}
      <Reveal inView={false} delay={0.06}>
        <Card padding="large" className={styles.heroCard}>
          <div className={styles.heroInner}>
            <motion.span
              className={styles.avatar}
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ ...springClay, delay: 0.12 }}
              whileHover={{ scale: 1.04, rotate: -3 }}
            >
              <User size={42} strokeWidth={2.2} />
            </motion.span>
            <div className={styles.heroText}>
              {isEditing ? (
                <div className={styles.heroNameEdit}>
                  <Input
                    label="Full name"
                    icon={<User size={16} />}
                    value={editForm?.full_name ?? ''}
                    onChange={updateField('full_name')}
                  />
                </div>
              ) : (
                <>
                  <h2 className={styles.heroName}>{user?.full_name}</h2>
                  <Badge tone="primary" icon={<Mail size={13} />} className={styles.emailBadge}>
                    {user?.email}
                  </Badge>
                </>
              )}
            </div>
          </div>
        </Card>
      </Reveal>

      {/* Sections */}
      <Stagger className={styles.sectionsGrid} stagger={0.09} inView={false} delay={0.12}>
        {sections.map((section) => (
          <StaggerItem key={section.title} style={{ height: '100%' }}>
            <Card padding="large" className={styles.sectionCard}>
              <div className={styles.sectionHead}>
                <span className={styles.sectionIcon} style={{ color: section.tone }}>
                  {section.icon}
                </span>
                <h3 className={styles.sectionTitle}>{section.title}</h3>
              </div>

              <div className={styles.rows}>
                {section.rows.map((row) => {
                  const editable = isEditing && !row.readOnly;
                  return (
                    <div key={row.field} className={styles.row}>
                      <div className={styles.rowLabel}>
                        <span className={styles.rowIcon}>{row.icon}</span>
                        <span>{row.label}</span>
                      </div>
                      <AnimatePresence mode="wait" initial={false}>
                        {editable ? (
                          <motion.div
                            key="input"
                            className={styles.rowInput}
                            initial={{ opacity: 0, y: -6 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -6 }}
                            transition={{ duration: 0.18 }}
                          >
                            <Input
                              type={row.type}
                              value={editForm?.[row.field] ?? ''}
                              onChange={updateField(row.field)}
                            />
                          </motion.div>
                        ) : (
                          <motion.span
                            key="value"
                            className={`${styles.rowValue} ${row.valueClassName ?? ''}`}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.18 }}
                          >
                            {user?.[row.field]}
                          </motion.span>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })}
              </div>
            </Card>
          </StaggerItem>
        ))}
      </Stagger>

      {/* Sign out */}
      {!isEditing && (
        <Reveal className={styles.signOutRow} delay={0.05}>
          <Button variant="ghost" onClick={handleLogout} className={styles.signOutBtn}>
            <LogOut size={17} /> Sign out from MediHealth
          </Button>
        </Reveal>
      )}
    </AppShell>
  );
}
