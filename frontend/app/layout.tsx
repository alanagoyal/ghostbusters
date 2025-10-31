import './globals.css'
import type { Metadata } from 'next'
import { GeistMono } from 'geist/font/mono'

export const metadata: Metadata = {
  title: 'Ghostbusters',
  description: 'A live classification of trick-or-treaters in San Francisco',
  openGraph: {
    title: 'Ghostbusters',
    description: 'A live classification of trick-or-treaters in San Francisco',
    images: ['/api/og'],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Ghostbusters',
    description: 'A live classification of trick-or-treaters in San Francisco',
    images: ['/api/og'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={GeistMono.className}>{children}</body>
    </html>
  )
}
