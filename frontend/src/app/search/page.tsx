"use client";

import { searchDocuments } from "@/lib/api";
import { Search } from "lucide-react";
import KnowledgeGraph from "@/components/graph/KnowledgeGraph";
import AppNav from "@/components/layout/AppNav";
import { useState } from "react";

type SearchResult = {
  doc_id: number;
  title: string;
  content?: string;
  type?: string;
  source?: string;
  uploaded_at?: string;
  score: number;
};

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);

  async function handleSearch() {
    if (!query.trim()) return;

    setLoading(true);

    try {
      const data = await searchDocuments(query);
      setResults(data);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  }

  const showResults = results.length > 0 || loading;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_45%),_linear-gradient(135deg,_#050816_0%,_#0b1120_45%,_#020617_100%)] text-white">
      <AppNav />

      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-cyan-950/20">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-[#c90c61]/10 p-2 text-[#c90c61]">
              <Search size={20} />
            </div>

            <div>
              <h1 className="text-2xl font-semibold text-white">
                Enterprise Search
              </h1>

              <p className="mt-0.5 text-sm text-zinc-400">
                Hybrid retrieval (Vector + Graph) across your knowledge base.
              </p>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mt-6 flex flex-col gap-3 rounded-2xl border border-white/10 bg-zinc-900/80 p-4 shadow-lg shadow-black/20 sm:flex-row">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search documents, SOWs, emails..."
            className="flex-1 rounded-xl border border-white/10 bg-zinc-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />

          <button
            onClick={handleSearch}
            disabled={loading}
            className="rounded-xl bg-[#c90c61] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#a70a4d] disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="mt-6 text-sm text-zinc-400">
            Searching knowledge base...
          </div>
        )}

        {/* Results + Graph */}
        <div
          className={`mt-6 grid gap-6 ${
            showResults
              ? "xl:grid-cols-[1.2fr_0.8fr]"
              : "grid-cols-1"
          }`}
        >
          {/* Results Panel */}
          {showResults && (
            <div className="rounded-2xl border border-white/10 bg-zinc-900/80 p-4 shadow-lg shadow-black/20">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-white">
                  Search Results
                </h2>

                {!loading && (
                  <span className="text-xs text-zinc-500">
                    {results.length} result
                    {results.length !== 1 ? "s" : ""}
                  </span>
                )}
              </div>

              <div className="space-y-4">
                {results.map((r) => (
                  <div
                    key={r.doc_id}
                    className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-4 transition hover:bg-zinc-800"
                  >
                    {/* Title */}
                    <div className="flex items-center justify-between gap-4">
                      <h2 className="font-medium text-white">
                        {r.title}
                      </h2>

                      <span className="text-xs text-zinc-400 whitespace-nowrap">
                        score: {r.score.toFixed(3)}
                      </span>
                    </div>

                    {/* Metadata */}
                    <div className="mt-2 flex flex-wrap gap-3 text-xs text-zinc-500">
                      {r.type && <span>type: {r.type}</span>}
                      {r.source && <span>source: {r.source}</span>}
                      {r.uploaded_at && (
                        <span>{r.uploaded_at}</span>
                      )}
                    </div>

                    {/* Preview */}
                    {r.content && (
                      <p className="mt-3 line-clamp-3 text-sm text-zinc-300">
                        {r.content}
                      </p>
                    )}

                    {/* Match Type */}
                    <div className="mt-3 text-xs text-blue-400">
                      {r.source === "vector" &&
                        "🔵 Vector Match"}

                      {(r as any).source_type === "graph" &&
                        "🟢 Graph Match"}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Graph */}
          <div className="rounded-2xl border border-white/10 bg-zinc-900/80 p-4 shadow-lg shadow-black/20">
            <KnowledgeGraph query={query} />
          </div>
        </div>

        {/* Empty state */}
        {!loading &&
          results.length === 0 &&
          query.trim() !== "" && (
            <div className="mt-6 rounded-2xl border border-dashed border-white/10 bg-white/5 p-6 text-center text-zinc-400">
              No results found. Try different keywords.
            </div>
          )}
      </div>
    </div>
  );
}