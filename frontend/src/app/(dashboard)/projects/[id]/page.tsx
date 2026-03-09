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
import { Project, Connection, Report } from "@/types"
import { Spinner } from "@/components/ui/spinner"
import { Play, Plus, Link as LinkIcon, Database, MessageSquare, FileText, AlertTriangle } from "lucide-react"

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [project, setProject] = useState<Project | null>(null)
  const [connections, setConnections] = useState<Connection[]>([])
  const [latestReport, setLatestReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)
  const [auditing, setAuditing] = useState(false)
  const [auditMsg, setAuditMsg] = useState("")
  const [showConnForm, setShowConnForm] = useState(false)
  const [connType, setConnType] = useState<"openapi" | "database">("openapi")
  const [connUrl, setConnUrl] = useState("")
  const [connDbStr, setConnDbStr] = useState("")
  const [addingConn, setAddingConn] = useState(false)

  useEffect(() => {
    Promise.all([
      api.projects.get(id),
      api.connections.list(id),
      api.reports.latest(id).catch(() => null),
    ]).then(([proj, conns, report]) => {
      setProject(proj)
      setConnections(conns)
      setLatestReport(report)
    }).finally(() => setLoading(false))
  }, [id])

  async function runAudit() {
    setAuditing(true)
    setAuditMsg("")
    try {
      const res = await api.audits.run(id)
      setAuditMsg(res.message + " — results will appear shortly.")
    } catch (e: unknown) {
      setAuditMsg(e instanceof Error ? e.message : "Audit failed")
    } finally {
      setAuditing(false)
    }
  }

  async function addConnection(e: React.FormEvent) {
    e.preventDefault()
    setAddingConn(true)
    try {
      const config = connType === "openapi"
        ? { url: connUrl }
        : { connection_string: connDbStr }
      const conn = await api.connections.create(id, connType, config)
      setConnections(prev => [...prev, conn])
      setShowConnForm(false)
      setConnUrl("")
      setConnDbStr("")
    } finally {
      setAddingConn(false)
    }
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>
  if (!project) return <p className="text-gray-400">Project not found.</p>

  const score = latestReport?.health_score
  const scoreColor = score === undefined ? "text-gray-400" : score >= 80 ? "text-green-400" : score >= 60 ? "text-yellow-400" : "text-red-400"

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <Header title={project.name} subtitle={project.description || undefined} />
        <Button onClick={runAudit} loading={auditing}>
          <Play className="w-4 h-4 mr-1" />
          Run Audit
        </Button>
      </div>

      {auditMsg && (
        <div className="mb-6 bg-archon-500/10 border border-archon-500/30 rounded-lg p-3 text-archon-400 text-sm">
          {auditMsg}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card>
          <p className="text-gray-400 text-sm">Health Score</p>
          <p className={`text-4xl font-bold mt-1 ${scoreColor}`}>
            {score !== undefined ? `${score}/100` : "—"}
          </p>
        </Card>
        <Card>
          <p className="text-gray-400 text-sm">Connections</p>
          <p className="text-4xl font-bold text-white mt-1">{connections.length}</p>
        </Card>
        <Card>
          <p className="text-gray-400 text-sm">Total Findings</p>
          <p className="text-4xl font-bold text-white mt-1">
            {latestReport?.report_json?.overview.total_findings ?? "—"}
          </p>
        </Card>
      </div>

      {latestReport?.summary && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 mb-6">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">AI Summary</p>
          <p className="text-gray-300 text-sm">{latestReport.summary}</p>
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
              <form onSubmit={addConnection} className="mb-4 p-3 bg-gray-700/50 rounded-lg space-y-3">
                <div className="flex gap-2">
                  <button type="button" onClick={() => setConnType("openapi")}
                    className={`flex-1 py-1.5 rounded text-sm font-medium transition-colors ${connType === "openapi" ? "bg-archon-500 text-white" : "bg-gray-700 text-gray-400"}`}>
                    OpenAPI
                  </button>
                  <button type="button" onClick={() => setConnType("database")}
                    className={`flex-1 py-1.5 rounded text-sm font-medium transition-colors ${connType === "database" ? "bg-archon-500 text-white" : "bg-gray-700 text-gray-400"}`}>
                    Database
                  </button>
                </div>
                {connType === "openapi" ? (
                  <div>
                    <Label>OpenAPI URL</Label>
                    <Input value={connUrl} onChange={e => setConnUrl(e.target.value)} placeholder="https://api.example.com/openapi.json" required />
                  </div>
                ) : (
                  <div>
                    <Label>Connection String</Label>
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
              <p className="text-gray-500 text-sm">No connections. Add an OpenAPI spec or database.</p>
            ) : (
              <div className="space-y-2">
                {connections.map(c => (
                  <div key={c.id} className="flex items-center gap-2 text-sm text-gray-300 bg-gray-700/50 rounded-lg px-3 py-2">
                    {c.type === "openapi" ? <LinkIcon className="w-4 h-4 text-purple-400" /> : <Database className="w-4 h-4 text-cyan-400" />}
                    <span className="capitalize">{c.type}</span>
                    <span className="text-gray-500 text-xs ml-auto">{new Date(c.created_at).toLocaleDateString()}</span>
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
              <Link href={`/projects/${id}/findings`} className="flex items-center gap-3 px-4 py-3 bg-gray-700/50 hover:bg-gray-700 rounded-lg transition-colors">
                <AlertTriangle className="w-5 h-5 text-orange-400" />
                <div>
                  <p className="text-white text-sm font-medium">View Findings</p>
                  <p className="text-gray-400 text-xs">All detected issues</p>
                </div>
              </Link>
              <Link href={`/projects/${id}/report`} className="flex items-center gap-3 px-4 py-3 bg-gray-700/50 hover:bg-gray-700 rounded-lg transition-colors">
                <FileText className="w-5 h-5 text-blue-400" />
                <div>
                  <p className="text-white text-sm font-medium">Technical Report</p>
                  <p className="text-gray-400 text-xs">Full audit report</p>
                </div>
              </Link>
              <Link href={`/projects/${id}/chat`} className="flex items-center gap-3 px-4 py-3 bg-gray-700/50 hover:bg-gray-700 rounded-lg transition-colors">
                <MessageSquare className="w-5 h-5 text-green-400" />
                <div>
                  <p className="text-white text-sm font-medium">AI Chat</p>
                  <p className="text-gray-400 text-xs">Query the analyzed system</p>
                </div>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
