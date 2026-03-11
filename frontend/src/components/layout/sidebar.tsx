"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { clsx } from "clsx"
import { LayoutDashboard, FolderOpen, KeyRound } from "lucide-react"
import { useI18n } from "@/lib/i18n"
import { UserMenu } from "./user-menu"
import { useEffect, useState } from "react"
import { api } from "@/lib/api"

export function Sidebar() {
  const pathname = usePathname()
  const { t } = useI18n()
  const [email, setEmail] = useState<string | undefined>()
  const [avatarUrl, setAvatarUrl] = useState<string | undefined>()

  useEffect(() => {
    api.users.me().then(u => { setEmail(u.email); setAvatarUrl(u.avatar_url) }).catch(() => null)
  }, [])

  const nav = [
    { href: "/dashboard",    label: t("dashboard"),    icon: LayoutDashboard },
    { href: "/projects",     label: t("projects"),     icon: FolderOpen },
    { href: "/credentials",  label: "Credentials",     icon: KeyRound },
  ]

  return (
    <aside className="w-60 bg-surface border-r bd1 flex flex-col h-screen sticky top-0 shrink-0">
      <div className="px-6 py-5 border-b bd1">
        <Link href="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-12 h-12 rounded-lg overflow-hidden">
            <img src="/img/logo-w-bg.png" alt="Archon" className="w-full h-full object-cover" />
          </div>
          <span className="t1 font-semibold text-lg">Archon</span>
        </Link>
        <p className="t4 text-xs mt-1">AI System Auditor</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
              pathname.startsWith(href)
                ? "bg-archon-500/20 text-archon-400"
                : "t3 hover-muted hover-t1"
            )}
          >
            <Icon className="w-4 h-4" />
            {label}
          </Link>
        ))}
      </nav>

      <div className="px-3 py-4 border-t bd1">
        <UserMenu email={email} avatarUrl={avatarUrl} />
      </div>
    </aside>
  )
}
