"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { api } from "@/lib/api"
import { getToken } from "@/lib/auth"
import { Project, Connection, Report, AuditRun } from "@/types"
import { Spinner } from "@/components/ui/spinner"
import { Play, Plus, Link as LinkIcon, Database, MessageSquare, FileText, AlertTriangle, CheckCircle, XCircle, ChevronDown, ChevronUp, RefreshCw, Trash2, Cpu, Bot, RotateCcw, Settings2, Clock, Zap } from "lucide-react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface AuditStep { text: string; group?: boolean }
interface AuditRule { rule: string; count: number }
type AuditEvent =
  | { type: "step"; text: string; group?: boolean }
  | { type: "rule"; rule: string; count: number }
  | { type: "done"; total_findings: number; health_score: number; summary: string }
  | { type: "error"; text: string }

interface AuditProgress {
  steps: AuditStep[]; rules: AuditRule[]; done: boolean
  error?: string; health_score?: number; total_findings?: number; summary?: string
}

function HealthTrend({ runs }: { runs: AuditRun[] }) {
  if (runs.length < 2) return null
  const W = 120, H = 40, pad = 4
  const scores = runs.map(r => r.health_score)
  const min = Math.min(...scores)
  const max = Math.max(...scores)
  const range = max - min || 1
  const pts = scores.map((s, i) => {
    const x = pad + (i / (scores.length - 1)) * (W - pad * 2)
    const y = H - pad - ((s - min) / range) * (H - pad * 2)
    return `${x},${y}`
  }).join(" ")
  const last = scores[scores.length - 1]
  const prev = scores[scores.length - 2]
  const trend = last > prev ? "↑" : last < prev ? "↓" : "→"
  const trendColor = last > prev ? "text-green-500" : last < prev ? "text-red-500" : "t3"
  return (
    <div className="flex items-center gap-3">
      <svg width={W} height={H} className="opacity-70">
        <polyline points={pts} fill="none" stroke="currentColor" strokeWidth="1.5" className="text-archon-400" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
      <span className={`text-sm font-semibold ${trendColor}`}>{trend} {Math.abs(last - prev).toFixed(0)} pts</span>
    </div>
  )
}

