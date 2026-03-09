"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import { Report } from "@/types"
import { Spinner } from "@/components/ui/spinner"
import { ArrowLeft } from "lucide-react"

export default function ReportPage() {
  const { id } = useParams<{ id: string }>()
  const [report, setReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.reports.latest(id).then(setReport).catch(() => setReport(null)).finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>

  return (
    <div>
      <div className="mb-6">
        <Link href={`/projects/${id}`} className="text-gray-400 hover:text-white text-sm flex items-center gap-1 mb-4">
          <ArrowLeft className="w-4 h-4" /> Back to project
        </Link>
        <Header title="Technical Report" subtitle={report ? `Generated ${new Date(report.created_at).toLocaleString()}` : undefined} />
      </div>

      {!report ? (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-12 text-center">
          <p className="text-gray-400">No report found. Run an audit to generate one.</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <p className="text-gray-400 text-sm">Health Score</p>
              <p className={`text-3xl font-bold mt-1 ${report.health_score >= 80 ? "text-green-400" : report.health_score >= 60 ? "text-yellow-400" : "text-red-400"}`}>
                {report.health_score}/100
              </p>
            </Card>
            <Card>
              <p className="text-gray-400 text-sm">Endpoints</p>
              <p className="text-3xl font-bold text-white mt-1">{report.report_json?.overview.total_endpoints ?? 0}</p>
            </Card>
            <Card>
              <p className="text-gray-400 text-sm">DB Tables</p>
              <p className="text-3xl font-bold text-white mt-1">{report.report_json?.overview.total_tables ?? 0}</p>
            </Card>
            <Card>
              <p className="text-gray-400 text-sm">Total Issues</p>
              <p className="text-3xl font-bold text-white mt-1">{report.report_json?.overview.total_findings ?? 0}</p>
            </Card>
          </div>

          {report.summary && (
            <Card>
              <CardHeader><CardTitle>Executive Summary</CardTitle></CardHeader>
              <CardContent>
                <p className="text-gray-300">{report.summary}</p>
              </CardContent>
            </Card>
          )}

          {report.report_json?.findings_by_severity && (
            <Card>
              <CardHeader><CardTitle>Issues by Severity</CardTitle></CardHeader>
              <CardContent>
                <div className="flex gap-3 flex-wrap">
                  {Object.entries(report.report_json.findings_by_severity).map(([sev, count]) => (
                    <div key={sev} className="flex items-center gap-2">
                      <Badge variant={sev as "critical" | "high" | "medium" | "low" | "info"}>{sev}</Badge>
                      <span className="text-white font-semibold">{count}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {report.report_json?.findings && report.report_json.findings.length > 0 && (
            <Card>
              <CardHeader><CardTitle>All Findings</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {report.report_json.findings.map(f => (
                    <div key={f.id} className="bg-gray-700/50 rounded-lg p-4">
                      <div className="flex gap-2 mb-2 flex-wrap">
                        <Badge variant={f.severity as "critical" | "high" | "medium" | "low" | "info"}>{f.severity}</Badge>
                        <Badge variant={f.category as "api" | "database" | "security" | "performance"}>{f.category}</Badge>
                      </div>
                      <p className="text-white font-medium mb-1">{f.title}</p>
                      <p className="text-gray-400 text-sm mb-2">{f.description}</p>
                      <p className="text-xs text-gray-500">Fix: {f.recommendation}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
