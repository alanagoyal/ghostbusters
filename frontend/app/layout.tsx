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
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `try{var t=new URLSearchParams(location.search).get("theme")||(location.pathname.match(/\\/theme\\/([a-z]+)/)||[])[1];if(t)document.documentElement.dataset.theme=t}catch(e){}` }} />
      </head>
      <body className={GeistMono.className}>{children}
        <footer className="p-4 text-center text-xs text-muted-foreground">
          <a href={process.env.NEXT_PUBLIC_SOURCE_URL || "https://github.com/alanagoyal/ghostbusters"}
            target="_blank" rel="noopener noreferrer">Source · AGPL-3.0</a>
        </footer>
      </body>
    </html>
  )
}
