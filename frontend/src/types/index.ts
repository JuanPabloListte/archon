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
  audit_system_prompt: string | null
}

export interface Connection {
  id: string
  project_id: string
  type: "openapi" | "database" | "logs"
  created_at: string
  status: "ingesting" | "done" | "error" | null
  ingestion_error: string | null
  ingested_count: number | null
}

export interface Finding {
  id: string
  project_id: string
  severity: "critical" | "high" | "medium" | "low" | "info"
  category: "api" | "database" | "security" | "performance"
  title: string
  description: string
  recommendation: string
  source: "rule" | "ai"
  status: "open" | "fixed" | "ignored"
  created_at: string
}

export interface Credential {
  id: string
  provider: string
  label: string | null
  api_key_masked: string | null
  model: string
  base_url: string | null
  is_active: boolean
  created_at: string
}

export interface ApiKey {
  id: string
  name: string
  key_prefix: string
  is_active: boolean
  last_used_at: string | null
  created_at: string
}

export interface ApiKeyCreated extends ApiKey {
  token: string
}

export interface AuditSchedule {
  id: string
  project_id: string
  is_active: boolean
  frequency: "daily" | "weekly" | "custom"
  cron_expression: string | null
  hour_utc: number
  day_of_week: number | null
  alert_email: string | null
  alert_webhook_url: string | null
  health_score_threshold: number
  alert_on_critical: boolean
  last_run_at: string | null
  next_run_at: string | null
  created_at: string
}

export interface AlertEvent {
  id: string
  trigger_type: string
  health_score: number
  critical_count: number
  notification_sent: string
  success: boolean
  error_message: string | null
  created_at: string
}

export interface CustomRule {
  id: string
  project_id: string
  name: string
  description: string | null
  category: "api" | "database" | "security" | "performance"
  severity: "critical" | "high" | "medium" | "low" | "info"
  target: "endpoints" | "tables"
  rule_yaml: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AuditRun {
  id: string
  project_id: string
  health_score: number
  total_findings: number
  summary: string | null
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
