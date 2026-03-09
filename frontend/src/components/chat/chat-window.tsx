"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"
import { Send, Bot, User } from "lucide-react"
import { Spinner } from "@/components/ui/spinner"

interface Message {
  role: "user" | "assistant"
  content: string
}

export function ChatWindow({ projectId }: { projectId: string }) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hello! I'm Archon. Ask me anything about the analyzed system — endpoints, tables, security findings, or recommendations." }
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  async function send() {
    const question = input.trim()
    if (!question || loading) return
    setInput("")
    setMessages(prev => [...prev, { role: "user", content: question }])
    setLoading(true)
    try {
      const res = await api.chat.ask(projectId, question)
      setMessages(prev => [...prev, { role: "assistant", content: res.answer }])
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Failed to get response"
      setMessages(prev => [...prev, { role: "assistant", content: `Error: ${message}` }])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex flex-col h-[600px] bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-8 h-8 bg-archon-500/20 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-4 h-4 text-archon-400" />
              </div>
            )}
            <div className={`max-w-[75%] rounded-xl px-4 py-3 text-sm ${
              msg.role === "user"
                ? "bg-archon-600 text-white"
                : "bg-gray-700 text-gray-200"
            }`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
            {msg.role === "user" && (
              <div className="w-8 h-8 bg-gray-700 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                <User className="w-4 h-4 text-gray-400" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 bg-archon-500/20 rounded-lg flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-archon-400" />
            </div>
            <div className="bg-gray-700 rounded-xl px-4 py-3">
              <Spinner className="w-4 h-4" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="border-t border-gray-700 p-4">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about endpoints, database, security findings..."
            className="h-10 py-2 text-sm"
            rows={1}
          />
          <Button onClick={send} disabled={loading || !input.trim()} size="sm" className="shrink-0 px-3">
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-xs text-gray-500 mt-2">Press Enter to send, Shift+Enter for newline</p>
      </div>
    </div>
  )
}
