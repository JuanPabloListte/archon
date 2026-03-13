"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Finding } from "@/types"
import { api } from "@/lib/api"
import { AlertTriangle, Database, Shield, Zap, Globe, Sparkles, CheckCircle2, EyeOff, Circle } from "lucide-react"

const categoryIcons = {
  api: Globe,
  database: Database,
  security: Shield,
  performance: Zap,
}

const STATUS_CONFIG = {
  open:    { label: "Open",    icon: Circle,        className: "text-blue-400 bg-blue-500/10 border-blue-500/30" },
  fixed:   { label: "Fixed",   icon: CheckCircle2,  className: "text-green-400 bg-green-500/10 border-green-500/30" },
  ignored: { label: "Ignored", icon: EyeOff,        className: "text-gray-400 bg-gray-500/10 border-gray-500/30" },
}

export function FindingCard({
  finding: initial,
  onStatusChange,
}: {
  finding: Finding
  onStatusChange?: (id: string, status: Finding["status"]) => void
}) {
  const [finding, setFinding] = useState(initial)
  const [updating, setUpdating] = useState(false)
  const Icon = categoryIcons[finding.category as keyof typeof categoryIcons] || AlertTriangle
  const status = finding.status ?? "open"
  const statusCfg = STATUS_CONFIG[status]
  const StatusIcon = statusCfg.icon

  async function changeStatus(next: Finding["status"]) {
    if (next === status || updating) return
    setUpdating(true)
    try {
      const updated = await api.audits.updateFindingStatus(finding.id, next)
      setFinding(updated)
      onStatusChange?.(finding.id, next)
    } catch {
      // silently ignore
    } finally {
      setUpdating(false)
    }
  }

  return (
    <div className={`bg-card border rounded-xl p-5 transition-colors ${
      status === "fixed" ? "border-green-500/20 opacity-75" :
      status === "ignored" ? "bd1 opacity-50" : "bd1 hover-bd2"
    }`}>
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center shrink-0 mt-0.5">
          <Icon className="w-5 h-5 t3" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2 flex-wrap">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant={finding.severity}>{finding.severity}</Badge>
              <Badge variant={finding.category}>{finding.category}</Badge>
              {finding.source === "ai" && (
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-purple-500/15 text-purple-400 border border-purple-500/30">
                  <Sparkles className="w-2.5 h-2.5" />
                  AI detected
                </span>
              )}
            </div>

            {/* Status selector */}
            <div className="flex items-center gap-1">
              {(["open", "fixed", "ignored"] as const).map(s => {
                const cfg = STATUS_CONFIG[s]
                const Ic = cfg.icon
                const isActive = status === s
                return (
                  <button
                    key={s}
                    onClick={() => changeStatus(s)}
                    disabled={updating}
                    title={cfg.label}
                    className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border transition-all ${
                      isActive ? cfg.className : "bd1 t4 hover-t2"
                    } disabled:opacity-50`}
                  >
                    <Ic className="w-2.5 h-2.5" />
                    {isActive && cfg.label}
                  </button>
                )
              })}
            </div>
          </div>

          <h3 className="t1 font-medium mb-1">{finding.title}</h3>
          <p className="t3 text-sm">{finding.description}</p>
          <div className="mt-3 bg-muted rounded-lg p-3">
            <p className="text-xs t4 uppercase tracking-wider mb-1">Recommendation</p>
            <p className="text-sm t2">{finding.recommendation}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
