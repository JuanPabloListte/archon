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
  users: {
    me: () => request<{ id: string; email: string; created_at: string; avatar_url?: string }>("/api/v1/users/me"),
    updateMe: (email: string) =>
      request<{ id: string; email: string; created_at: string }>("/api/v1/users/me", {
        method: "PATCH",
        body: JSON.stringify({ email }),
      }),
    changePassword: (current_password: string, new_password: string) =>
      request<void>("/api/v1/users/me/password", {
        method: "POST",
        body: JSON.stringify({ current_password, new_password }),
      }),
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
    updateSettings: (id: string, settings: { audit_system_prompt?: string | null }) =>
      request<import("@/types").Project>(`/api/v1/projects/${id}/settings`, {
        method: "PATCH",
        body: JSON.stringify(settings),
      }),
  },
  connections: {
    create: (projectId: string, type: string, config: Record<string, unknown>) =>
      request<import("@/types").Connection>("/api/v1/connections", {
        method: "POST",
        body: JSON.stringify({ project_id: projectId, type, config }),
      }),
    list: (projectId: string) =>
      request<import("@/types").Connection[]>(`/api/v1/connections/project/${projectId}`),
    delete: (connectionId: string) =>
      request<void>(`/api/v1/connections/${connectionId}`, { method: "DELETE" }),
  },
  audits: {
    run: (projectId: string, options?: { system_prompt?: string }) =>
      request<{ message: string; project_id: string }>(`/api/v1/audits/run/${projectId}`, {
        method: "POST",
        body: JSON.stringify(options ?? {}),
      }),
    findings: (projectId: string) =>
      request<import("@/types").Finding[]>(`/api/v1/audits/findings/${projectId}`),
    updateFindingStatus: (findingId: string, status: "open" | "fixed" | "ignored") =>
      request<import("@/types").Finding>(`/api/v1/audits/findings/${findingId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }),
    insights: (projectId: string) =>
      request<{ prioritized: { id: string; severity: string; title: string }[]; summary: string }>(
        `/api/v1/audits/insights/${projectId}`
      ),
    findingAdvice: (findingId: string) =>
      request<{ finding_id: string; recommendations: string }>(
        `/api/v1/audits/findings/${findingId}/advice`
      ),
    runs: (projectId: string) =>
      request<import("@/types").AuditRun[]>(`/api/v1/audits/runs/${projectId}`),
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
  dataset: {
    stats: () => request<{ your_findings: number; global_patterns: number; confirmed_solutions: number; total_examples: number }>("/api/v1/dataset/stats"),
    presets: () => request<{ id: string; preview: string }[]>("/api/v1/dataset/presets"),
    exportUrl: (fmt: "jsonl" | "alpaca" = "jsonl", preset?: string, systemPrompt?: string) => {
      const params = new URLSearchParams({ fmt });
      if (preset) params.set("preset", preset);
      if (systemPrompt) params.set("system_prompt", systemPrompt);
      return `${API_URL}/api/v1/dataset/export?${params.toString()}`;
    },
  },
  credentials: {
    list: () => request<import("@/types").Credential[]>("/api/v1/credentials"),
    create: (data: { provider: string; label?: string; api_key?: string; model: string; base_url?: string }) =>
      request<import("@/types").Credential>("/api/v1/credentials", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: string, data: { label?: string; api_key?: string; model?: string; base_url?: string }) =>
      request<import("@/types").Credential>(`/api/v1/credentials/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (id: string) => request<void>(`/api/v1/credentials/${id}`, { method: "DELETE" }),
    activate: (id: string) =>
      request<import("@/types").Credential>(`/api/v1/credentials/${id}/activate`, { method: "POST" }),
    deactivate: (id: string) =>
      request<import("@/types").Credential>(`/api/v1/credentials/${id}/deactivate`, { method: "POST" }),
    models: (provider: string, api_key?: string, base_url?: string) =>
      request<{ models: string[] }>("/api/v1/credentials/models", {
        method: "POST",
        body: JSON.stringify({ provider, api_key, base_url }),
      }),
  },
  apiKeys: {
    list: () => request<import("@/types").ApiKey[]>("/api/v1/api-keys"),
    create: (name: string) =>
      request<import("@/types").ApiKeyCreated>("/api/v1/api-keys", {
        method: "POST",
        body: JSON.stringify({ name }),
      }),
    revoke: (id: string) => request<void>(`/api/v1/api-keys/${id}`, { method: "DELETE" }),
  },
  schedules: {
    list: (projectId: string) =>
      request<import("@/types").AuditSchedule[]>(`/api/v1/projects/${projectId}/schedules`),
    create: (projectId: string, data: Partial<import("@/types").AuditSchedule>) =>
      request<import("@/types").AuditSchedule>(`/api/v1/projects/${projectId}/schedules`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (projectId: string, scheduleId: string, data: Partial<import("@/types").AuditSchedule>) =>
      request<import("@/types").AuditSchedule>(`/api/v1/projects/${projectId}/schedules/${scheduleId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (projectId: string, scheduleId: string) =>
      request<void>(`/api/v1/projects/${projectId}/schedules/${scheduleId}`, { method: "DELETE" }),
    alerts: (projectId: string, scheduleId: string) =>
      request<import("@/types").AlertEvent[]>(`/api/v1/projects/${projectId}/schedules/${scheduleId}/alerts`),
  },
  customRules: {
    list: (projectId: string) =>
      request<import("@/types").CustomRule[]>(`/api/v1/projects/${projectId}/rules`),
    example: () => request<{ rule_yaml: string }>("/api/v1/projects/example/rules/example"),
    create: (projectId: string, data: { name: string; rule_yaml: string; description?: string }) =>
      request<import("@/types").CustomRule>(`/api/v1/projects/${projectId}/rules`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (projectId: string, ruleId: string, data: Partial<{ name: string; rule_yaml: string; description: string; is_active: boolean }>) =>
      request<import("@/types").CustomRule>(`/api/v1/projects/${projectId}/rules/${ruleId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (projectId: string, ruleId: string) =>
      request<void>(`/api/v1/projects/${projectId}/rules/${ruleId}`, { method: "DELETE" }),
    test: (projectId: string, ruleId: string) =>
      request<{ matched: number; findings: { title: string; severity: string; category: string; description: string; recommendation: string }[] }>(
        `/api/v1/projects/${projectId}/rules/${ruleId}/test`, { method: "POST" }
      ),
  },
}
