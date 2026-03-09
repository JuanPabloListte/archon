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
  const [filter, setFilter] = useState<string>("all")

  useEffect(() => {
    api.audits.findings(id).then(setFindings).finally(() => setLoading(false))
  }, [id])

  const sorted = [...findings].sort(
    (a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity)
  )
  const filtered = filter === "all" ? sorted : sorted.filter(f => f.severity === filter || f.category === filter)

  const counts = findings.reduce((acc, f) => ({ ...acc, [f.severity]: (acc[f.severity] || 0) + 1 }), {} as Record<string, number>)

  return (
    <div>
      <div className="mb-6">
        <Link href={`/projects/${id}`} className="text-gray-400 hover:text-white text-sm flex items-center gap-1 mb-4">
          <ArrowLeft className="w-4 h-4" /> Back to project
        </Link>
        <Header title="Audit Findings" subtitle={`${findings.length} issues detected`} />
      </div>

      <div className="flex gap-2 mb-6 flex-wrap">
        {["all", "critical", "high", "medium", "low", "info"].map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-1 rounded-full text-sm font-medium capitalize transition-colors ${
              filter === s
                ? "bg-archon-500 text-white"
                : "bg-gray-800 text-gray-400 hover:text-white border border-gray-700"
            }`}
          >
            {s} {s !== "all" && counts[s] ? `(${counts[s]})` : ""}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner /></div>
      ) : filtered.length === 0 ? (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-12 text-center">
          <p className="text-gray-400">
            {findings.length === 0 ? "No findings yet. Run an audit first." : "No findings match the filter."}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(f => <FindingCard key={f.id} finding={f} />)}
        </div>
      )}
    </div>
  )
}
