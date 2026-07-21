"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Bot, User, Database, Sparkles, Share2, X } from "lucide-react";
import AppNav from "@/components/layout/AppNav";
import KnowledgeGraph from "@/components/graph/KnowledgeGraph";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: any[];
  suggestedQuestions?: string[];
  queryForGraph?: string;
};

const SESSION_STORAGE_KEY = "copilot_session_id";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [openGraphIdx, setOpenGraphIdx] = useState<number | null>(null);
  const sessionIdRef = useRef<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    let existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!existing) {
      existing = crypto.randomUUID();
      window.sessionStorage.setItem(SESSION_STORAGE_KEY, existing);
    }
    sessionIdRef.current = existing;
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Close the graph modal on Escape, and stop background scroll while open.
  useEffect(() => {
    if (openGraphIdx === null) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpenGraphIdx(null);
    }

    document.addEventListener("keydown", handleKeyDown);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = prevOverflow;
    };
  }, [openGraphIdx]);

  async function sendMessage(overrideText?: string) {
    const question = (overrideText ?? input).trim();
    if (!question) return;

    const userMessage: Message = {
      role: "user",
      content: question,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/answer`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question,
            session_id: sessionIdRef.current || undefined,
          }),
        }
      );

      const data = await res.json();

      if (data.session_id) {
        sessionIdRef.current = data.session_id;
        if (typeof window !== "undefined") {
          window.sessionStorage.setItem(SESSION_STORAGE_KEY, data.session_id);
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources || [],
          suggestedQuestions: data.suggested_questions || [],
          queryForGraph: question,
        },
      ]);
    } catch (err) {
      console.error(err);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Failed to generate response. Please check backend connectivity.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleSuggestedClick(question: string) {
    if (loading) return;
    sendMessage(question);
  }

  const activeGraphMessage =
    openGraphIdx !== null ? messages[openGraphIdx] : null;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_45%),_linear-gradient(135deg,_#050816_0%,_#0b1120_45%,_#020617_100%)] text-white">
      <AppNav />
      <div className="mx-auto flex h-[calc(100vh-88px)] max-w-6xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-6 rounded-2xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-cyan-950/20">
          <h1 className="text-2xl font-semibold text-white">
            Enterprise Copilot
          </h1>

          <p className="mt-1 text-sm text-zinc-400">
            Chat with your enterprise knowledge base in one unified workspace.
          </p>
        </div>

        <div className="dark-scrollbar flex-1 overflow-y-auto rounded-2xl border border-white/10 bg-zinc-900/80 p-5 shadow-2xl shadow-black/20 space-y-5">
          {messages.length === 0 && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <Bot
                  size={42}
                  className="mx-auto text-zinc-600"
                />

                <h2 className="mt-4 text-lg font-medium">
                  Start a conversation
                </h2>

                <p className="text-zinc-500 text-sm mt-1">
                  Ask questions about uploaded documents,
                  SOWs, discovery outputs and enterprise data.
                </p>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => {
            const isLastMessage = idx === messages.length - 1;

            return (
              <div
                key={idx}
                className={`flex flex-col gap-2 ${
                  msg.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-xl border p-4 ${
                    msg.role === "user"
                      ? "bg-white text-black border-white"
                      : "bg-zinc-950 border-zinc-800 text-zinc-200"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    {msg.role === "user" ? (
                      <User size={16} />
                    ) : (
                      <Bot size={16} />
                    )}

                    <span className="text-xs font-medium">
                      {msg.role === "user"
                        ? "You"
                        : "Enterprise Copilot"}
                    </span>
                  </div>

                  <div className="whitespace-pre-wrap text-sm">
                    {msg.content}
                  </div>

                  {msg.role === "assistant" &&
                    msg.sources &&
                    msg.sources.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-zinc-800">
                        <div className="flex items-center gap-2 mb-2 text-xs text-zinc-400">
                          <Database size={14} />
                          Sources
                        </div>

                        <div className="flex flex-wrap gap-2">
                          {msg.sources.map(
                            (s: any, i: number) => (
                              <span
                                key={i}
                                className="text-xs px-2 py-1 rounded-md bg-zinc-800 text-zinc-300 border border-zinc-700"
                              >
                                {s.title || `Doc ${s.doc_id}`}
                              </span>
                            )
                          )}
                        </div>
                      </div>
                    )}

                  {msg.role === "assistant" &&
                    msg.sources &&
                    msg.sources.length > 0 && (
                      <div className="mt-3">
                        <button
                          onClick={() => setOpenGraphIdx(idx)}
                          className="flex items-center gap-2 text-xs text-cyan-400 hover:text-cyan-300 transition"
                        >
                          <Share2 size={13} />
                          View knowledge graph
                        </button>
                      </div>
                    )}

                  {msg.role === "assistant" &&
                    isLastMessage &&
                    !loading &&
                    msg.suggestedQuestions &&
                    msg.suggestedQuestions.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-zinc-800">
                        <div className="flex items-center gap-2 mb-2 text-xs text-zinc-400">
                          <Sparkles size={14} />
                          Suggested follow-ups
                        </div>

                        <div className="flex flex-col gap-2">
                          {msg.suggestedQuestions.map((q, i) => (
                            <button
                              key={i}
                              onClick={() => handleSuggestedClick(q)}
                              className="text-left text-xs px-3 py-2 rounded-md bg-zinc-900 text-zinc-300 border border-zinc-700 hover:border-[#c90c61] hover:text-white transition"
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex items-center gap-2 text-sm text-zinc-500">
              <Bot size={16} />
              Thinking...
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="mt-4 flex gap-3 rounded-2xl border border-white/10 bg-zinc-900/80 p-3 shadow-lg shadow-black/20">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about your enterprise data..."
            className="flex-1 bg-transparent outline-none text-sm text-white placeholder:text-zinc-500"
            onKeyDown={(e) =>
              e.key === "Enter" && sendMessage()
            }
          />

          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="flex items-center gap-2 rounded-xl bg-[#c90c61] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#a70a4d] disabled:opacity-50"
          >
            <Send size={15} />
            Send
          </button>
        </div>
      </div>

      {/* Knowledge graph modal */}
      {activeGraphMessage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-8"
          onClick={() => setOpenGraphIdx(null)}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

          {/* Panel */}
          <div
            onClick={(e) => e.stopPropagation()}
            className="relative flex h-[85vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-cyan-900/40 bg-zinc-950 shadow-2xl shadow-cyan-950/30"
          >
            <div className="flex items-center justify-between border-b border-cyan-900/30 bg-zinc-900/60 px-5 py-4">
              <div className="flex flex-col">
                <span className="flex items-center gap-2 text-sm text-cyan-400">
                  <Share2 size={14} />
                  Knowledge graph
                </span>
                <span className="mt-0.5 text-xs text-zinc-500">
                  {activeGraphMessage.sources?.length} cited source
                  {activeGraphMessage.sources?.length !== 1 ? "s" : ""}
                </span>
              </div>

              <button
                onClick={() => setOpenGraphIdx(null)}
                className="rounded-lg p-1.5 text-zinc-500 transition hover:bg-white/5 hover:text-zinc-200"
                aria-label="Close knowledge graph"
              >
                <X size={18} />
              </button>
            </div>

            {/* Graph gets the full remaining space to lay itself out — no
                cramped fixed height or forced scroll container. */}
            <div className="flex-1 overflow-auto p-4">
              <KnowledgeGraph
                key={openGraphIdx}
                docIds={activeGraphMessage.sources?.map((s: any) => s.doc_id) || []}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}