'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { motion } from 'motion/react';
import {
  LayoutDashboard,
  MessageCircleHeart,
  BarChart3,
  ScanLine,
  User,
  LogOut,
  type LucideIcon,
} from 'lucide-react';
import { useAuth } from '@clerk/nextjs';
import { cn } from '@/lib/cn';
import { Logo } from '@/components/ui/Logo';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import styles from './AppShell.module.css';

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

const NAV: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/chat', label: 'Consultation', icon: MessageCircleHeart },
  { href: '/analysis', label: 'Analytics', icon: BarChart3 },
  { href: '/injury-analysis', label: 'Injury Scan', icon: ScanLine },
  { href: '/profile', label: 'Profile', icon: User },
];

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { signOut } = useAuth();

  const handleLogout = async () => {
    await signOut();
    router.push('/');
  };

  return (
    <div className={styles.sidebarInner}>
      <div className={styles.sidebarTop}>
        <Logo size="md" />
      </div>

      <nav className={styles.nav} aria-label="Primary">
        {NAV.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + '/');
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(styles.navItem, active && styles.navItemActive)}
              aria-current={active ? 'page' : undefined}
            >
              {active && (
                <motion.span
                  layoutId="nav-active"
                  className={styles.navActiveBg}
                  transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                />
              )}
              <span className={styles.navIcon}>
                <Icon size={20} strokeWidth={2.2} />
              </span>
              <span className={styles.navLabel}>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className={styles.sidebarFooter}>
        <ThemeToggle />
        <button type="button" onClick={handleLogout} className={styles.logoutBtn}>
          <LogOut size={18} />
          <span>Sign out</span>
        </button>
      </div>
    </div>
  );
}
