import { Card } from "@/components/ui/card"
import { LucideIcon } from "lucide-react"

export function StatsCard({
  title,
  value,
  icon: Icon,
  color = "archon",
}: {
  title: string
  value: string | number
  icon: LucideIcon
  color?: string
}) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
        </div>
        <div className="w-12 h-12 bg-archon-500/20 rounded-xl flex items-center justify-center">
          <Icon className="w-6 h-6 text-archon-400" />
        </div>
      </div>
    </Card>
  )
}
