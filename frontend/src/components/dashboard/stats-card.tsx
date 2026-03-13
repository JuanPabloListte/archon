import { Card } from "@/components/ui/card"
import { LucideIcon } from "lucide-react"
import { Info } from "lucide-react"

export function StatsCard({
  title,
  value,
  icon: Icon,
  tooltip,
  color = "archon",
}: {
  title: string
  value: string | number
  icon: LucideIcon
  tooltip?: string
  color?: string
}) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-1.5">
            <p className="text-sm text-gray-400">{title}</p>
            {tooltip && (
              <div className="relative group">
                <Info className="w-3.5 h-3.5 text-gray-600 hover:text-gray-400 cursor-default transition-colors" />
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10 w-52 pointer-events-none">
                  <div className="bg-gray-900 border border-gray-700 text-gray-300 text-xs rounded-lg px-3 py-2 shadow-xl text-center leading-relaxed">
                    {tooltip}
                  </div>
                  <div className="w-2 h-2 bg-gray-900 border-r border-b border-gray-700 rotate-45 mx-auto -mt-1" />
                </div>
              </div>
            )}
          </div>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
        </div>
        <div className="w-12 h-12 bg-archon-500/20 rounded-xl flex items-center justify-center">
          <Icon className="w-6 h-6 text-archon-400" />
        </div>
      </div>
    </Card>
  )
}
