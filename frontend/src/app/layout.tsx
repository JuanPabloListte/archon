import type { Metadata } from "next"
import "./globals.css"
import { I18nProvider } from "@/lib/i18n"
import { ThemeProvider } from "@/lib/theme"

export const metadata: Metadata = {
  title: "Archon — AI System Auditor",
  description: "Automated AI auditing for backend systems",
  icons: {
    icon: "/img/logo-w-bg.png",
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" className="dark">
      <body>
        <ThemeProvider>
          <I18nProvider>
            {children}
          </I18nProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
