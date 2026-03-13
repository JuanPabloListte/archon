"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Spinner } from "@/components/ui/spinner"
import { api } from "@/lib/api"
import { CustomRule } from "@/types"
import { ArrowLeft, Plus, Zap, Trash2, Play, CheckCircle, XCircle, ToggleLeft, ToggleRight, ChevronDown, ChevronUp } from "lucide-react"

const SEV_COLORS: Record<string, string> = {
  critical: "text-red-500 bg-red-500/10",
  high: "text-orange-500 bg-orange-500/10",
  medium: "text-yellow-500 bg-yellow-500/10",
  low: "text-blue-400 bg-blue-400/10",
  info: "text-gray-400 bg-gray-400/10",
}

const EXAMPLE = `name: "Example: DELETE without auth"
description: "All DELETE endpoints must require authentication"
category: security
severity: high
target: endpoints
conditions:
  - field: method
    operator: eq
    value: DELETE
  - field: auth_required
    operator: eq
    value: "false"
match: all
finding_title: "Unauthenticated DELETE: {path}"
finding_description: "Endpoint {method} {path} allows deletions without auth."
finding_recommendation: "Add authentication middleware to this endpoint."`

export default function CustomRulesPage() {
  const { id } = useParams<{ id: string }>()
  const [rules, setRules] = useState<CustomRule[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedRule, setExpandedRule] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, { matched: number; findings: { title: string; severity: string }[] }>>({})
  const [testing, setTesting] = useState<string | null>(null)

  const [ruleName, setRuleName] = useState("")
  const [ruleYaml, setRuleYaml] = useState(EXAMPLE)

  useEffect(() => {
    api.customRules.list(id)
      .then(setRules)
      .finally(() => setLoading(false))
  }, [id])

  async function createRule(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const rule = await api.customRules.create(id, { name: ruleName || "My Rule", rule_yaml: ruleYaml })
      setRules(prev => [...prev, rule])
      setShowForm(false)
      setRuleName("")
      setRuleYaml(EXAMPLE)
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || "Failed to create rule")
    } finally {
      setSaving(false)
    }
  }

  async function toggleRule(rule: CustomRule) {
    const updated = await api.customRules.update(id, rule.id, { is_active: !rule.is_active })
    setRules(prev => prev.map(r => r.id === rule.id ? updated : r))
  }

  async function deleteRule(ruleId: string) {
    if (!confirm("Delete this rule?")) return
    await api.customRules.delete(id, ruleId)
    setRules(prev => prev.filter(r => r.id !== ruleId))
  }

  async function testRule(ruleId: string) {
    setTesting(ruleId)
    try {
      const result = await api.customRules.test(id, ruleId)
      setTestResults(prev => ({ ...prev, [ruleId]: result }))
      setExpandedRule(ruleId)
    } finally {
      setTesting(null)
    }
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link href={`/projects/${id}`} className="t3 hover-t1 transition-colors"><ArrowLeft className="w-4 h-4" /></Link>
        <Header title="Custom Rules" subtitle="Define your own audit checks using YAML" />
        <Button className="ml-auto" onClick={() => setShowForm(v => !v)}><Plus className="w-4 h-4 mr-1" />New Rule</Button>
      </div>

      {showForm && (
        <Card className="mb-6">
          <CardHeader><CardTitle>New Custom Rule</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={createRule} className="space-y-4">
              <div>
                <Label>Rule name</Label>
                <Input value={ruleName} onChange={e => setRuleName(e.target.value)} placeholder="Inferred from YAML if empty" />
              </div>
              <div>
                <Label>Rule definition (YAML)</Label>
                <textarea
                  value={ruleYaml}
                  onChange={e => setRuleYaml(e.target.value)}
                  rows={16}
                  className="w-full mt-1 rounded-lg border bd1 bg-muted px-3 py-2 text-sm t1 font-mono resize-none focus:outline-none focus:ring-1 focus:ring-archon-500"
                />
                <p className="text-xs t4 mt-1">
                  Operators: eq, neq, contains, not_contains, starts_with, ends_with, gt, lt, gte, lte, is_empty, is_not_empty, matches_regex
                </p>
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <div className="flex gap-2">
                <Button type="submit" loading={saving}>Save Rule</Button>
                <Button type="button" variant="secondary" onClick={() => { setShowForm(false); setError(null) }}>Cancel</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {rules.length === 0 && !showForm ? (
        <div className="bg-card border bd1 rounded-xl p-12 text-center">
          <Zap className="w-10 h-10 t4 mx-auto mb-3" />
          <p className="t3 mb-2">No custom rules yet.</p>
          <p className="text-xs t4">Create rules in YAML to extend the built-in audit checks with your own logic.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rules.map(rule => (
            <Card key={rule.id}>
              <CardContent className="pt-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <Zap className={`w-4 h-4 shrink-0 ${rule.is_active ? "text-yellow-500" : "t4"}`} />
                    <div className="min-w-0">
                      <p className="t1 font-medium truncate">{rule.name}</p>
                      {rule.description && <p className="t4 text-xs mt-0.5 truncate">{rule.description}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SEV_COLORS[rule.severity]}`}>{rule.severity}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-muted t3 capitalize">{rule.category}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-muted t4">{rule.target}</span>
                    <button onClick={() => testRule(rule.id)} title="Test rule" className="t3 hover:text-archon-400 transition-colors" disabled={testing === rule.id}>
                      {testing === rule.id ? <Spinner className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>
                    <button onClick={() => toggleRule(rule)} className="t3 hover-t1 transition-colors">
                      {rule.is_active ? <ToggleRight className="w-5 h-5 text-archon-400" /> : <ToggleLeft className="w-5 h-5" />}
                    </button>
                    <button onClick={() => setExpandedRule(expandedRule === rule.id ? null : rule.id)} className="t4 hover-t1 transition-colors">
                      {expandedRule === rule.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    <button onClick={() => deleteRule(rule.id)} className="t4 hover:text-red-500 transition-colors"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </div>

                {expandedRule === rule.id && (
                  <div className="mt-4 space-y-3">
                    <pre className="bg-muted rounded-lg p-3 text-xs font-mono t2 overflow-auto max-h-48">{rule.rule_yaml}</pre>
                    {testResults[rule.id] && (
                      <div className="border bd1 rounded-lg p-3">
                        <p className="text-xs font-medium t2 mb-2">
                          Test result: <span className={testResults[rule.id].matched > 0 ? "text-orange-400" : "text-green-400"}>
                            {testResults[rule.id].matched} match{testResults[rule.id].matched !== 1 ? "es" : ""}
                          </span>
                        </p>
                        {testResults[rule.id].findings.slice(0, 5).map((f, i) => (
                          <div key={i} className="flex items-center gap-2 text-xs t3 py-1 border-t bd1">
                            <span className={`w-2 h-2 rounded-full shrink-0 ${f.severity === "critical" ? "bg-red-500" : f.severity === "high" ? "bg-orange-500" : "bg-yellow-500"}`} />
                            {f.title}
                          </div>
                        ))}
                      </div>
                    )}
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
