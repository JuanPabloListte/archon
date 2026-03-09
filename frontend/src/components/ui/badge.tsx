import { clsx } from "clsx"

const severityColors = {
  critical: "bg-red-900/40 text-red-400 border-red-800",
  high: "bg-orange-900/40 text-orange-400 border-orange-800",
  medium: "bg-yellow-900/40 text-yellow-400 border-yellow-800",
  low: "bg-blue-900/40 text-blue-400 border-blue-800",
  info: "bg-gray-700 text-gray-400 border-gray-600",
  api: "bg-purple-900/40 text-purple-400 border-purple-800",
  database: "bg-cyan-900/40 text-cyan-400 border-cyan-800",
  security: "bg-red-900/40 text-red-400 border-red-800",
  performance: "bg-orange-900/40 text-orange-400 border-orange-800",
}

type BadgeVariant = keyof typeof severityColors

export function Badge({ variant, children, className }: { variant?: BadgeVariant; children: React.ReactNode; className?: string }) {
  return (
    <span className={clsx(
      "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
      variant ? severityColors[variant] : "bg-gray-700 text-gray-300 border-gray-600",
      className
    )}>
      {children}
    </span>
  )
}
