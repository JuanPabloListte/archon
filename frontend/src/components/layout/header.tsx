export function Header({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-8">
      <h1 className="text-2xl font-bold t1">{title}</h1>
      {subtitle && <p className="t3 mt-1">{subtitle}</p>}
    </div>
  )
}
