"use client"

import { useEffect, useState } from "react"
import { Header } from "@/components/layout/header"
import { StatsCard } from "@/components/dashboard/stats-card"
import { api } from "@/lib/api"
import { Project } from "@/types"
import { FolderOpen, AlertTriangle, CheckCircle, Activity } from "lucide-react"
import Link from "next/link"
import { Spinner } from "@/components/ui/spinner"

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.projects.list().then(setProjects).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <Header title="Dashboard" subtitle="Overview of your audited systems" />

      {loading ? (
        <div className="flex justify-center py-20"><Spinner /></div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatsCard title="Total Projects" value={projects.length} icon={FolderOpen} />
            <StatsCard title="Systems Monitored" value={projects.length} icon={Activity} />
            <StatsCard title="Active Audits" value={0} icon={AlertTriangle} />
            <StatsCard title="Health Avg" value="—" icon={CheckCircle} />
          </div>

          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Recent Projects</h2>
            {projects.length === 0 ? (
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-12 text-center">
                <FolderOpen className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                <p className="text-gray-400">No projects yet.</p>
                <Link href="/projects" className="text-archon-400 text-sm hover:text-archon-300 mt-2 inline-block">
                  Create your first project →
                </Link>
              </div>
            ) : (
              <div className="grid gap-3">
                {projects.slice(0, 5).map(p => (
                  <Link key={p.id} href={`/projects/${p.id}`}>
                    <div className="bg-gray-800 border border-gray-700 hover:border-gray-600 rounded-xl p-4 flex items-center justify-between transition-colors">
                      <div>
                        <p className="text-white font-medium">{p.name}</p>
                        {p.description && <p className="text-gray-400 text-sm">{p.description}</p>}
                      </div>
                      <span className="text-gray-500 text-sm">{new Date(p.created_at).toLocaleDateString()}</span>
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
