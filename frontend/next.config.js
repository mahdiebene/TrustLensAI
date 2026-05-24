/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    API_URL: process.env.API_URL || "http://107.161.168.216:8000",
  },
};

module.exports = nextConfig;
