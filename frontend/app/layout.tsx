import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Analytical Trading Dashboard',
  description: 'Next.js frontend for stock analysis and strategy visualization'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
