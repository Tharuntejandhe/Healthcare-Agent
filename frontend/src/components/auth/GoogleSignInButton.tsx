"use client";

import { useEffect, useRef } from "react";

import { GOOGLE_CLIENT_ID } from "@/lib/auth";

interface GoogleSignInButtonProps {
  onCredential: (idToken: string) => void;
  onError?: (msg: string) => void;
  text?: "signin_with" | "signup_with" | "continue_with";
}

// Module-scoped promise so the GIS script is only injected once even if
// several instances of this component mount during a session.
let gisLoaderPromise: Promise<void> | null = null;

function loadGoogleScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if ((window as any).google?.accounts?.id) return Promise.resolve();
  if (gisLoaderPromise) return gisLoaderPromise;

  gisLoaderPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(
      'script[src="https://accounts.google.com/gsi/client"]',
    );
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener(
        "error",
        () => reject(new Error("Failed to load Google Identity Services")),
        { once: true },
      );
      return;
    }
    const s = document.createElement("script");
    s.src = "https://accounts.google.com/gsi/client";
    s.async = true;
    s.defer = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Failed to load Google Identity Services"));
    document.head.appendChild(s);
  });
  return gisLoaderPromise;
}

export function GoogleSignInButton({
  onCredential,
  onError,
  text = "continue_with",
}: GoogleSignInButtonProps) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  // Keep latest callbacks in refs so the init effect can run only once.
  const onCredentialRef = useRef(onCredential);
  const onErrorRef = useRef(onError);
  onCredentialRef.current = onCredential;
  onErrorRef.current = onError;

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      onErrorRef.current?.(
        "Google sign-in is not configured. Set NEXT_PUBLIC_GOOGLE_CLIENT_ID and restart the dev server.",
      );
      return;
    }

    let cancelled = false;
    let resizeObserver: ResizeObserver | null = null;

    loadGoogleScript()
      .then(() => {
        if (cancelled || !hostRef.current) return;
        const g = (window as any).google;
        g.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: (response: { credential?: string }) => {
            if (response?.credential) onCredentialRef.current(response.credential);
            else onErrorRef.current?.("No credential returned from Google.");
          },
        });

        const render = () => {
          if (!hostRef.current) return;
          const width = Math.min(
            400,
            Math.max(240, Math.floor(hostRef.current.getBoundingClientRect().width)),
          );
          hostRef.current.innerHTML = "";
          g.accounts.id.renderButton(hostRef.current, {
            type: "standard",
            theme: "outline",
            size: "large",
            text,
            shape: "pill",
            logo_alignment: "left",
            width,
          });
        };

        render();

        // Keep the button width in sync with the form column.
        resizeObserver = new ResizeObserver(() => render());
        resizeObserver.observe(hostRef.current);
      })
      .catch((err) => {
        onErrorRef.current?.(err?.message ?? "Failed to load Google sign-in.");
      });

    return () => {
      cancelled = true;
      resizeObserver?.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{ width: "100%", display: "flex", justifyContent: "center" }}>
      <div ref={hostRef} style={{ width: "100%" }} />
    </div>
  );
}
