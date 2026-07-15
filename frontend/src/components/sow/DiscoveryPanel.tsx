"use client";

import { useState } from "react";
import { Sparkles, Loader2, ChevronDown, ListTree } from "lucide-react";

export default function DiscoveryPanel({
  transcript,
  state,
  setState,
  setSow,
}: {
  transcript: string;
  state: any;
  setState: (v: any) => void;
  setSow: (v: string) => void;
}) {
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  async function runDiscovery() {
    if (!transcript) return;
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/discovery/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: "Discovery Session",
          transcript,
        }),
      });

      const data = await res.json();
      setState(data.state);
      setShowDetails(false);

      const sowRes = await fetch("http://localhost:8000/api/sow/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: data.state }),
      });

      const sowData = await sowRes.json();
      setSow(sowData.sow);
    } catch (err) {
      console.error("Discovery failed:", err);
    } finally {
      setLoading(false);
    }
  }

  const fieldCount = state ? Object.keys(state).length : 0;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      <div className="flex items-center gap-2">
        <div className="rounded-lg bg-[#c90c61]/10 p-1.5 text-[#c90c61]">
          <Sparkles size={16} />
        </div>
        <div>
          <h2 className="text-lg font-medium">Discovery Engine</h2>
          <p className="text-xs text-zinc-400">
            Extract structured project state from transcript
          </p>
        </div>
      </div>

      <button
        onClick={runDiscovery}
        disabled={loading || !transcript}
        className="mt-4 flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-medium text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading && <Loader2 size={14} className="animate-spin" />}
        {loading ? "Extracting..." : "Run Discovery"}
      </button>

      {!transcript && (
        <p className="mt-3 text-xs text-zinc-600">
          Add a transcript first to enable discovery.
        </p>
      )}

      {/* State summary */}
      {state && (
        <div className="mt-5 rounded-lg border border-zinc-800 bg-zinc-950/60">
          <button
            onClick={() => setShowDetails((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-3"
          >
            <span className="flex items-center gap-2 text-sm text-zinc-300">
              <ListTree size={14} className="text-emerald-400" />
              {fieldCount} field{fieldCount === 1 ? "" : "s"} extracted
            </span>
            <ChevronDown
              size={14}
              className={`text-zinc-500 transition-transform ${showDetails ? "rotate-180" : ""}`}
            />
          </button>

          {showDetails && (
            <pre className="max-h-64 overflow-auto border-t border-zinc-800 p-4 text-xs text-zinc-300">
              {JSON.stringify(state, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}