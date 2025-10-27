import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Person Detection Dashboard',
  description: 'Real-time person detection monitoring',
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
