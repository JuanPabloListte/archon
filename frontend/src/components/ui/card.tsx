import { clsx } from "clsx"

export function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={clsx("bg-card border bd1 rounded-xl p-6", className)}>
      {children}
    </div>
  )
}

export function CardHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={clsx("mb-4", className)}>{children}</div>
}

export function CardTitle({ className, children }: { className?: string; children: React.ReactNode }) {
  return <h2 className={clsx("text-lg font-semibold t1", className)}>{children}</h2>
}

export function CardContent({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={clsx(className)}>{children}</div>
}
