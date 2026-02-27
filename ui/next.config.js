/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: __dirname
  },
  output: "standalone",
  typescript: {
    ignoreBuildErrors: false
  }
};

module.exports = nextConfig;
