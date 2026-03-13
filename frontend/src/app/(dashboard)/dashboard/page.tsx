"use client"

import { useEffect, useState } from "react"
import { Header } from "@/components/layout/header"
import { StatsCard } from "@/components/dashboard/stats-card"
import { api, DashboardStats } from "@/lib/api"
import { Project } from "@/types"
import { FolderOpen, AlertTriangle, CheckCircle, Activity, Brain, Download, Sparkles } from "lucide-react"
import Link from "next/link"
import { Spinner } from "@/components/ui/spinner"
import { getToken } from "@/lib/auth"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface DatasetStats {
  your_findings: number
  global_patterns: number
  confirmed_solutions: number
  total_examples: number
}

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [datasetStats, setDatasetStats] = useState<DatasetStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.projects.list(),
      api.dashboard.stats(),
      api.dataset.stats().catch(() => null),
    ]).then(([p, s, ds]) => {
      setProjects(p)
      setStats(s)
      setDatasetStats(ds)
    }).finally(() => setLoading(false))
  }, [])

  function downloadDataset(fmt: "jsonl" | "alpaca") {
    const token = getToken()
    const url = `${API_URL}/api/v1/dataset/export?fmt=${fmt}`
    // Fetch with auth header and trigger download
    fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(res => res.blob())
      .then(blob => {
        const a = document.createElement("a")
        a.href = URL.createObjectURL(blob)
        a.download = fmt === "jsonl" ? "archon_dataset.jsonl" : "archon_dataset.json"
        a.click()
        URL.revokeObjectURL(a.href)
      })
  }

  return (
    <div>
      <Header title="Dashboard" subtitle="Overview of your audited systems" />
      {loading ? (
        <div className="flex justify-center py-20"><Spinner /></div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatsCard
              title="Total Projects"
              value={stats?.total_projects ?? 0}
              icon={FolderOpen}
              tooltip="Number of projects you have created in Archon."
            />
            <StatsCard
              title="Projects Audited"
              value={stats?.projects_audited ?? 0}
              icon={Activity}
              tooltip="Projects that have been audited at least once. A project is audited when you run an audit and it generates findings or a report."
            />
            <StatsCard
              title="Total Findings"
              value={stats?.total_findings ?? 0}
              icon={AlertTriangle}
              tooltip="Total number of issues detected across all your projects — security vulnerabilities, missing indexes, bad API design, etc."
            />
            <StatsCard
              title="Health Avg"
              value={stats?.avg_health_score != null ? `${stats.avg_health_score}` : "—"}
              icon={CheckCircle}
              tooltip="Average health score across all audited projects. Score goes from 0 to 100 — the higher, the healthier. It drops based on the severity of open findings (critical = −25, high = −15, medium = −8, low = −3)."
            />
          </div>

          {/* Global Knowledge Base */}
          {datasetStats !== null && (
            <div className="bg-card border bd1 rounded-xl p-5 mb-8">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-archon-400" />
                  <h2 className="text-base font-semibold t1">Global Knowledge Base</h2>
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-archon-500/20 text-archon-400 border border-archon-500/30">
                    Cross-project learning
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => downloadDataset("jsonl")}
                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border bd1 t3 hover-t1 transition-colors"
                    title="OpenAI / Anthropic fine-tuning format"
                  >
                    <Download className="w-3.5 h-3.5" />
                    JSONL
                  </button>
                  <button
                    onClick={() => downloadDataset("alpaca")}
                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border bd1 t3 hover-t1 transition-colors"
                    title="Alpaca format for Llama / Ollama fine-tuning"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Alpaca
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-muted rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold t1">{datasetStats.global_patterns}</p>
                  <p className="text-xs t4 mt-0.5">Learned patterns</p>
                </div>
                <div className="bg-muted rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-green-500">{datasetStats.confirmed_solutions}</p>
                  <p className="text-xs t4 mt-0.5">Confirmed fixes</p>
                </div>
                <div className="bg-muted rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold t1">{datasetStats.your_findings}</p>
                  <p className="text-xs t4 mt-0.5">Your findings</p>
                </div>
                <div className="bg-muted rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-archon-400">{datasetStats.total_examples}</p>
                  <p className="text-xs t4 mt-0.5">Training examples</p>
                </div>
              </div>

              <p className="text-xs t4 mt-3">
                Every audit adds patterns to the global knowledge base. Mark findings as <span className="text-green-400 font-medium">Fixed</span> to confirm solutions and improve AI accuracy. Export to fine-tune your own model.
              </p>
            </div>
          )}

          <div>
            <h2 className="text-lg font-semibold t1 mb-4">Recent Projects</h2>
            {projects.length === 0 ? (
              <div className="bg-card border bd1 rounded-xl p-12 text-center">
                <FolderOpen className="w-12 h-12 t4 mx-auto mb-3" />
                <p className="t3">No projects yet.</p>
                <Link href="/projects" className="text-archon-400 text-sm hover:text-archon-300 mt-2 inline-block">
                  Create your first project →
                </Link>
              </div>
            ) : (
              <div className="grid gap-3">
                {projects.slice(0, 5).map(p => (
                  <Link key={p.id} href={`/projects/${p.id}`}>
                    <div className="bg-card border bd1 hover-bd2 rounded-xl p-4 flex items-center justify-between transition-colors">
                      <div>
                        <p className="t1 font-medium">{p.name}</p>
                        {p.description && <p className="t3 text-sm">{p.description}</p>}
                      </div>
                      <span className="t4 text-sm">{new Date(p.created_at).toLocaleDateString()}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
