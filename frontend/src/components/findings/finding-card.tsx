import { Badge } from "@/components/ui/badge"
import { Finding } from "@/types"
import { AlertTriangle, Database, Shield, Zap, Globe, Sparkles } from "lucide-react"

const categoryIcons = {
  api: Globe,
  database: Database,
  security: Shield,
  performance: Zap,
}

export function FindingCard({ finding }: { finding: Finding }) {
  const Icon = categoryIcons[finding.category] || AlertTriangle

  return (
    <div className="bg-card border bd1 rounded-xl p-5 hover-bd2 transition-colors">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center shrink-0 mt-0.5">
          <Icon className="w-5 h-5 t3" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <Badge variant={finding.severity}>{finding.severity}</Badge>
            <Badge variant={finding.category}>{finding.category}</Badge>
            {finding.source === "ai" && (
              <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-purple-500/15 text-purple-400 border border-purple-500/30">
                <Sparkles className="w-2.5 h-2.5" />
                AI detected
              </span>
            )}
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
