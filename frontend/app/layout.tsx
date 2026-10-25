import './globals.css'
import type { Metadata } from 'next'
import { GeistMono } from 'geist/font/mono'

export const metadata: Metadata = {
  title: 'Ghostbusters',
  description: 'Camera detections and Halloween costume guesses',
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
