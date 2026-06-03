import { extractErrorMessage, getApiUrl } from "./api";

export const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

const TOKEN_KEY = "access_token"; // existing app reads this exact key

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

/** Remove any PHI that older builds cached in localStorage (defense in depth). */
export function purgeLegacyPhi(): void {
  if (typeof window === "undefined") return;
  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith("patient_reports_"))
      .forEach((k) => localStorage.removeItem(k));
  } catch {
    /* ignore */
  }
}

/**
 * Sign out everywhere it matters: revoke the token server-side (so a stolen
 * copy is useless), then clear all local state. Best-effort on the network call
 * — we always clear locally even if the request fails.
 */
export async function logout(): Promise<void> {
  const token = getToken();
  if (token) {
    try {
      await fetch(getApiUrl("/api/v1/auth/logout"), {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        keepalive: true,
      });
    } catch {
      /* best-effort */
    }
  }
  clearToken();
  purgeLegacyPhi();
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function loginWithPassword(email: string, password: string): Promise<TokenResponse> {
  // OAuth2PasswordRequestForm wants application/x-www-form-urlencoded with username/password
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(getApiUrl("/api/v1/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, "Invalid email or password."));
  }
  const data: TokenResponse = await res.json();
  setToken(data.access_token);
  return data;
}

export async function signup(payload: {
  email: string;
  password: string;
  full_name?: string;
}): Promise<{ id: number; email: string }> {
  const res = await fetch(getApiUrl("/api/v1/auth/signup"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, "Could not create account."));
  }
  return res.json();
}

export async function loginWithGoogle(idToken: string): Promise<TokenResponse> {
  const res = await fetch(getApiUrl("/api/v1/auth/google"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken }),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, "Google sign-in failed."));
  }
  const data: TokenResponse = await res.json();
  setToken(data.access_token);
  return data;
}
