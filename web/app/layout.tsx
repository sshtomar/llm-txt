import type { Metadata } from 'next'
import './globals.css'
import { Header } from '@/components/header'

export const metadata: Metadata = {
  title: 'LLM.txt Generator',
  description: 'Generate optimized llm.txt files from documentation sites',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-mono bg-black text-terminal-green min-h-screen">
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="flex-1 container mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="border-t border-terminal-green/30 py-4 text-center text-sm text-terminal-green/70">
            <p>© 2024 LLM.txt Generator | Optimized for LLM context windows</p>
          </footer>
        </div>
      </body>
    </html>
  )
}