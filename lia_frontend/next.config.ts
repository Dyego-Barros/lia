import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: false,
  output: "standalone",
  // Keep the API's trailing slash when the request is proxied to FastAPI.
  // Otherwise Next.js emits a 308 before the rewrite and FastAPI emits a
  // second redirect to its internal Docker hostname.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      // FastAPI declares collection routes with a trailing slash. Next.js
      // normalizes the public URL before applying the generic rewrite, so
      // keep these destinations explicit to avoid a redirect to api:8000.
      { source: "/api/clientes", destination: "http://api:8000/clientes/" },
      { source: "/api/procedimentos", destination: "http://api:8000/procedimentos/" },
      { source: "/api/agendamentos", destination: "http://api:8000/agendamentos/" },
      { source: "/api/:path*", destination: "http://api:8000/:path*" },
      // FastAPI's Swagger HTML requests this absolute path without /api.
      { source: "/openapi.json", destination: "http://api:8000/openapi.json" },
    ];
  },
  async headers() {
    return [{ source: "/(.*)", headers: [
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "X-Frame-Options", value: "DENY" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
      { key: "Content-Security-Policy", value: "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'" },
    ] }];
  },
};

export default nextConfig;
