import { Badge } from "@/components/ui/badge"
import { Finding } from "@/types"
import { AlertTriangle, Database, Shield, Zap, Globe } from "lucide-react"

const categoryIcons = {
  api: Globe,
  database: Database,
  security: Shield,
  performance: Zap,
}

export function FindingCard({ finding }: { finding: Finding }) {
  const Icon = categoryIcons[finding.category] || AlertTriangle

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 hover:border-gray-600 transition-colors">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 bg-gray-700 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
          <Icon className="w-5 h-5 text-gray-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <Badge variant={finding.severity}>{finding.severity}</Badge>
            <Badge variant={finding.category}>{finding.category}</Badge>
          </div>
          <h3 className="text-white font-medium mb-1">{finding.title}</h3>
          <p className="text-gray-400 text-sm">{finding.description}</p>
          <div className="mt-3 bg-gray-700/50 rounded-lg p-3">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Recommendation</p>
            <p className="text-sm text-gray-300">{finding.recommendation}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
