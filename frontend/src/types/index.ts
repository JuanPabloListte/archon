export interface User {
  id: string
  email: string
}

export interface Project {
  id: string
  name: string
  description: string | null
  owner_id: string
  created_at: string
}

export interface Connection {
  id: string
  project_id: string
  type: "openapi" | "database" | "logs"
  created_at: string
}

export interface Finding {
  id: string
  project_id: string
  severity: "critical" | "high" | "medium" | "low" | "info"
  category: "api" | "database" | "security" | "performance"
  title: string
  description: string
  recommendation: string
  created_at: string
}

export interface Report {
  id: string
  project_id: string
  health_score: number
  summary: string | null
  report_json: {
    generated_at: string
    project: { id: string; name: string }
    overview: {
      total_endpoints: number
      total_tables: number
      total_findings: number
      health_score: number
    }
    findings_by_severity: Record<string, number>
    findings_by_category: Record<string, number>
    findings: Finding[]
  } | null
  created_at: string
}
