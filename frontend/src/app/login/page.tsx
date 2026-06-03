"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AuthShell } from "@/components/auth/AuthShell";
import { GoogleSignInButton } from "@/components/auth/GoogleSignInButton";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { GOOGLE_CLIENT_ID, loginWithGoogle, loginWithPassword } from "@/lib/auth";
import styles from "../auth.module.css";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      await loginWithPassword(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogle = async (idToken: string) => {
    setError("");
    setIsLoading(true);
    try {
      await loginWithGoogle(idToken);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google sign-in failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Welcome back"
      title="Sign in to MediHealth"
      subtitle="Pick up where you left off — your dashboard is waiting."
      footer={
        <>
          New here?<Link href="/signup">Create an account</Link>
        </>
      }
    >
      {error && (
        <div className={styles.errorAlert} role="alert">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      <form className={styles.form} onSubmit={handleLogin}>
        <Input
          label="Email address"
          type="email"
          placeholder="you@clinic.com"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Input
          label="Password"
          type="password"
          placeholder="••••••••"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <Button type="submit" fullWidth isLoading={isLoading} size="large" style={{ marginTop: "0.75rem" }}>
          Sign in
        </Button>
      </form>

      {GOOGLE_CLIENT_ID ? (
        <>
          <div className={styles.divider}>or</div>
          <GoogleSignInButton onCredential={handleGoogle} onError={setError} text="signin_with" />
        </>
      ) : null}
    </AuthShell>
  );
}
