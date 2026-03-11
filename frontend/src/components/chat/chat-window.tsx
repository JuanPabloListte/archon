"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { getToken } from "@/lib/auth"
import { Send, Bot, User, ChevronDown, ChevronUp, FileText, Database, Shield } from "lucide-react"
import { Spinner } from "@/components/ui/spinner"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Source { source_type: string; content: string; score?: number }
interface ThinkingStep { text: string }
interface Message {
  role: "user" | "assistant"
  content: string
  streaming?: boolean
  steps?: ThinkingStep[]
  sources?: Source[]
  prompt?: string
}

function SourceIcon({ type }: { type: string }) {
  if (type === "endpoint") return <FileText className="w-3 h-3" />
  if (type === "table") return <Database className="w-3 h-3" />
  return <Shield className="w-3 h-3" />
}

function ThinkingPanel({ steps, sources, prompt }: { steps: ThinkingStep[]; sources?: Source[]; prompt?: string }) {
  const [open, setOpen] = useState(true)
  const [showPrompt, setShowPrompt] = useState(false)

  return (
    <div className="text-xs border bd1 rounded-lg overflow-hidden mb-2">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 py-2 bg-muted t2 hover-subtle transition-colors"
      >
        <span className="font-medium">Thinking process</span>
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>

      {open && (
        <div className="bg-page px-3 py-2 space-y-2">
          {steps.map((s, i) => (
            <div key={i} className="flex items-center gap-2 t3">
              <span className="w-1.5 h-1.5 rounded-full bg-archon-400 shrink-0" />
              {s.text}
            </div>
          ))}

          {sources && sources.length > 0 && (
            <div className="mt-2 space-y-1">
              <p className="t4 font-medium">Context retrieved:</p>
              {sources.map((src, i) => (
                <div key={i} className="flex items-start gap-2 t3 bg-muted rounded px-2 py-1">
                  <SourceIcon type={src.source_type} />
                  <div className="min-w-0">
                    <span className="text-archon-400 font-medium">[{src.source_type}]</span>{" "}
                    <span className="truncate">{src.content.slice(0, 120)}{src.content.length > 120 ? "…" : ""}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {prompt && (
            <div className="mt-1">
              <button
                onClick={() => setShowPrompt(p => !p)}
                className="t4 hover-t1 transition-colors flex items-center gap-1"
              >
                {showPrompt ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {showPrompt ? "Hide prompt" : "Show full prompt"}
              </button>
              {showPrompt && (
                <pre className="mt-1 t3 bg-muted rounded p-2 whitespace-pre-wrap overflow-auto max-h-48 text-xs">
                  {prompt}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function ChatWindow({ projectId, pendingQuestion, onPendingConsumed }: {
  projectId: string
  pendingQuestion?: string
  onPendingConsumed?: () => void
}) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hello! I'm Archon. Ask me anything about the analyzed system — endpoints, tables, security findings, or recommendations." }
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (pendingQuestion) {
      setInput(pendingQuestion)
      onPendingConsumed?.()
      setTimeout(() => textareaRef.current?.focus(), 0)
    }
  }, [pendingQuestion])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  async function send() {
    const question = input.trim()
    if (!question || loading) return
    setInput("")
    setMessages(prev => [...prev, { role: "user", content: question }])
    setLoading(true)
    setMessages(prev => [...prev, { role: "assistant", content: "", streaming: true, steps: [], sources: undefined, prompt: undefined }])

    try {
      const token = getToken()
      const resp = await fetch(`${API_URL}/api/v1/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ project_id: projectId, question }),
      })
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)

      const reader = resp.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() ?? ""
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          try { handleEvent(JSON.parse(line.slice(6))) } catch { }
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to get response"
      setMessages(prev => { const u = [...prev]; const l = u[u.length - 1]; if (l.role === "assistant") u[u.length - 1] = { ...l, content: `Error: ${msg}`, streaming: false }; return u })
    } finally {
      setLoading(false)
      setMessages(prev => { const u = [...prev]; const l = u[u.length - 1]; if (l.role === "assistant" && l.streaming) u[u.length - 1] = { ...l, streaming: false }; return u })
    }
  }

  function handleEvent(event: { type: string; text?: string; sources?: Source[]; answer?: string; prompt?: string }) {
    setMessages(prev => {
      const updated = [...prev]
      const last = updated[updated.length - 1]
      if (last.role !== "assistant") return prev
      if (event.type === "step")    return [...updated.slice(0, -1), { ...last, steps: [...(last.steps ?? []), { text: event.text! }] }]
      if (event.type === "context") return [...updated.slice(0, -1), { ...last, sources: event.sources }]
      if (event.type === "prompt")  return [...updated.slice(0, -1), { ...last, prompt: event.text }]
      if (event.type === "token")   return [...updated.slice(0, -1), { ...last, content: last.content + event.text! }]
      if (event.type === "done")    return [...updated.slice(0, -1), { ...last, streaming: false }]
      return prev
    })
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <div className="flex flex-col bg-card border bd1 rounded-xl overflow-hidden" style={{ height: "calc(100vh - 220px)" }}>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-8 h-8 bg-archon-500/20 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-4 h-4 text-archon-400" />
              </div>
            )}
            <div className={`max-w-[80%] ${msg.role === "user" ? "" : "w-full"}`}>
              {msg.role === "assistant" && (msg.steps?.length ?? 0) > 0 && (
                <ThinkingPanel steps={msg.steps!} sources={msg.sources} prompt={msg.prompt} />
              )}
              {(msg.content || msg.streaming) && (
                <div className={`rounded-xl px-4 py-3 text-sm ${msg.role === "user" ? "bg-archon-600 text-white" : "bg-muted t1"}`}>
                  {msg.content ? <p className="whitespace-pre-wrap">{msg.content}{msg.streaming ? "▍" : ""}</p> : <Spinner className="w-4 h-4" />}
                </div>
              )}
            </div>
            {msg.role === "user" && (
              <div className="w-8 h-8 bg-subtle rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                <User className="w-4 h-4 t3" />
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="border-t bd1 p-4">
        <div className="flex gap-2">
          <Textarea
            ref={textareaRef}
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
        <p className="text-xs t4 mt-2">Press Enter to send, Shift+Enter for newline</p>
      </div>
    </div>
  )
}
