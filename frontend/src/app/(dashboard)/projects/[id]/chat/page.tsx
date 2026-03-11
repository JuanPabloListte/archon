"use client"

import { useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { ChatWindow } from "@/components/chat/chat-window"
import { ArrowLeft } from "lucide-react"

const SUGGESTIONS = [
  "Which endpoints don't have authentication?",
  "What are the most critical security issues?",
  "Which database tables are missing indexes?",
  "What are the top 3 things to fix immediately?",
  "Are there any sensitive data exposure issues?",
]

export default function ChatPage() {
  const { id } = useParams<{ id: string }>()
  const [pendingQuestion, setPendingQuestion] = useState("")

  return (
    <div>
      <div className="mb-6">
        <Link href={`/projects/${id}`} className="t3 hover-t1 text-sm flex items-center gap-1 mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to project
        </Link>
        <Header title="AI Chat" subtitle="Ask questions about the analyzed system" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChatWindow
            projectId={id}
            pendingQuestion={pendingQuestion}
            onPendingConsumed={() => setPendingQuestion("")}
          />
        </div>
        <div className="space-y-3">
          <div className="bg-card border bd1 rounded-xl p-4">
            <h3 className="t1 font-medium mb-3">Suggested questions</h3>
            <div className="space-y-2 text-sm t3">
              {SUGGESTIONS.map(q => (
                <button
                  key={q}
                  onClick={() => setPendingQuestion(q)}
                  className="w-full text-left hover-t1 hover-muted transition-colors rounded-lg px-2 py-1.5 -mx-2"
                >
                  → {q}
                </button>
              ))}
            </div>
          </div>
          <div className="bg-card border bd1 rounded-xl p-4">
            <h3 className="t1 font-medium mb-2">About Archon AI</h3>
            <p className="t3 text-sm">
              Archon uses RAG (Retrieval-Augmented Generation) to answer questions using the actual data analyzed from your system. Powered by a local LLM via Ollama.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
