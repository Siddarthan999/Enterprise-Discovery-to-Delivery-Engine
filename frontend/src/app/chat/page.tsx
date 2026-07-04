"use client";

import { useState } from "react";
import { Send, Bot, User, Database } from "lucide-react";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: any[];
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    if (!input.trim()) return;

    const question = input;

    const userMessage: Message = {
      role: "user",
      content: question,
    };

    setMessages((prev) => [...prev, userMessage]);

    setInput("");
    setLoading(true);

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/answer`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question,
          }),
        }
      );

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources || [],
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

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-6xl mx-auto px-6 py-8 h-screen flex flex-col">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">
            Enterprise Copilot
          </h1>

          <p className="text-sm text-zinc-400 mt-1">
            Chat with your enterprise knowledge base
          </p>
        </div>

        {/* Chat Window */}
        <div className="flex-1 overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900 p-5 space-y-5">
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

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${
                msg.role === "user"
                  ? "justify-end"
                  : "justify-start"
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
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-sm text-zinc-500">
              <Bot size={16} />
              Thinking...
            </div>
          )}
        </div>

        {/* Input */}
        <div className="mt-4 border border-zinc-800 rounded-xl bg-zinc-900 p-3 flex gap-3">
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
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-zinc-200 disabled:opacity-50 flex items-center gap-2"
          >
            <Send size={15} />
            Send
          </button>
        </div>
      </div>
    </div>
  );
}