"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"
import { setToken } from "@/lib/auth"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 48 48" fill="none">
    <path d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 7.9 3l5.7-5.7C34.5 6.5 29.6 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.2-.1-2.4-.4-3.5z" fill="#FFC107"/>
    <path d="M6.3 14.7l6.6 4.8C14.6 16.1 19 13 24 13c3.1 0 5.8 1.1 7.9 3l5.7-5.7C34.5 6.5 29.6 4 24 4c-7.7 0-14.3 4.4-17.7 10.7z" fill="#FF3D00"/>
    <path d="M24 44c5.4 0 10.2-2 13.8-5.3l-6.4-5.4C29.5 35 26.9 36 24 36c-5.3 0-9.7-3.3-11.3-7.9l-6.6 5.1C9.5 39.5 16.2 44 24 44z" fill="#4CAF50"/>
    <path d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4-4.1 5.3l6.4 5.4C37.5 38.8 44 34 44 24c0-1.2-.1-2.4-.4-3.5z" fill="#1976D2"/>
  </svg>
)

export default function RegisterPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.origin !== API_URL) return
      if (event.data?.type === "oauth_success" && event.data?.token) {
        setToken(event.data.token)
        router.push("/dashboard")
      }
    }
    window.addEventListener("message", handleMessage)
    return () => window.removeEventListener("message", handleMessage)
  }, [router])

  function handleGoogleLogin() {
    const w = 500, h = 600
    const left = window.screenX + (window.outerWidth - w) / 2
    const top = window.screenY + (window.outerHeight - h) / 2
    window.open(
      `${API_URL}/api/v1/auth/google`,
      "google-oauth",
      `width=${w},height=${h},left=${left},top=${top},toolbar=no,menubar=no`
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(""); setLoading(true)
    try {
      const res = await api.auth.register(email, password)
      setToken(res.access_token)
      router.push("/dashboard")
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Registration failed")
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-page flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="mx-auto mb-4 w-24 h-24 rounded-2xl overflow-hidden">
            <img src="/img/logo-w-bg.png" alt="Archon" className="w-full h-full object-cover" />
          </div>
          <h1 className="text-2xl font-bold t1">Create account</h1>
          <p className="t3 mt-1">Start auditing your systems</p>
        </div>

        <div className="bg-card border bd1 rounded-xl p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div><Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required autoFocus />
            </div>
            <div><Label htmlFor="password">Password</Label>
              <Input id="password" type="password" placeholder="Min. 8 characters" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} />
            </div>
            {error && <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-500 text-sm">{error}</div>}
            <Button type="submit" className="w-full" loading={loading}>Create account</Button>
          </form>

          <div className="flex items-center gap-3 my-4">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-xs t3">or</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          <button
            onClick={handleGoogleLogin}
            className="flex items-center justify-center gap-3 w-full border bd1 rounded-lg px-4 py-2.5 text-sm font-medium t1 hover:bg-white/5 transition-colors"
          >
            <GoogleIcon />
            Continue with Google
          </button>
        </div>

        <p className="text-center t3 text-sm mt-4">
          Already have an account?{" "}
          <Link href="/login" className="text-archon-400 hover:text-archon-300">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
