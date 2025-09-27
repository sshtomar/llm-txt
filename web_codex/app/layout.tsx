import './globals.css'
import React from 'react'

export const metadata = {
  title: 'llms.txt Generator',
  description: 'Crawl docs and compose optimized llms.txt files',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className="scroll-smooth dark">
      <head>
        <meta name="color-scheme" content="dark" />
        <link rel="preload" href="/fonts/BerkeleyMono-Variable.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <meta name="theme-color" content="#0b0b0c" />
      </head>
      <body className="min-h-screen bg-[var(--bg)] text-[var(--fg)] font-mono">
        {children}
      </body>
    </html>
  )
}
