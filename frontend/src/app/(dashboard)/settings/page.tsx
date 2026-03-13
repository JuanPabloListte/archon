"use client"

import { useEffect, useState } from "react"
import { createPortal } from "react-dom"
import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Spinner } from "@/components/ui/spinner"
import { api } from "@/lib/api"
import { ApiKey } from "@/types"
import { Key, Plus, Trash2, Copy, CheckCircle, AlertTriangle, X, BookOpen } from "lucide-react"

const CICD_EXAMPLE = `- name: Archon Audit Check
  run: |
    curl -s -X POST \\
      https://your-archon.com/api/v1/projects/PROJECT_ID/audit/check \\
      -H "X-API-Key: \${{ secrets.ARCHON_API_KEY }}" \\
      -H "Content-Type: application/json" \\
      -d '{"threshold": 70, "fail_on": ["critical"]}' | \\
      python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d['status']=='pass' else 1)"`

function ExampleModal({ onClose }: { onClose: () => void }) {
  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-surface border bd1 rounded-2xl w-full max-w-3xl mx-4 shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b bd1">
          <h2 className="t1 font-semibold">CI/CD Usage Example</h2>
          <button onClick={onClose} className="t3 hover-t1 transition-colors"><X className="w-5 h-5" /></button>
        </div>
        <div className="px-6 py-5 space-y-4">
          <p className="text-sm t3">Add this step to your <span className="text-archon-400 font-medium">GitHub Actions</span> workflow. The step fails if the health score drops below the threshold or critical findings are detected.</p>
          <pre className="bg-muted rounded-xl p-4 text-xs font-mono t2 overflow-x-auto whitespace-pre leading-relaxed">{CICD_EXAMPLE}</pre>
          <div className="text-xs t4 space-y-1">
            <p><span className="text-archon-400">threshold</span> — minimum acceptable health score (0–100)</p>
            <p><span className="text-archon-400">fail_on</span> — severities that cause failure regardless of score</p>
          </div>
        </div>
      </div>
    </div>,
    document.body
  )
}

export default function SettingsPage() {
  const [keys, setKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [keyName, setKeyName] = useState("")
  const [creating, setCreating] = useState(false)
  const [newToken, setNewToken] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [showExample, setShowExample] = useState(false)

  useEffect(() => {
    api.apiKeys.list().then(setKeys).finally(() => setLoading(false))
  }, [])

  async function createKey(e: React.FormEvent) {
    e.preventDefault()
    if (!keyName.trim()) return
    setCreating(true)
    try {
      const created = await api.apiKeys.create(keyName.trim())
      setNewToken(created.token)
      setKeys(prev => [...prev, created])
      setKeyName("")
      setShowForm(false)
    } finally {
      setCreating(false)
    }
  }

  async function revokeKey(id: string) {
    if (!confirm("Revoke this API key? It will stop working immediately.")) return
    await api.apiKeys.revoke(id)
    setKeys(prev => prev.filter(k => k.id !== id))
  }

  function copyToken() {
    if (!newToken) return
    navigator.clipboard.writeText(newToken)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>

  return (
    <div>
      <Header title="API Keys" subtitle="Manage API keys for CI/CD and programmatic access" />

      {showExample && <ExampleModal onClose={() => setShowExample(false)} />}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Key className="w-4 h-4 text-archon-400" />
              <CardTitle>API Keys</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowExample(true)}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border bd1 t3 hover-t1 transition-colors"
              >
                <BookOpen className="w-3.5 h-3.5" />
                CI/CD Example
              </button>
              <Button size="sm" onClick={() => setShowForm(v => !v)}>
                <Plus className="w-4 h-4 mr-1" />New Key
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm t3 mb-4">
            Use API keys to authenticate CI/CD pipelines. Pass them as <code className="bg-muted px-1 rounded text-archon-400">X-API-Key</code> header.
          </p>

          {newToken && (
            <div className="mb-4 p-4 rounded-xl border border-yellow-500/30 bg-yellow-500/5">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-yellow-500" />
                <p className="text-sm font-medium text-yellow-400">Copy your key now — it won't be shown again</p>
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-muted rounded-lg px-3 py-2 text-sm font-mono t1 break-all">{newToken}</code>
                <Button size="sm" variant="secondary" onClick={copyToken}>
                  {copied ? <CheckCircle className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                </Button>
              </div>
              <button onClick={() => setNewToken(null)} className="mt-2 text-xs t4 hover-t1 transition-colors">Dismiss</button>
            </div>
          )}

          {showForm && (
            <form onSubmit={createKey} className="mb-4 flex gap-2">
              <Input
                value={keyName}
                onChange={e => setKeyName(e.target.value)}
                placeholder='e.g. "GitHub Actions — Production"'
                className="flex-1"
                autoFocus
                required
              />
              <Button type="submit" loading={creating}>Create</Button>
              <Button type="button" variant="secondary" onClick={() => setShowForm(false)}>Cancel</Button>
            </form>
          )}

          {keys.length === 0 ? (
            <p className="text-sm t4 text-center py-6">No API keys yet.</p>
          ) : (
            <div className="space-y-2">
              {keys.map(k => (
                <div key={k.id} className="flex items-center gap-3 px-3 py-2.5 bg-muted rounded-lg text-sm">
                  <Key className="w-4 h-4 t4 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="t1 font-medium">{k.name}</p>
                    <p className="t4 text-xs font-mono">{k.key_prefix}••••••••</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs t4">{k.last_used_at ? `Last used ${new Date(k.last_used_at).toLocaleDateString()}` : "Never used"}</p>
                    <p className="text-xs t4">Created {new Date(k.created_at).toLocaleDateString()}</p>
                  </div>
                  <button onClick={() => revokeKey(k.id)} className="t4 hover:text-red-500 transition-colors ml-1" title="Revoke key">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
