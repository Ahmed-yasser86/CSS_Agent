import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // This UI lives in a repo that also contains unrelated lockfiles; pin the
  // Turbopack workspace root to this directory.
  turbopack: {
    root: __dirname,
  },
  // Proxy the SocialScienceResearch FastAPI backend during development and
  // deployment so the browser never needs to talk cross-origin.
  // Start the backend with: uvicorn SocialScienceResearch.api:create_app --factory
  async rewrites() {
    return [
      {
        source: "/api/v1/social-science/:path*",
        destination: `${process.env.BACKEND_URL ?? "http://127.0.0.1:8000"}/api/v1/social-science/:path*`,
      },
    ];
  },
};

export default nextConfig;
