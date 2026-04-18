import type { NextConfig } from "next";

// BACKEND_URL lets Docker / production deployments point at the correct host.
// Defaults to localhost for local development without Docker.
const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

// Baseline security headers applied to every frontend response.
// Mirrors the backend middleware so worldoftaxonomy.com and the API
// present a consistent posture to browsers and scanners.
const securityHeaders = [
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "geolocation=(), microphone=(), camera=()",
  },
];

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
  // Prevent remark and its plugins from being bundled (they are Node-only)
  serverExternalPackages: ['remark', 'remark-gfm', 'remark-html'],
};

export default nextConfig;
