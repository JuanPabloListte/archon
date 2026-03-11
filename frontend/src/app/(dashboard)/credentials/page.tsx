"use client"

import { useState, useEffect, useRef } from "react"
import { Plus, Trash2, CheckCircle2, Circle, Pencil, X, Eye, EyeOff, CircleOff } from "lucide-react"
import { api } from "@/lib/api"
import { Credential } from "@/types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

// ── Provider icons (SVG) ──────────────────────────────────────────────────────
const ProviderIcons: Record<string, React.FC<{ size?: number }>> = {
  anthropic: ({ size = 20 }) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
    >
      <path d="M16.7645 5H13.4568L19.3799 20H22.6107L16.7645 5ZM7.22604 5L1.37988 20H4.68758L5.99527 16.8462H12.1491L13.3799 19.9231H16.6876L10.6876 5H7.30296H7.22604ZM6.91834 14.0769L8.91834 8.76923L10.9953 14.0769H6.99527H6.91834Z" />
    </svg>
  ),
  openai: ({ size = 20 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M22.28 9.93a5.77 5.77 0 0 0-.5-4.73 5.9 5.9 0 0 0-6.36-2.83A5.9 5.9 0 0 0 11 .63a5.9 5.9 0 0 0-5.62 4.08 5.9 5.9 0 0 0-3.94 2.87 5.9 5.9 0 0 0 .73 6.9 5.77 5.77 0 0 0 .5 4.73 5.9 5.9 0 0 0 6.36 2.83A5.88 5.88 0 0 0 13 23.37a5.9 5.9 0 0 0 5.63-4.09 5.9 5.9 0 0 0 3.93-2.86 5.9 5.9 0 0 0-.28-6.49zM13 21.77a4.37 4.37 0 0 1-2.8-1.02l.14-.08 4.65-2.68a.76.76 0 0 0 .38-.66v-6.55l1.97 1.14a.07.07 0 0 1 .04.05v5.42A4.41 4.41 0 0 1 13 21.77zM3.55 17.9a4.37 4.37 0 0 1-.52-2.96l.14.08 4.65 2.68a.75.75 0 0 0 .76 0l5.68-3.28v2.27a.07.07 0 0 1-.03.06L9.5 19.4A4.41 4.41 0 0 1 3.55 17.9zm-1.14-9.6a4.37 4.37 0 0 1 2.28-1.92v5.51a.75.75 0 0 0 .38.65l5.67 3.27-1.97 1.14a.07.07 0 0 1-.07 0L4.1 14.3a4.41 4.41 0 0 1-1.69-6zm16.2 3.79-5.68-3.28 1.97-1.14a.07.07 0 0 1 .07 0l4.59 2.65a4.4 4.4 0 0 1-.68 7.94v-5.52a.76.76 0 0 0-.27-.65zm1.96-3-.14-.08-4.64-2.7a.76.76 0 0 0-.76 0L9.35 9.6V7.33a.07.07 0 0 1 .03-.06l4.59-2.65a4.4 4.4 0 0 1 6.6 4.57zM8.28 12.9 6.3 11.76a.07.07 0 0 1-.04-.06V6.3a4.4 4.4 0 0 1 7.22-3.38l-.14.08L8.7 5.68a.75.75 0 0 0-.38.65l-.04 6.57zm1.07-2.3 2.53-1.46 2.52 1.45v2.9l-2.52 1.46-2.53-1.46v-2.9z" />
    </svg>
  ),
  gemini: ({ size = 20 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path d="M12 2C12 2 14.5 9.5 22 12C14.5 14.5 12 22 12 22C12 22 9.5 14.5 2 12C9.5 9.5 12 2 12 2Z" fill="currentColor" />
    </svg>
  ),
  groq: ({ size = 20 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 3.5a6.5 6.5 0 0 1 5.5 9.96V12a5.5 5.5 0 1 0-5.5 5.5h3v1.83A6.5 6.5 0 0 1 12 5.5z" />
    </svg>
  ),
  mistral: ({ size = 20 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <rect x="2" y="2" width="5" height="5" />
      <rect x="9" y="2" width="5" height="5" />
      <rect x="16" y="2" width="6" height="5" />
      <rect x="16" y="9" width="6" height="5" />
      <rect x="9" y="9" width="5" height="5" />
      <rect x="2" y="9" width="5" height="5" />
      <rect x="2" y="16" width="5" height="6" />
      <rect x="16" y="16" width="6" height="6" />
    </svg>
  ),
  ollama: ({ size = 20 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <circle cx="9" cy="7" r="2.5" />
      <circle cx="15" cy="7" r="2.5" />
      <path d="M5 13c0-3.87 3.13-7 7-7s7 3.13 7 7v5a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-5z" />
      <circle cx="9.5" cy="14" r="1" fill="white" />
      <circle cx="14.5" cy="14" r="1" fill="white" />
    </svg>
  ),
  custom: ({ size = 20 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14" />
      <path d="M12 2v2m0 16v2M2 12h2m16 0h2" />
    </svg>
  ),
}

// ── Provider catalogue ────────────────────────────────────────────────────────
const PROVIDERS: Record<string, {
  name: string; company: string; color: string; needsKey: boolean
  needsBaseUrl: boolean; keyPrefixes?: string[]
}> = {
  anthropic: {
    name: "Claude", company: "Anthropic", color: "#D97706",
    needsKey: true, needsBaseUrl: false,
    keyPrefixes: ["sk-ant-"],
  },
  openai: {
    name: "ChatGPT", company: "OpenAI", color: "#059669",
    needsKey: true, needsBaseUrl: false,
    keyPrefixes: ["sk-"],
  },
  gemini: {
    name: "Gemini", company: "Google", color: "#2563EB",
    needsKey: true, needsBaseUrl: false,
    keyPrefixes: ["AIza"],
  },
  groq: {
    name: "Groq", company: "Groq", color: "#DC2626",
    needsKey: true, needsBaseUrl: false,
    keyPrefixes: ["gsk_"],
  },
  mistral: {
    name: "Mistral", company: "Mistral AI", color: "#7C3AED",
    needsKey: true, needsBaseUrl: false,
    keyPrefixes: [],
  },
  ollama: {
    name: "Ollama", company: "Local", color: "#4B5563",
    needsKey: false, needsBaseUrl: true,
  },
  custom: {
    name: "Custom API", company: "OpenAI-compatible", color: "#0891B2",
    needsKey: true, needsBaseUrl: true,
  },
}

function detectProviderFromKey(key: string): string | null {
  if (key.startsWith("sk-ant-")) return "anthropic"
  if (key.startsWith("AIza")) return "gemini"
  if (key.startsWith("gsk_")) return "groq"
  // openai last since "sk-" is a subset of "sk-ant-"
  if (key.startsWith("sk-")) return "openai"
  return null
}

// ── Provider badge ────────────────────────────────────────────────────────────
function ProviderBadge({ provider, size = "md" }: { provider: string; size?: "sm" | "md" }) {
  const p = PROVIDERS[provider]
  const color = p?.color ?? "#6B7280"
  const Icon = ProviderIcons[provider]
  const sz = size === "sm" ? "w-7 h-7" : "w-10 h-10"
  const iconSz = size === "sm" ? 14 : 18
  return (
    <div
      className={`${sz} rounded-lg flex items-center justify-center shrink-0`}
      style={{ background: color + "22", color, border: `1px solid ${color}44` }}
    >
      {Icon ? <Icon size={iconSz} /> : <span className="font-bold text-xs">{provider.slice(0, 2).toUpperCase()}</span>}
    </div>
  )
}

// ── Credential card ───────────────────────────────────────────────────────────
function CredentialCard({ cred, onActivate, onDeactivate, onEdit, onDelete }: {
  cred: Credential
  onActivate: () => void; onDeactivate: () => void; onEdit: () => void; onDelete: () => void
}) {
  const p = PROVIDERS[cred.provider]
  return (
    <div className={`bg-card border rounded-xl p-4 flex items-center gap-4 transition-colors ${cred.is_active ? "border-archon-500/50 shadow-[0_0_0_1px_rgba(var(--archon-500),0.2)]" : "bd1"
      }`}>
      <ProviderBadge provider={cred.provider} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="t1 font-medium text-sm">{cred.label || (p?.name ?? cred.provider)}</span>
          {cred.is_active && (
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-archon-500/20 text-archon-400 border border-archon-500/30">
              ACTIVE
            </span>
          )}
        </div>
        <p className="t3 text-xs mt-0.5">{p?.company ?? cred.provider} · {cred.model}</p>
        {cred.api_key_masked && <p className="t4 text-xs font-mono mt-0.5">{cred.api_key_masked}</p>}
        {cred.base_url && <p className="t4 text-xs mt-0.5 truncate">{cred.base_url}</p>}
      </div>
      <div className="flex items-center gap-1 shrink-0">
        {!cred.is_active && (
          <div className="group relative">
            <button onClick={onActivate}
              className="p-1.5 rounded-lg t3 hover:text-archon-400 hover-muted transition-colors">
              <Circle className="w-4 h-4" />
            </button>
            <div className="absolute bottom-full right-0 mb-1.5 hidden group-hover:block z-10">
              <div className="bg-surface border bd1 rounded-lg px-2.5 py-1.5 text-xs t1 whitespace-nowrap shadow-lg">
                Use this model for audits and AI Chat
              </div>
            </div>
          </div>
        )}
        {cred.is_active && (
          <div className="group relative">
            <button onClick={onDeactivate}
              className="p-1.5 rounded-lg text-archon-400 hover:text-red-400 hover-muted transition-colors">
              <CircleOff className="w-4 h-4" />
            </button>
            <div className="absolute bottom-full right-0 mb-1.5 hidden group-hover:block z-10">
              <div className="bg-surface border bd1 rounded-lg px-2.5 py-1.5 text-xs t1 whitespace-nowrap shadow-lg">
                Stop using this model (falls back to Ollama)
              </div>
            </div>
          </div>
        )}
        <button onClick={onEdit} className="p-1.5 rounded-lg t3 hover-t1 hover-muted transition-colors">
          <Pencil className="w-3.5 h-3.5" />
        </button>
        <button onClick={onDelete} className="p-1.5 rounded-lg t3 hover:text-red-500 hover-muted transition-colors">
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}

// ── Form modal ────────────────────────────────────────────────────────────────
function CredentialForm({ initial, onSave, onClose }: {
  initial?: Credential | null
  onSave: (data: { provider: string; label: string; api_key: string; model: string; base_url: string }) => Promise<void>
  onClose: () => void
}) {
  const [provider, setProvider] = useState(initial?.provider ?? "anthropic")
  const [label, setLabel] = useState(initial?.label ?? "")
  const [apiKey, setApiKey] = useState("")
  const [model, setModel] = useState(initial?.model ?? "")
  const [baseUrl, setBaseUrl] = useState(initial?.base_url ?? "")
  const [showKey, setShowKey] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [detectedFrom, setDetectedFrom] = useState<string | null>(null)
  const [models, setModels] = useState<string[]>([])
  const [modelsLoading, setModelsLoading] = useState(false)
  const [modelsError, setModelsError] = useState("")
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const p = PROVIDERS[provider]
  const isEdit = !!initial

  // Fetch models from the provider API (debounced)
  function scheduleFetchModels(prov: string, key: string, burl: string) {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    const canFetch = prov === "ollama" ? !!burl : key.length >= 8
    if (!canFetch) return
    debounceRef.current = setTimeout(async () => {
      setModelsLoading(true)
      setModelsError("")
      setModels([])
      setModel("")
      try {
        const res = await api.credentials.models(prov, key || undefined, burl || undefined)
        setModels(res.models)
        if (res.models.length > 0) setModel(res.models[0])
      } catch (e: unknown) {
        setModelsError(e instanceof Error ? e.message : "Could not load models")
      } finally {
        setModelsLoading(false)
      }
    }, 700)
  }

  function handleProviderChange(v: string) {
    setProvider(v)
    setModels([])
    setModel("")
    setDetectedFrom(null)
    setModelsError("")
  }

  function handleApiKeyChange(val: string) {
    setApiKey(val)
    setModelsError("")
    if (!isEdit && val.length >= 4) {
      const detected = detectProviderFromKey(val)
      if (detected && detected !== provider) {
        setProvider(detected)
        setDetectedFrom(detected)
      }
    }
    scheduleFetchModels(provider, val, baseUrl)
  }

  function handleBaseUrlChange(val: string) {
    setBaseUrl(val)
    if (provider === "ollama" || provider === "custom") {
      scheduleFetchModels(provider, apiKey, val)
    }
  }

  // On edit mode, load existing models immediately
  useEffect(() => {
    if (isEdit) scheduleFetchModels(initial!.provider, "", initial!.base_url ?? "")
  }, []) // eslint-disable-line

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!model) { setError("Please load and select a model first"); return }
    setError(""); setLoading(true)
    try {
      await onSave({ provider, label, api_key: apiKey, model, base_url: baseUrl })
      onClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to save")
    } finally { setLoading(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-surface border bd1 rounded-2xl w-full max-w-md shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b bd1 sticky top-0 bg-surface z-10">
          <h2 className="t1 font-semibold">{isEdit ? "Edit credential" : "Add AI credential"}</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg t3 hover-muted transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {/* Provider selector */}
          {!isEdit && (
            <div>
              <Label>Provider</Label>
              <div className="grid grid-cols-4 gap-2 mt-1.5">
                {Object.entries(PROVIDERS).map(([id, info]) => {
                  const Icon = ProviderIcons[id]
                  return (
                    <button
                      key={id}
                      type="button"
                      onClick={() => handleProviderChange(id)}
                      className={`flex flex-col items-center gap-1.5 p-2.5 rounded-xl border text-xs font-medium transition-all ${provider === id
                          ? "border-archon-500/60 bg-archon-500/10 text-archon-400"
                          : "bd1 t3 hover-muted hover-t1"
                        }`}
                    >
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{
                          background: info.color + "22",
                          color: info.color,
                          border: `1px solid ${info.color}44`,
                        }}
                      >
                        {Icon ? <Icon size={15} /> : <span className="font-bold">{info.name.slice(0, 2)}</span>}
                      </div>
                      <span className="truncate w-full text-center leading-tight">{info.name}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* API Key — shown first so auto-detect triggers before provider */}
          {p?.needsKey && (
            <div>
              <Label htmlFor="apikey">
                API Key {isEdit && <span className="t4">(leave empty to keep current)</span>}
              </Label>
              <div className="relative">
                <Input
                  id="apikey"
                  type={showKey ? "text" : "password"}
                  placeholder={isEdit ? "••••••••" : "Paste your API key…"}
                  value={apiKey}
                  onChange={e => handleApiKeyChange(e.target.value)}
                  required={!isEdit}
                  className="pr-10 font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(s => !s)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 t3 hover-t1"
                >
                  {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {detectedFrom && (
                <p className="text-xs mt-1.5 flex items-center gap-1.5" style={{ color: PROVIDERS[detectedFrom]?.color }}>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Provider auto-detected: <strong>{PROVIDERS[detectedFrom]?.name}</strong>
                </p>
              )}
            </div>
          )}

          {/* Base URL */}
          {p?.needsBaseUrl && (
            <div>
              <Label htmlFor="baseurl">Base URL</Label>
              <Input
                id="baseurl"
                placeholder={provider === "ollama" ? "http://localhost:11434" : "https://api.example.com/v1"}
                value={baseUrl}
                onChange={e => handleBaseUrlChange(e.target.value)}
                required={provider === "ollama"}
              />
            </div>
          )}

          {/* Model */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <Label htmlFor="model">Model</Label>
              {modelsLoading && (
                <span className="text-xs t3 flex items-center gap-1.5">
                  <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Loading models…
                </span>
              )}
            </div>

            {models.length > 0 ? (
              <select
                id="model"
                value={model}
                onChange={e => setModel(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bd1 bg-card t1 text-sm focus:outline-none focus:border-archon-500/60"
              >
                {models.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            ) : (
              <div className="w-full px-3 py-2 rounded-lg border bd1 bg-card text-sm t3 italic">
                {modelsLoading
                  ? "Fetching available models…"
                  : modelsError
                    ? <span className="text-red-400 not-italic">{modelsError}</span>
                    : p?.needsKey
                      ? "Enter your API key to load available models"
                      : provider === "ollama"
                        ? "Enter the base URL to load models"
                        : "No models available"}
              </div>
            )}
          </div>

          {/* Label */}
          <div>
            <Label htmlFor="label">Label <span className="t4">(optional)</span></Label>
            <Input
              id="label"
              placeholder={`My ${p?.name ?? provider} key`}
              value={label}
              onChange={e => setLabel(e.target.value)}
            />
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-500 text-sm">{error}</div>
          )}

          <div className="flex gap-2 pt-1">
            <Button type="button" variant="ghost" className="flex-1" onClick={onClose}>Cancel</Button>
            <Button type="submit" className="flex-1" loading={loading}>
              {isEdit ? "Save changes" : "Add credential"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function CredentialsPage() {
  const [creds, setCreds] = useState<Credential[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Credential | null>(null)

  async function load() {
    try { setCreds(await api.credentials.list()) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  async function handleSave(data: { provider: string; label: string; api_key: string; model: string; base_url: string }) {
    if (editing) {
      await api.credentials.update(editing.id, {
        label: data.label || undefined,
        api_key: data.api_key || undefined,
        model: data.model,
        base_url: data.base_url || undefined,
      })
    } else {
      await api.credentials.create({
        provider: data.provider,
        label: data.label || undefined,
        api_key: data.api_key || undefined,
        model: data.model,
        base_url: data.base_url || undefined,
      })
    }
    await load()
  }

  const active = creds.find(c => c.is_active)

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold t1">AI Credentials</h1>
          <p className="t3 text-sm mt-1">Configure which AI model to use for auditing your systems</p>
        </div>
        <Button onClick={() => { setEditing(null); setShowForm(true) }}>
          <Plus className="w-4 h-4 mr-1.5" />
          Add credential
        </Button>
      </div>

      {/* Active model highlight */}
      {active && (
        <div className="mb-6 p-4 rounded-xl border border-archon-500/30 bg-archon-500/5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-semibold text-archon-400">ACTIVE MODEL</p>
            <button
              onClick={() => api.credentials.deactivate(active.id).then(load)}
              title="Deactivate"
              className="flex items-center gap-1 text-xs t3 hover:text-red-400 transition-colors"
            >
              <CircleOff className="w-3.5 h-3.5" />
              Deactivate
            </button>
          </div>
          <div className="flex items-center gap-3">
            <ProviderBadge provider={active.provider} />
            <div>
              <p className="t1 font-semibold">{active.label || PROVIDERS[active.provider]?.name || active.provider}</p>
              <p className="t3 text-xs">{PROVIDERS[active.provider]?.company} · {active.model}</p>
            </div>
          </div>
        </div>
      )}

      {/* List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2].map(i => <div key={i} className="h-20 bg-card border bd1 rounded-xl animate-pulse" />)}
        </div>
      ) : creds.length === 0 ? (
        <div className="text-center py-16 border bd1 rounded-xl bg-card">
          <div className="w-12 h-12 rounded-xl bg-archon-500/10 border border-archon-500/20 flex items-center justify-center mx-auto mb-3">
            <span className="text-archon-400 text-xl">🔑</span>
          </div>
          <p className="t1 font-medium">No credentials yet</p>
          <p className="t3 text-sm mt-1 mb-4">Add your first AI provider to start auditing</p>
          <Button onClick={() => { setEditing(null); setShowForm(true) }}>
            <Plus className="w-4 h-4 mr-1.5" />
            Add credential
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {creds.map(c => (
            <CredentialCard
              key={c.id}
              cred={c}
              onActivate={() => api.credentials.activate(c.id).then(load)}
              onDeactivate={() => api.credentials.deactivate(c.id).then(load)}
              onEdit={() => { setEditing(c); setShowForm(true) }}
              onDelete={() => api.credentials.delete(c.id).then(load)}
            />
          ))}
        </div>
      )}

      {showForm && (
        <CredentialForm
          initial={editing}
          onSave={handleSave}
          onClose={() => { setShowForm(false); setEditing(null) }}
        />
      )}
    </div>
  )
}
