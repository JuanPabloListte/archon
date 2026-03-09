"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"
import { setToken } from "@/lib/auth"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      const res = await api.auth.login(email, password)
      setToken(res.access_token)
      router.push("/dashboard")
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="mx-auto mb-4 w-24 h-24">
            <img src="/img/logo-w-bg.png" alt="Archon" className="w-full h-full" style={{ mixBlendMode: "screen" }} />
          </div>
          <h1 className="text-2xl font-bold text-white">Sign in to Archon</h1>
          <p className="text-gray-400 mt-1">AI System Auditor</p>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>
            {error && (
              <div className="bg-red-900/40 border border-red-800 rounded-lg p-3 text-red-400 text-sm">
                {error}
              </div>
            )}
            <Button type="submit" className="w-full" loading={loading}>
              Sign in
            </Button>
          </form>
        </div>

        <p className="text-center text-gray-400 text-sm mt-4">
          No account?{" "}
          <Link href="/register" className="text-archon-400 hover:text-archon-300">
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}
