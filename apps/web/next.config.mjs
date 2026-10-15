/** @type {import('next').NextConfig} */

const isProd = process.env.NODE_ENV === "production";

function resolveOrigin(rawUrl) {
  if (!rawUrl || !rawUrl.startsWith("http")) return null;
  try {
    return new URL(rawUrl).origin;
  } catch {
    return null;
  }
}

const apiOrigin = resolveOrigin(process.env.NEXT_PUBLIC_API_URL);

// Prod: same-origin only (API is proxied through the /api/v1 rewrite) plus the
// optional absolute NEXT_PUBLIC_API_URL origin. Dev additionally allows the
// HMR websocket and any local backend so `next dev` never breaks.
const connectSrc = isProd
  ? ["'self'", apiOrigin].filter(Boolean).join(" ")
  : ["'self'", "ws:", "wss:", "http:", "https:", apiOrigin].filter(Boolean).join(" ");

const contentSecurityPolicy = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isProd ? "" : " 'unsafe-eval'"}`,
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com",
  "img-src 'self' blob: data: https:",
  "media-src 'self' blob: https:",
  `connect-src ${connectSrc}`,
  "frame-src 'self' https:",
  "worker-src 'self' blob:",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: contentSecurityPolicy },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
];

const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.API_BASE_URL || "http://127.0.0.1:8000"}/api/v1/:path*`,
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
};

export default nextConfig;
