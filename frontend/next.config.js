/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/ghostbusters',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'szsjlqaxcznegnjflogo.supabase.co',
        pathname: '/storage/v1/object/public/**',
      },
    ],
  },
};

module.exports = nextConfig
