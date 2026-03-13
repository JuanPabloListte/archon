"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { FindingCard } from "@/components/findings/finding-card"
import { api } from "@/lib/api"
import { Finding } from "@/types"
import { Spinner } from "@/components/ui/spinner"
import { ArrowLeft } from "lucide-react"

const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]

export default function FindingsPage() {
  const { id } = useParams<{ id: string }>()
  const [findings, setFindings] = useState<Finding[]>([])
  const [loading, setLoading] = useState(true)
  const [severityFilter, setSeverityFilter] = useState<string>("all")
  const [statusFilter, setStatusFilter] = useState<string>("open")

  useEffect(() => {
    api.audits.findings(id).then(setFindings).finally(() => setLoading(false))
  }, [id])

  function handleStatusChange(fid: string, status: Finding["status"]) {
    setFindings(prev => prev.map(f => f.id === fid ? { ...f, status } : f))
  }

  const sorted = [...findings].sort((a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity))
  const bySeverity = severityFilter === "all" ? sorted : sorted.filter(f => f.severity === severityFilter || f.category === severityFilter)
  const filtered = statusFilter === "all" ? bySeverity : bySeverity.filter(f => (f.status ?? "open") === statusFilter)

  const severityCounts = findings.reduce((acc, f) => ({ ...acc, [f.severity]: (acc[f.severity] || 0) + 1 }), {} as Record<string, number>)
  const statusCounts = findings.reduce((acc, f) => {
    const s = f.status ?? "open"
    return { ...acc, [s]: (acc[s] || 0) + 1 }
  }, {} as Record<string, number>)

  return (
    <div>
      <div className="mb-6">
        <Link href={`/projects/${id}`} className="t3 hover-t1 text-sm flex items-center gap-1 mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to project
        </Link>
        <Header title="Audit Findings" subtitle={`${findings.length} issues detected`} />
      </div>

      {/* Severity filters */}
      <div className="flex gap-2 mb-3 flex-wrap">
        {["all", "critical", "high", "medium", "low", "info"].map(s => (
          <button
            key={s}
            onClick={() => setSeverityFilter(s)}
            className={`px-3 py-1 rounded-full text-sm font-medium capitalize transition-colors ${
              severityFilter === s ? "bg-archon-500 text-white" : "bg-muted t3 hover-t1 border bd1"
            }`}
          >
            {s} {s !== "all" && severityCounts[s] ? `(${severityCounts[s]})` : ""}
          </button>
        ))}
      </div>

      {/* Status filters */}
      <div className="flex gap-2 mb-6">
        {[
          { key: "all",     label: "All statuses" },
          { key: "open",    label: `Open (${statusCounts.open ?? 0})` },
          { key: "fixed",   label: `Fixed (${statusCounts.fixed ?? 0})` },
          { key: "ignored", label: `Ignored (${statusCounts.ignored ?? 0})` },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setStatusFilter(key)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              statusFilter === key ? "bg-surface border bd1 t1" : "t4 hover-t2"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner /></div>
      ) : filtered.length === 0 ? (
        <div className="bg-card border bd1 rounded-xl p-12 text-center">
          <p className="t3">{findings.length === 0 ? "No findings yet. Run an audit first." : "No findings match the filter."}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(f => (
            <FindingCard key={f.id} finding={f} onStatusChange={handleStatusChange} />
          ))}
        </div>
      )}
    </div>
  )
}
