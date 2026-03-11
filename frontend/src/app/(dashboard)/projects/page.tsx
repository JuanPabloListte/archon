"use client"

import { useEffect, useState } from "react"
import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"
import { Project } from "@/types"
import { Plus, FolderOpen, Trash2, ArrowRight } from "lucide-react"
import Link from "next/link"
import { Spinner } from "@/components/ui/spinner"

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [error, setError] = useState("")

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try { setProjects(await api.projects.list()) }
    finally { setLoading(false) }
  }

  async function createProject(e: React.FormEvent) {
    e.preventDefault(); setCreating(true); setError("")
    try {
      const project = await api.projects.create(name, description || undefined)
      setProjects(prev => [project, ...prev])
      setShowForm(false); setName(""); setDescription("")
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create project")
    } finally { setCreating(false) }
  }

  async function deleteProject(id: string) {
    if (!confirm("Delete this project? This cannot be undone.")) return
    await api.projects.delete(id)
    setProjects(prev => prev.filter(p => p.id !== id))
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <Header title="Projects" subtitle="Manage your audited systems" />
        <Button onClick={() => setShowForm(!showForm)} size="sm">
          <Plus className="w-4 h-4 mr-1" /> New Project
        </Button>
      </div>

      {showForm && (
        <div className="bg-card border bd1 rounded-xl p-6 mb-6">
          <h3 className="t1 font-semibold mb-4">Create New Project</h3>
          <form onSubmit={createProject} className="space-y-4">
            <div><Label htmlFor="name">Project Name</Label>
              <Input id="name" value={name} onChange={e => setName(e.target.value)} placeholder="My API Service" required />
            </div>
            <div><Label htmlFor="desc">Description (optional)</Label>
              <Input id="desc" value={description} onChange={e => setDescription(e.target.value)} placeholder="Describe the system..." />
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <div className="flex gap-2">
              <Button type="submit" loading={creating}>Create</Button>
              <Button type="button" variant="secondary" onClick={() => setShowForm(false)}>Cancel</Button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-20"><Spinner /></div>
      ) : projects.length === 0 ? (
        <div className="bg-card border bd1 rounded-xl p-12 text-center">
          <FolderOpen className="w-12 h-12 t4 mx-auto mb-3" />
          <p className="t3 mb-2">No projects yet.</p>
          <Button onClick={() => setShowForm(true)} size="sm"><Plus className="w-4 h-4 mr-1" />Create your first project</Button>
        </div>
      ) : (
        <div className="grid gap-3">
          {projects.map(p => (
            <div key={p.id} className="bg-card border bd1 hover-bd2 rounded-xl p-5 flex items-center justify-between transition-colors">
              <div>
                <p className="t1 font-medium">{p.name}</p>
                {p.description && <p className="t3 text-sm mt-0.5">{p.description}</p>}
                <p className="t4 text-xs mt-1">{new Date(p.created_at).toLocaleDateString()}</p>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => deleteProject(p.id)}>
                  <Trash2 className="w-4 h-4 text-red-400" />
                </Button>
                <Link href={`/projects/${p.id}`}>
                  <Button variant="secondary" size="sm">Open <ArrowRight className="w-4 h-4 ml-1" /></Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
