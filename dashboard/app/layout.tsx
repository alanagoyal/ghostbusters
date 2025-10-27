import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Halloween Dashboard - Trick-or-Treater Analytics',
  description: 'Real-time Halloween trick-or-treater monitoring with costume analytics and visitor insights',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
