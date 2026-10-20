const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const storage = supabaseUrl ? new URL(supabaseUrl) : null

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Preserve the original hosting path; set to an empty string for root hosting.
  basePath: process.env.NEXT_PUBLIC_BASE_PATH ?? '/ghostbusters',
  images: {
    remotePatterns: storage ? [{
      protocol: storage.protocol.replace(':', ''),
      hostname: storage.hostname,
      port: storage.port,
      pathname: '/storage/v1/object/public/detection-images/**',
    }] : [],
  },
}

module.exports = nextConfig
