"use client"

import { useEffect, useState } from "react"
import { Header } from "@/components/layout/header"
import { StatsCard } from "@/components/dashboard/stats-card"
import { api, DashboardStats } from "@/lib/api"
import { Project } from "@/types"
import { FolderOpen, AlertTriangle, CheckCircle, Activity } from "lucide-react"
import Link from "next/link"
import { Spinner } from "@/components/ui/spinner"

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.projects.list(), api.dashboard.stats()])
      .then(([p, s]) => { setProjects(p); setStats(s) })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <Header title="Dashboard" subtitle="Overview of your audited systems" />
      {loading ? (
        <div className="flex justify-center py-20"><Spinner /></div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatsCard title="Total Projects"    value={stats?.total_projects ?? 0}   icon={FolderOpen} />
            <StatsCard title="Projects Audited"  value={stats?.projects_audited ?? 0} icon={Activity} />
            <StatsCard title="Total Findings"    value={stats?.total_findings ?? 0}   icon={AlertTriangle} />
            <StatsCard title="Health Avg"        value={stats?.avg_health_score != null ? `${stats.avg_health_score}` : "—"} icon={CheckCircle} />
          </div>

          <div>
            <h2 className="text-lg font-semibold t1 mb-4">Recent Projects</h2>
            {projects.length === 0 ? (
              <div className="bg-card border bd1 rounded-xl p-12 text-center">
                <FolderOpen className="w-12 h-12 t4 mx-auto mb-3" />
                <p className="t3">No projects yet.</p>
                <Link href="/projects" className="text-archon-400 text-sm hover:text-archon-300 mt-2 inline-block">
                  Create your first project →
                </Link>
              </div>
            ) : (
              <div className="grid gap-3">
                {projects.slice(0, 5).map(p => (
                  <Link key={p.id} href={`/projects/${p.id}`}>
                    <div className="bg-card border bd1 hover-bd2 rounded-xl p-4 flex items-center justify-between transition-colors">
                      <div>
                        <p className="t1 font-medium">{p.name}</p>
                        {p.description && <p className="t3 text-sm">{p.description}</p>}
                      </div>
                      <span className="t4 text-sm">{new Date(p.created_at).toLocaleDateString()}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
