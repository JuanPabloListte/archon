import { getToken } from "./auth"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, err.detail || "Request failed")
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export interface DashboardStats {
  total_projects: number
  total_findings: number
  avg_health_score: number | null
  projects_audited: number
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      request<{ access_token: string }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    register: (email: string, password: string) =>
      request<{ access_token: string }>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
  },
  dashboard: {
    stats: () => request<DashboardStats>("/api/v1/dashboard/stats"),
  },
  projects: {
    list: () => request<import("@/types").Project[]>("/api/v1/projects"),
    create: (name: string, description?: string) =>
      request<import("@/types").Project>("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify({ name, description }),
      }),
    get: (id: string) => request<import("@/types").Project>(`/api/v1/projects/${id}`),
    delete: (id: string) => request<void>(`/api/v1/projects/${id}`, { method: "DELETE" }),
  },
  connections: {
    create: (projectId: string, type: string, config: Record<string, unknown>) =>
      request<import("@/types").Connection>("/api/v1/connections", {
        method: "POST",
        body: JSON.stringify({ project_id: projectId, type, config }),
      }),
    list: (projectId: string) =>
      request<import("@/types").Connection[]>(`/api/v1/connections/project/${projectId}`),
  },
  audits: {
    run: (projectId: string) =>
      request<{ message: string; project_id: string }>(`/api/v1/audits/run/${projectId}`, { method: "POST" }),
    findings: (projectId: string) =>
      request<import("@/types").Finding[]>(`/api/v1/audits/findings/${projectId}`),
    insights: (projectId: string) =>
      request<{ prioritized: { id: string; severity: string; title: string }[]; summary: string }>(
        `/api/v1/audits/insights/${projectId}`
      ),
    findingAdvice: (findingId: string) =>
      request<{ finding_id: string; recommendations: string }>(
        `/api/v1/audits/findings/${findingId}/advice`
      ),
  },
  reports: {
    latest: (projectId: string) =>
      request<import("@/types").Report>(`/api/v1/reports/${projectId}/latest`),
    list: (projectId: string) =>
      request<import("@/types").Report[]>(`/api/v1/reports/${projectId}`),
  },
  chat: {
    ask: (projectId: string, question: string) =>
      request<{ answer: string; sources: unknown[] }>("/api/v1/chat", {
        method: "POST",
        body: JSON.stringify({ project_id: projectId, question }),
      }),
  },
}
