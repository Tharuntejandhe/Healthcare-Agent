import type { Metadata, Viewport } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/Toaster";
import { MotionProvider } from "@/components/providers/MotionProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "MediHealth — Intelligent Care Companion",
    template: "%s · MediHealth",
  },
  description:
    "MediHealth is an AI-powered care orchestration platform that combines medical reasoning, vision triage, and personalized insights.",
  applicationName: "MediHealth",
  icons: {
    icon: "/favicon.ico",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#e7f0ee" },
    { media: "(prefers-color-scheme: dark)", color: "#07181a" },
  ],
  width: "device-width",
  initialScale: 1,
};

// Set the theme class on <html> BEFORE the body renders to avoid a flash of
// the wrong palette. Defaults to the user's OS preference.
const themeScript = `
  (function(){
    try {
      var saved = localStorage.getItem('theme');
      var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      var theme = saved || (prefersDark ? 'dark' : 'light');
      if (theme === 'dark') document.documentElement.classList.add('dark');
    } catch (e) {}
  })();
`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    // suppressHydrationWarning: themeScript adds the `dark` class to <html>
    // before hydration to avoid a flash of the wrong palette, so the html
    // attributes intentionally differ from the server render.
    <ClerkProvider>
      <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`} suppressHydrationWarning>
        <head>
          <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        </head>
        <body>
          <div className="mesh-bg" aria-hidden="true" />
          <MotionProvider>{children}</MotionProvider>
          <Toaster />
        </body>
      </html>
    </ClerkProvider>
  );
}
