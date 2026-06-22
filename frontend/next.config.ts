import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

const ROOT_DOMAIN = process.env.NEXT_PUBLIC_ROOT_DOMAIN ?? "silentchair.app";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
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

export default withNextIntl(nextConfig);
