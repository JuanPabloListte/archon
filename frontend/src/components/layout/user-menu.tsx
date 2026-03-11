"use client"

import { useState, useRef, useEffect } from "react"
import { useRouter } from "next/navigation"
import { User, LogOut, ChevronUp, Sun, Moon, Monitor } from "lucide-react"
import { removeToken } from "@/lib/auth"
import { useI18n } from "@/lib/i18n"
import { useTheme, Theme } from "@/lib/theme"
import { ProfileModal } from "./profile-modal"

export function UserMenu({ email, avatarUrl }: { email?: string; avatarUrl?: string }) {
  const [open, setOpen] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const { t } = useI18n()
  const { theme, setTheme } = useTheme()

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  function logout() {
    removeToken()
    router.push("/login")
  }

  const initials = email ? email[0].toUpperCase() : "U"

  const themes: { value: Theme; icon: React.ReactNode; label: string }[] = [
    { value: "dark",   icon: <Moon className="w-3.5 h-3.5" />,    label: t("themeDark") },
    { value: "light",  icon: <Sun className="w-3.5 h-3.5" />,     label: t("themeLight") },
    { value: "system", icon: <Monitor className="w-3.5 h-3.5" />, label: t("themeSystem") },
  ]

  return (
    <>
      <div ref={ref} className="relative">
        <button
          onClick={() => setOpen(o => !o)}
          className="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg hover-muted transition-colors"
        >
          <div className="w-7 h-7 rounded-full bg-archon-500/30 border border-archon-500/40 flex items-center justify-center shrink-0 overflow-hidden">
            {avatarUrl
              ? <img src={avatarUrl} alt={email} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
              : <span className="text-archon-400 text-xs font-bold">{initials}</span>
            }
          </div>
          <div className="flex-1 text-left min-w-0">
            <p className="t1 text-xs font-medium truncate">{email || "User"}</p>
          </div>
          <ChevronUp className={`w-3.5 h-3.5 t4 transition-transform ${open ? "" : "rotate-180"}`} />
        </button>

        {open && (
          <div className="absolute bottom-full left-0 right-0 mb-1 bg-surface border bd1 rounded-xl shadow-2xl overflow-hidden z-50">
            <button
              onClick={() => { setShowProfile(true); setOpen(false) }}
              className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm t2 hover-muted transition-colors"
            >
              <User className="w-4 h-4 text-archon-400" />
              {t("profile")}
            </button>

            <div className="border-t bd1 mx-3" />

            <div className="px-4 py-2">
              <p className="t4 text-xs font-medium mb-1.5">{t("theme")}</p>
              <div className="flex gap-1">
                {themes.map(({ value, icon, label }) => (
                  <button
                    key={value}
                    onClick={() => setTheme(value)}
                    title={label}
                    className={`flex-1 flex flex-col items-center gap-1 py-2 rounded-lg text-xs transition-colors ${
                      theme === value
                        ? "bg-archon-500/20 text-archon-400 border border-archon-500/40"
                        : "t3 hover-muted border border-transparent"
                    }`}
                  >
                    {icon}
                    <span className="text-[10px]">{label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="border-t bd1 mx-3" />

            <button
              onClick={logout}
              className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm t3 hover:text-red-500 hover-muted transition-colors"
            >
              <LogOut className="w-4 h-4" />
              {t("signOut")}
            </button>
          </div>
        )}
      </div>

      {showProfile && <ProfileModal onClose={() => setShowProfile(false)} />}
    </>
  )
}
