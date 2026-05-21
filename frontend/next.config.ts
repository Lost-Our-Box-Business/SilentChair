import type { NextConfig } from "next";

const ROOT_DOMAIN = process.env.NEXT_PUBLIC_ROOT_DOMAIN ?? "silentchair.app";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      // Rewrite *.silentchair.app/* → /site/[subdomain]/* for non-Vercel environments
      // (Vercel handles this via middleware; this covers local dev with custom hosts)
      {
        source: "/:path*",
        has: [
          {
            type: "host",
            value: `(?<subdomain>(?!www$)[^.]+)\\.${ROOT_DOMAIN.replace(".", "\\.")}`,
          },
        ],
        destination: "/site/:subdomain/:path*",
      },
    ];
  },
};

export default nextConfig;
