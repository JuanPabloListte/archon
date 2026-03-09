"use client"

import { useParams } from "next/navigation"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { ChatWindow } from "@/components/chat/chat-window"
import { ArrowLeft } from "lucide-react"

export default function ChatPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <div>
      <div className="mb-6">
        <Link href={`/projects/${id}`} className="text-gray-400 hover:text-white text-sm flex items-center gap-1 mb-4">
          <ArrowLeft className="w-4 h-4" /> Back to project
        </Link>
        <Header title="AI Chat" subtitle="Ask questions about the analyzed system" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChatWindow projectId={id} />
        </div>
        <div className="space-y-3">
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
            <h3 className="text-white font-medium mb-3">Suggested questions</h3>
            <div className="space-y-2 text-sm text-gray-400">
              {[
                "Which endpoints don't have authentication?",
                "What are the most critical security issues?",
                "Which database tables are missing indexes?",
                "What are the top 3 things to fix immediately?",
                "Are there any sensitive data exposure issues?",
              ].map(q => (
                <p key={q} className="cursor-default hover:text-gray-300 transition-colors">→ {q}</p>
              ))}
            </div>
          </div>
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
            <h3 className="text-white font-medium mb-2">About Archon AI</h3>
            <p className="text-gray-400 text-sm">
              Archon uses RAG (Retrieval-Augmented Generation) to answer questions using the actual data analyzed from your system. Powered by a local LLM via Ollama.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
