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
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    // In production, proxy /api/v1/* through Vercel to the backend.
    // This completely eliminates CORS issues and avoids browser preflight overhead.
    if (apiUrl && apiUrl !== "http://localhost:8000" && apiUrl !== "http://127.0.0.1:8000") {
      return [
        {
          source: "/api/v1/:path*",
          destination: `${apiUrl}/api/v1/:path*`,
        },
      ];
    }
    return [];
  },
};

export default nextConfig;
