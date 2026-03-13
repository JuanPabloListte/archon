"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Spinner } from "@/components/ui/spinner"
import { api } from "@/lib/api"
import { AuditSchedule, AlertEvent } from "@/types"
import { ArrowLeft, Plus, Clock, Bell, Trash2, CheckCircle, XCircle, ToggleLeft, ToggleRight } from "lucide-react"

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

export default function SchedulesPage() {
  const { id } = useParams<{ id: string }>()
  const [schedules, setSchedules] = useState<AuditSchedule[]>([])
  const [alerts, setAlerts] = useState<Record<string, AlertEvent[]>>({})
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)

  const [frequency, setFrequency] = useState<"daily" | "weekly" | "custom">("weekly")
  const [hourUtc, setHourUtc] = useState(9)
  const [dayOfWeek, setDayOfWeek] = useState(0)
  const [cronExpr, setCronExpr] = useState("")
  const [alertEmail, setAlertEmail] = useState("")
  const [alertWebhook, setAlertWebhook] = useState("")
  const [threshold, setThreshold] = useState(70)
  const [alertOnCritical, setAlertOnCritical] = useState(true)

  useEffect(() => {
    api.schedules.list(id)
      .then(setSchedules)
      .finally(() => setLoading(false))
  }, [id])

  async function loadAlerts(scheduleId: string) {
    if (alerts[scheduleId]) return
    const events = await api.schedules.alerts(id, scheduleId).catch(() => [])
    setAlerts(prev => ({ ...prev, [scheduleId]: events }))
  }

  async function createSchedule(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const s = await api.schedules.create(id, {
        frequency,
        hour_utc: hourUtc,
        day_of_week: frequency === "weekly" ? dayOfWeek : undefined,
        cron_expression: frequency === "custom" ? cronExpr : undefined,
        alert_email: alertEmail || undefined,
        alert_webhook_url: alertWebhook || undefined,
        health_score_threshold: threshold,
        alert_on_critical: alertOnCritical,
      } as Partial<AuditSchedule>)
      setSchedules(prev => [...prev, s])
      setShowForm(false)
    } finally {
      setSaving(false)
    }
  }

  async function toggleSchedule(s: AuditSchedule) {
    const updated = await api.schedules.update(id, s.id, { is_active: !s.is_active } as Partial<AuditSchedule>)
    setSchedules(prev => prev.map(x => x.id === s.id ? updated : x))
  }

  async function deleteSchedule(scheduleId: string) {
    if (!confirm("Delete this schedule?")) return
    await api.schedules.delete(id, scheduleId)
    setSchedules(prev => prev.filter(s => s.id !== scheduleId))
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link href={`/projects/${id}`} className="t3 hover-t1 transition-colors"><ArrowLeft className="w-4 h-4" /></Link>
        <Header title="Scheduled Audits" subtitle="Automate audits and get alerts when issues arise" />
        <Button className="ml-auto" onClick={() => setShowForm(v => !v)}><Plus className="w-4 h-4 mr-1" />New Schedule</Button>
      </div>

      {showForm && (
        <Card className="mb-6">
          <CardHeader><CardTitle>Configure Schedule</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={createSchedule} className="space-y-4">
              <div>
                <Label>Frequency</Label>
                <div className="flex gap-2 mt-1">
                  {(["daily", "weekly", "custom"] as const).map(f => (
                    <button key={f} type="button" onClick={() => setFrequency(f)}
                      className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors capitalize ${frequency === f ? "bg-archon-500 text-white" : "bg-muted t3 hover-t1"}`}>
                      {f}
                    </button>
                  ))}
                </div>
              </div>

              {frequency === "custom" ? (
                <div>
                  <Label>Cron Expression</Label>
                  <Input value={cronExpr} onChange={e => setCronExpr(e.target.value)} placeholder="0 9 * * 1  (every Monday at 9am UTC)" className="font-mono" />
                </div>
              ) : (
                <div className="flex gap-4">
                  <div className="flex-1">
                    <Label>Hour (UTC)</Label>
                    <Input type="number" min={0} max={23} value={hourUtc} onChange={e => setHourUtc(+e.target.value)} />
                  </div>
                  {frequency === "weekly" && (
                    <div className="flex-1">
                      <Label>Day of week</Label>
                      <select value={dayOfWeek} onChange={e => setDayOfWeek(+e.target.value)}
                        className="w-full rounded-lg border bd1 bg-muted px-3 py-2 text-sm t1 focus:outline-none focus:ring-1 focus:ring-archon-500">
                        {DAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
                      </select>
                    </div>
                  )}
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Alert email (optional)</Label>
                  <Input type="email" value={alertEmail} onChange={e => setAlertEmail(e.target.value)} placeholder="you@example.com" />
                </div>
                <div>
                  <Label>Webhook URL (optional)</Label>
                  <Input value={alertWebhook} onChange={e => setAlertWebhook(e.target.value)} placeholder="https://hooks.slack.com/..." />
                </div>
              </div>

              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <Label>Alert if health score below</Label>
                  <Input type="number" min={0} max={100} value={threshold} onChange={e => setThreshold(+e.target.value)} />
                </div>
                <div className="flex items-center gap-2 pb-2">
                  <input type="checkbox" id="critical" checked={alertOnCritical} onChange={e => setAlertOnCritical(e.target.checked)} className="accent-archon-500" />
                  <Label htmlFor="critical" className="cursor-pointer">Alert on critical findings</Label>
                </div>
              </div>

              <div className="flex gap-2">
                <Button type="submit" loading={saving}>Create Schedule</Button>
                <Button type="button" variant="secondary" onClick={() => setShowForm(false)}>Cancel</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {schedules.length === 0 ? (
        <div className="bg-card border bd1 rounded-xl p-12 text-center">
          <Clock className="w-10 h-10 t4 mx-auto mb-3" />
          <p className="t3">No schedules yet. Create one to automate audits.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {schedules.map(s => (
            <Card key={s.id}>
              <CardContent className="pt-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <Clock className={`w-5 h-5 ${s.is_active ? "text-cyan-500" : "t4"}`} />
                    <div>
                      <p className="t1 font-medium capitalize">{s.frequency === "custom" ? `Custom (${s.cron_expression})` : `${s.frequency} at ${s.hour_utc}:00 UTC${s.frequency === "weekly" ? ` — ${DAYS[s.day_of_week ?? 0]}` : ""}`}</p>
                      <p className="t4 text-xs mt-0.5">
                        {s.next_run_at ? `Next run: ${new Date(s.next_run_at).toLocaleString()}` : "Not scheduled"}
                        {s.last_run_at ? ` · Last run: ${new Date(s.last_run_at).toLocaleString()}` : ""}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => toggleSchedule(s)} className="t3 hover-t1 transition-colors" title={s.is_active ? "Disable" : "Enable"}>
                      {s.is_active ? <ToggleRight className="w-5 h-5 text-archon-400" /> : <ToggleLeft className="w-5 h-5" />}
                    </button>
                    <button onClick={() => deleteSchedule(s.id)} className="t4 hover:text-red-500 transition-colors"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap gap-3 text-xs">
                  <span className="px-2 py-0.5 rounded-full bg-muted t3">Score threshold: {s.health_score_threshold}</span>
                  {s.alert_on_critical && <span className="px-2 py-0.5 rounded-full bg-red-500/10 text-red-400">Alert on critical</span>}
                  {s.alert_email && <span className="px-2 py-0.5 rounded-full bg-muted t3"><Bell className="w-3 h-3 inline mr-1" />{s.alert_email}</span>}
                  {s.alert_webhook_url && <span className="px-2 py-0.5 rounded-full bg-muted t3">Webhook configured</span>}
                </div>

                <button onClick={() => loadAlerts(s.id)} className="mt-3 text-xs text-archon-400 hover:text-archon-300 transition-colors">
                  View alert history →
                </button>
                {alerts[s.id] && (
                  <div className="mt-2 space-y-1">
                    {alerts[s.id].length === 0 ? (
                      <p className="text-xs t4">No alerts triggered yet.</p>
                    ) : alerts[s.id].slice(0, 5).map(ev => (
                      <div key={ev.id} className="flex items-center gap-2 text-xs bg-muted rounded-lg px-3 py-1.5">
                        {ev.success ? <CheckCircle className="w-3 h-3 text-green-500 shrink-0" /> : <XCircle className="w-3 h-3 text-red-500 shrink-0" />}
                        <span className="t2 capitalize">{ev.trigger_type.replace(/_/g, " ")}</span>
                        <span className="t4">Score: {ev.health_score.toFixed(0)}</span>
                        {ev.critical_count > 0 && <span className="text-red-400">{ev.critical_count} critical</span>}
                        <span className="ml-auto t4">{new Date(ev.created_at).toLocaleDateString()}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
