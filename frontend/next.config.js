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
  async headers() {
    return [
      {
        // Cache the main page in the browser for 60s, stale-while-revalidate for 5min
        source: '/',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, s-maxage=300, stale-while-revalidate=600',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig
