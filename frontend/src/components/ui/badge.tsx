import { clsx } from "clsx"

const severityColors = {
  critical:    "bg-red-500/10 text-red-500 border-red-500/30",
  high:        "bg-orange-500/10 text-orange-500 border-orange-500/30",
  medium:      "bg-yellow-500/10 text-yellow-600 border-yellow-500/30",
  low:         "bg-blue-500/10 text-blue-500 border-blue-500/30",
  info:        "bg-muted t3 bd1",
  api:         "bg-purple-500/10 text-purple-500 border-purple-500/30",
  database:    "bg-cyan-500/10 text-cyan-500 border-cyan-500/30",
  security:    "bg-red-500/10 text-red-500 border-red-500/30",
  performance: "bg-orange-500/10 text-orange-500 border-orange-500/30",
}

type BadgeVariant = keyof typeof severityColors

export function Badge({ variant, children, className }: { variant?: BadgeVariant; children: React.ReactNode; className?: string }) {
  return (
    <span className={clsx(
      "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
      variant ? severityColors[variant] : "bg-muted t3 bd1",
      className
    )}>
      {children}
    </span>
  )
}