function AuditProgressPanel({ progress, onClose }: { progress: AuditProgress; onClose: () => void }) {
  const [open, setOpen] = useState(true)

  return (
    <div className="mb-6 border bd1 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-subtle hover:bg-[var(--bg-subtle)] transition-colors border-b bd1"
      >
        <div className="flex items-center gap-2">
          {progress.done && !progress.error
            ? <CheckCircle className="w-4 h-4 text-green-500" />
            : progress.error ? <XCircle className="w-4 h-4 text-red-500" /> : <Spinner className="w-4 h-4" />}
          <span className="t1 text-sm font-medium">
            {progress.done && !progress.error
              ? `Audit complete — ${progress.total_findings} findings, health score ${progress.health_score}/100`
              : progress.error ? "Audit failed" : "Running audit..."}
          </span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 t3" /> : <ChevronDown className="w-4 h-4 t3" />}
      </button>

      {open && (
        <div className="bg-subtle px-4 py-3 space-y-1 text-sm">
          {progress.steps.map((s, i) => (
            <div key={i} className={`flex items-center gap-2 ${s.group ? "mt-2 t2 font-medium" : "t3 ml-2"}`}>
              <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${s.group ? "bg-archon-400" : "bg-subtle"}`} />
              {s.text}
            </div>
          ))}
          {progress.rules.map((r, i) => (
            <div key={i} className="flex items-center gap-2 t3 ml-6">
              <span className="text-archon-500">→</span>
              <span className="font-mono">{r.rule}</span>
              <span className={`ml-auto font-medium ${r.count > 0 ? "text-orange-500" : "text-green-500"}`}>
                {r.count} finding{r.count !== 1 ? "s" : ""}
              </span>
            </div>
          ))}
          {!progress.done && !progress.error && (
            <div className="flex items-center gap-2 t4 mt-1"><Spinner className="w-3 h-3" /><span>Processing...</span></div>
          )}
          {progress.error && <p className="text-red-500 mt-1">{progress.error}</p>}
          {progress.done && progress.summary && (
            <div className="mt-3 pt-3 border-t bd1">
              <p className="t4 text-xs uppercase tracking-wider mb-1">Summary</p>
              <p className="t2">{progress.summary}</p>
            </div>
          )}
          {progress.done && (
            <div className="mt-2 flex justify-end">
              <button onClick={onClose} className="text-xs t4 hover-t1 transition-colors">Dismiss</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [project, setProject] = useState<Project | null>(null)
  const [connections, setConnections] = useState<Connection[]>([])
  const [latestReport, setLatestReport] = useState<Report | null>(null)
  const [auditRuns, setAuditRuns] = useState<AuditRun[]>([])
  const [activeCredential, setActiveCredential] = useState<import("@/types").Credential | null>(null)
  const [loading, setLoading] = useState(true)
  const [auditing, setAuditing] = useState(false)
  const [auditProgress, setAuditProgress] = useState<AuditProgress | null>(null)
  const [showConnForm, setShowConnForm] = useState(false)
  const [connType, setConnType] = useState<"openapi" | "database">("openapi")
  const [connUrl, setConnUrl] = useState("")
  const [connDbStr, setConnDbStr] = useState("")
  const [addingConn, setAddingConn] = useState(false)
  const [systemPrompt, setSystemPrompt] = useState<string>("")
  const [savingPrompt, setSavingPrompt] = useState(false)
  const [promptSaved, setPromptSaved] = useState(false)
  const [showPromptPanel, setShowPromptPanel] = useState(false)
  const [selectedConnIds, setSelectedConnIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    Promise.all([
      api.projects.get(id),
      api.connections.list(id),
      api.reports.latest(id).catch(() => null),
      api.credentials.list().catch(() => []),
      api.audits.runs(id).catch(() => []),
    ]).then(([proj, conns, report, creds, runs]) => {
      setProject(proj); setConnections(conns); setLatestReport(report)
      setAuditRuns(runs as AuditRun[])
      setActiveCredential((creds as import("@/types").Credential[]).find(c => c.is_active) ?? null)
      setSystemPrompt(proj.audit_system_prompt ?? "")
      const saved = localStorage.getItem(`audit-conns-${id}`)
      const allIds = new Set(conns.map(c => c.id))
      if (saved) {
        const parsed: string[] = JSON.parse(saved)
        setSelectedConnIds(new Set(parsed.filter(x => allIds.has(x))))
      } else {
        setSelectedConnIds(allIds)
      }
    }).finally(() => setLoading(false))
  }, [id])

  async function runAudit() {
    setAuditing(true)
    setAuditProgress({ steps: [], rules: [], done: false })
    try {
      const token = getToken()
      const connIds = [...selectedConnIds]
      const resp = await fetch(`${API_URL}/api/v1/audits/run/${id}/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ connection_ids: connIds.length < connections.length ? connIds : null }),
      })
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)

      const reader = resp.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n"); buffer = lines.pop() ?? ""
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          try {
            const event: AuditEvent = JSON.parse(line.slice(6))
            setAuditProgress(prev => {
              if (!prev) return prev
              if (event.type === "step") return { ...prev, steps: [...prev.steps, { text: event.text, group: event.group }] }
              if (event.type === "rule") return { ...prev, rules: [...prev.rules, { rule: event.rule, count: event.count }] }
              if (event.type === "done") {
                api.reports.latest(id).then(setLatestReport).catch(() => null)
                api.audits.runs(id).then(setAuditRuns).catch(() => null)
                return { ...prev, done: true, health_score: event.health_score, total_findings: event.total_findings, summary: event.summary }
              }
              if (event.type === "error") return { ...prev, done: true, error: event.text }
              return prev
            })
          } catch { }
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Audit failed"
      setAuditProgress(prev => prev ? { ...prev, done: true, error: msg } : null)
    } finally { setAuditing(false) }
  }

  async function saveSystemPrompt() {
    setSavingPrompt(true)
    try {
      const updated = await api.projects.updateSettings(id, {
        audit_system_prompt: systemPrompt.trim() || null,
      })
      setProject(updated)
      setPromptSaved(true)
      setTimeout(() => setPromptSaved(false), 2000)
    } finally {
      setSavingPrompt(false)
    }
  }

  async function addConnection(e: React.FormEvent) {
    e.preventDefault(); setAddingConn(true)
    try {
      const config = connType === "openapi" ? { url: connUrl } : { connection_string: connDbStr }
      const conn = await api.connections.create(id, connType, config)
      setConnections(prev => [...prev, conn])
      setSelectedConnIds(prev => new Set([...prev, conn.id]))
      setShowConnForm(false); setConnUrl(""); setConnDbStr("")
    } finally { setAddingConn(false) }
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>
  if (!project) return <p className="t3">Project not found.</p>

  const score = auditProgress?.done && auditProgress.health_score !== undefined
    ? auditProgress.health_score : latestReport?.health_score
  const scoreColor = score === undefined ? "t3" : score >= 80 ? "text-green-500" : score >= 60 ? "text-yellow-500" : "text-red-500"

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <Header title={project.name} subtitle={project.description || undefined} />
        <div className="flex items-center gap-2">
          {activeCredential ? (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border bd1 bg-card">
              <Cpu className="w-3.5 h-3.5 text-archon-400" />
              <span className="text-xs t2 font-medium">{activeCredential.model}</span>
            </div>
          ) : (
            <Link href="/credentials" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-yellow-500/30 bg-yellow-500/5 text-yellow-500 text-xs font-medium hover:bg-yellow-500/10 transition-colors">
              <Cpu className="w-3.5 h-3.5" />
              No AI model
            </Link>
          )}
          <button
            onClick={() => setShowPromptPanel(p => !p)}
            title="AI Reviewer settings"
            className={`relative p-2 rounded-lg border transition-colors ${showPromptPanel ? "border-archon-500 bg-archon-500/10 text-archon-400" : "bd1 bg-card t3 hover-t1"}`}
          >
            <Settings2 className="w-4 h-4" />
            {project.audit_system_prompt && (
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-archon-500" />
            )}
          </button>
          <Button onClick={runAudit} loading={auditing}><Play className="w-4 h-4 mr-1" />Run Audit</Button>
        </div>
      </div>

      {showPromptPanel && (
        <div className="mb-5 rounded-xl border bd1 bg-card overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b bd1 bg-subtle">
            <Bot className="w-4 h-4 text-archon-400" />
            <span className="text-sm font-medium t1">AI Reviewer — System Prompt</span>
            <span className="ml-2 text-xs t4">Customize how the AI interprets findings for this project</span>
          </div>
          <div className="p-4">
            <textarea
              value={systemPrompt}
              onChange={e => setSystemPrompt(e.target.value)}
              placeholder='Default: "You are an expert security and software auditor. Review the provided findings carefully and improve audit quality."'
              rows={3}
              className="w-full rounded-lg border bd1 bg-muted px-3 py-2 text-sm t1 placeholder:t4 resize-none focus:outline-none focus:ring-1 focus:ring-archon-500 font-mono"
            />
            <div className="flex items-center gap-2 mt-3">
              <Button size="sm" onClick={saveSystemPrompt} loading={savingPrompt}>
                {promptSaved ? <><CheckCircle className="w-3.5 h-3.5 mr-1" />Saved</> : "Save"}
              </Button>
              {systemPrompt && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => { setSystemPrompt(""); api.projects.updateSettings(id, { audit_system_prompt: null }).then(setProject) }}
                >
                  <RotateCcw className="w-3.5 h-3.5 mr-1" />Reset to default
                </Button>
              )}
              {project.audit_system_prompt && (
                <span className="ml-auto text-xs text-archon-400 flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" />Custom prompt active
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {auditProgress && <AuditProgressPanel progress={auditProgress} onClose={() => setAuditProgress(null)} />}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card>
          <p className="t3 text-sm">Health Score</p>
          <p className={`text-4xl font-bold mt-1 ${scoreColor}`}>{score !== undefined ? `${score}/100` : "—"}</p>
          <div className="mt-2"><HealthTrend runs={auditRuns} /></div>
        </Card>
        <Card>
          <p className="t3 text-sm">Connections</p>
          <p className="text-4xl font-bold t1 mt-1">{connections.length}</p>
        </Card>
        <Card>
          <p className="t3 text-sm">Total Findings</p>
          <p className="text-4xl font-bold t1 mt-1">
            {auditProgress?.done && auditProgress.total_findings !== undefined
              ? auditProgress.total_findings
              : latestReport?.report_json?.overview.total_findings ?? "—"}
          </p>
        </Card>
      </div>

      {(latestReport?.summary || (auditProgress?.done && auditProgress.summary)) && (
        <div className="bg-card border bd1 rounded-xl p-4 mb-6">
          <p className="text-xs t4 uppercase tracking-wider mb-1">AI Summary</p>
          <p className="t2 text-sm">{auditProgress?.done && auditProgress.summary ? auditProgress.summary : latestReport?.summary}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Connections</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowConnForm(!showConnForm)}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {showConnForm && (
              <form onSubmit={addConnection} className="mb-4 p-3 bg-muted rounded-lg space-y-3">
                <div className="flex gap-2">
                  <button type="button" onClick={() => setConnType("openapi")}
                    className={`flex-1 py-1.5 rounded text-sm font-medium transition-colors ${connType === "openapi" ? "bg-archon-500 text-white" : "bg-subtle t3"}`}>
                    OpenAPI
                  </button>
                  <button type="button" onClick={() => setConnType("database")}
                    className={`flex-1 py-1.5 rounded text-sm font-medium transition-colors ${connType === "database" ? "bg-archon-500 text-white" : "bg-subtle t3"}`}>
                    Database
                  </button>
                </div>
                {connType === "openapi" ? (
                  <div><Label>OpenAPI URL</Label>
                    <Input value={connUrl} onChange={e => setConnUrl(e.target.value)} placeholder="https://api.example.com/openapi.json" required />
                  </div>
                ) : (
                  <div><Label>Connection String</Label>
                    <Input value={connDbStr} onChange={e => setConnDbStr(e.target.value)} placeholder="postgresql://user:pass@host:5432/db" required />
                  </div>
                )}
                <div className="flex gap-2">
                  <Button type="submit" size="sm" loading={addingConn}>Add &amp; Ingest</Button>
                  <Button type="button" size="sm" variant="secondary" onClick={() => setShowConnForm(false)}>Cancel</Button>
                </div>
              </form>
            )}
            {connections.length === 0 ? (
              <p className="t4 text-sm">No connections. Add an OpenAPI spec or database.</p>
            ) : (
              <div className="space-y-2">
                {connections.map(c => (
                  <div key={c.id} className={`text-sm t2 bg-muted rounded-lg px-3 py-2 transition-opacity ${!selectedConnIds.has(c.id) ? "opacity-50" : ""}`}>
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedConnIds.has(c.id)}
                        onChange={() => setSelectedConnIds(prev => {
                          const next = new Set(prev)
                          next.has(c.id) ? next.delete(c.id) : next.add(c.id)
                          localStorage.setItem(`audit-conns-${id}`, JSON.stringify([...next]))
                          return next
                        })}
                        className="accent-archon-500 w-3.5 h-3.5 shrink-0 cursor-pointer"
                        title="Include in next audit"
                      />
                      {c.type === "openapi" ? <LinkIcon className="w-4 h-4 text-purple-500" /> : <Database className="w-4 h-4 text-cyan-500" />}
                      <span className="capitalize">{c.type}</span>
                      <span className="ml-auto flex items-center gap-2">
                        {c.status === "ingesting" && <><RefreshCw className="w-3 h-3 text-yellow-500 animate-spin" /><span className="text-yellow-500 text-xs">Ingesting...</span></>}
                        {c.status === "done" && <><CheckCircle className="w-3 h-3 text-green-500" /><span className="text-green-500 text-xs">{c.ingested_count ?? 0} items</span></>}
                        {c.status === "error" && <><XCircle className="w-3 h-3 text-red-500" /><span className="text-red-500 text-xs">Error</span></>}
                        {!c.status && <span className="t4 text-xs">{new Date(c.created_at).toLocaleDateString()}</span>}
                        <button
                          onClick={() => { if (confirm(`Delete this ${c.type} connection?`)) api.connections.delete(c.id).then(() => { setConnections(prev => prev.filter(x => x.id !== c.id)); setSelectedConnIds(prev => { const n = new Set(prev); n.delete(c.id); return n }) }) }}
                          className="ml-1 t4 hover:text-red-500 transition-colors" title="Delete connection"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </span>
                    </div>
                    {c.status === "error" && c.ingestion_error && (
                      <p className="text-red-500 text-xs mt-1.5 ml-6 font-mono break-all">{c.ingestion_error}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Quick Actions</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Link href={`/projects/${id}/findings`} className="flex items-center gap-3 px-4 py-3 bg-muted hover-subtle rounded-lg transition-colors">
                <AlertTriangle className="w-5 h-5 text-orange-500" />
                <div><p className="t1 text-sm font-medium">View Findings</p><p className="t3 text-xs">All detected issues</p></div>
              </Link>
              <Link href={`/projects/${id}/report`} className="flex items-center gap-3 px-4 py-3 bg-muted hover-subtle rounded-lg transition-colors">
                <FileText className="w-5 h-5 text-blue-500" />
                <div><p className="t1 text-sm font-medium">Technical Report</p><p className="t3 text-xs">Full audit report</p></div>
              </Link>
              <Link href={`/projects/${id}/chat`} className="flex items-center gap-3 px-4 py-3 bg-muted hover-subtle rounded-lg transition-colors">
                <MessageSquare className="w-5 h-5 text-green-500" />
                <div><p className="t1 text-sm font-medium">AI Chat</p><p className="t3 text-xs">Query the analyzed system</p></div>
              </Link>
              <Link href={`/projects/${id}/schedules`} className="flex items-center gap-3 px-4 py-3 bg-muted hover-subtle rounded-lg transition-colors">
                <Clock className="w-5 h-5 text-cyan-500" />
                <div><p className="t1 text-sm font-medium">Scheduled Audits</p><p className="t3 text-xs">Automate & get alerts</p></div>
              </Link>
              <Link href={`/projects/${id}/rules`} className="flex items-center gap-3 px-4 py-3 bg-muted hover-subtle rounded-lg transition-colors">
                <Zap className="w-5 h-5 text-yellow-500" />
                <div><p className="t1 text-sm font-medium">Custom Rules</p><p className="t3 text-xs">Define your own audit checks</p></div>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {auditRuns.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Audit History</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[...auditRuns].reverse().map((run, i) => {
                const color = run.health_score >= 80 ? "text-green-500" : run.health_score >= 60 ? "text-yellow-500" : "text-red-500"
                return (
                  <div key={run.id} className="flex items-center gap-3 text-sm px-3 py-2 bg-muted rounded-lg">
                    <span className="t4 text-xs w-5 text-center">#{auditRuns.length - i}</span>
                    <span className={`font-bold w-16 ${color}`}>{run.health_score}/100</span>
                    <span className="t3 flex-1">{run.total_findings} findings</span>
                    <span className="t4 text-xs">{new Date(run.created_at).toLocaleDateString()}</span>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
