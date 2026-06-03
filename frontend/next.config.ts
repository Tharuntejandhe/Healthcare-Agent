import type { NextConfig } from "next";

// Security headers applied to every response. Note camera + microphone are
// allowed for same-origin because the consultation page uses getUserMedia.
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(self), microphone=(self), geolocation=()",
  },
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: process.cwd(),
  turbopack: { root: process.cwd() },
  poweredByHeader: false,
  images: {
    remotePatterns: [
      // Google profile pictures (for accounts created via Google sign-in).
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
    ],
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
