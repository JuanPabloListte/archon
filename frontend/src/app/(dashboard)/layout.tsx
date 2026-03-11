"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Sidebar } from "@/components/layout/sidebar"
import { isAuthenticated } from "@/lib/auth"
import { Spinner } from "@/components/ui/spinner"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    if (!isAuthenticated()) router.replace("/login")
    else setChecking(false)
  }, [router])

  if (checking) return (
    <div className="flex min-h-screen bg-page items-center justify-center">
      <Spinner />
    </div>
  )

  return (
    <div className="flex min-h-screen bg-page">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto">{children}</main>
    </div>
  )
}
