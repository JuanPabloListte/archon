import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Archon — AI System Auditor",
  description: "Automated AI auditing for backend systems",
  icons: {
    icon: "/img/logo-w-bg.png",
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
