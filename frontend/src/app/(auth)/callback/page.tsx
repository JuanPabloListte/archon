"use client"

import { useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { setToken } from "@/lib/auth"

export default function AuthCallbackPage() {
  const router = useRouter()
  const params = useSearchParams()

  useEffect(() => {
    const token = params.get("token")
    if (token) {
      setToken(token)
      router.push("/dashboard")
    } else {
      router.push("/login?error=oauth_failed")
    }
  }, [params, router])

  return (
    <div className="min-h-screen bg-page flex items-center justify-center">
      <p className="t3">Signing you in...</p>
    </div>
  )
}
