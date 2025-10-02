import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  basePath: '/k9',
  assetPrefix: '/k9',
  images: {
    unoptimized: true
  }
};

export default nextConfig;
