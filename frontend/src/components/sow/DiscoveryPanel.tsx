"use client";

import { useState } from "react";

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

      // optional: auto generate SOW preview
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

  return (
    <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900">
      
      <h2 className="text-lg font-medium">Discovery Engine</h2>
      <p className="text-xs text-zinc-400 mt-1">
        Extract structured project state from transcript
      </p>

      <button
        onClick={runDiscovery}
        disabled={loading || !transcript}
        className="mt-4 px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-zinc-200 disabled:opacity-50"
      >
        {loading ? "Extracting..." : "Run Discovery"}
      </button>

      {/* State Preview */}
      {state && (
        <pre className="mt-4 text-xs bg-zinc-950 p-3 rounded-lg border border-zinc-800 overflow-auto max-h-64">
          {JSON.stringify(state, null, 2)}
        </pre>
      )}
    </div>
  );
}