"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AuthShell } from "@/components/auth/AuthShell";
import { GoogleSignInButton } from "@/components/auth/GoogleSignInButton";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { GOOGLE_CLIENT_ID, loginWithGoogle, loginWithPassword, signup } from "@/lib/auth";
import styles from "../auth.module.css";

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      await signup({ email, password, full_name: name });
      // Auto-login so the user lands on the dashboard, not a second screen.
      await loginWithPassword(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create your account.");
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
      eyebrow="Get started"
      title="Create your MediHealth account"
      subtitle="Use email and password, or continue with Google — no credit card required."
      footer={
        <>
          Already have an account?<Link href="/login">Sign in</Link>
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

      <form className={styles.form} onSubmit={handleSignup}>
        <Input
          label="Full name"
          type="text"
          placeholder="Dr. Jane Smith"
          autoComplete="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
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
          placeholder="At least 8 characters"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
          required
        />
        <Button type="submit" fullWidth isLoading={isLoading} size="large" style={{ marginTop: "0.75rem" }}>
          Create account
        </Button>
      </form>

      {GOOGLE_CLIENT_ID ? (
        <>
          <div className={styles.divider}>or</div>
          <GoogleSignInButton onCredential={handleGoogle} onError={setError} text="signup_with" />
        </>
      ) : null}
    </AuthShell>
  );
}
