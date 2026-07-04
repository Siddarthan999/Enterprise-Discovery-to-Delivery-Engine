"use client";

import { searchDocuments } from "@/lib/api";
import KnowledgeGraph from "@/components/graph/KnowledgeGraph";
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

  return (
    <div className="min-h-screen bg-zinc-950 text-white px-6 py-8">
      {/* Header */}
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold">Enterprise Search</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Hybrid retrieval (Vector + Graph)
        </p>

        {/* Search Bar */}
        <div className="flex gap-2 mt-6">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search documents, SOWs, emails..."
            className="flex-1 px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-800 focus:outline-none focus:border-zinc-600"
          />

          <button
            onClick={handleSearch}
            className="px-5 py-3 rounded-lg bg-white text-black font-medium hover:bg-zinc-200"
          >
            Search
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="mt-6 text-zinc-400">Searching knowledge base...</div>
        )}

        {/* Results */}
        <div className="mt-8 space-y-4">
          {results.map((r) => (
            <div
              key={r.doc_id}
              className="p-4 rounded-xl border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 transition"
            >
              {/* Title */}
              <div className="flex justify-between items-center">
                <h2 className="font-medium text-white">{r.title}</h2>

                <span className="text-xs text-zinc-400">
                  score: {r.score.toFixed(3)}
                </span>
              </div>

              {/* Meta */}
              <div className="text-xs text-zinc-500 mt-1 flex gap-3">
                {r.type && <span>type: {r.type}</span>}
                {r.source && <span>source: {r.source}</span>}
                {r.uploaded_at && <span>{r.uploaded_at}</span>}
              </div>

              {/* Content preview */}
              {r.content && (
                <p className="text-sm text-zinc-300 mt-3 line-clamp-3">
                  {r.content}
                </p>
              )}

              {/* Tags */}
              <div className="mt-3 text-xs text-blue-400">
                {r.source === "vector" && "🔵 Vector Match"}
                {r.source_type === "graph" && "🟢 Graph Match"}
              </div>
            </div>
          ))}
        </div>
        <div>
            <KnowledgeGraph query={query} />
        </div>

        {/* Empty State */}
        {!loading && results.length === 0 && query && (
          <div className="mt-10 text-zinc-500">
            No results found. Try different keywords.
          </div>
        )}
      </div>
    </div>
  );
}