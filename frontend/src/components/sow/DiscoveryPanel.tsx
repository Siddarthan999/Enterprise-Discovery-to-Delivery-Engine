"use client";

import { useState, forwardRef, useImperativeHandle, } from "react";
import { Sparkles, Loader2, ChevronDown, ListTree } from "lucide-react";

type DocMode = "sow" | "proposal";

const DiscoveryPanel = forwardRef(function DiscoveryPanel({
  mode,
  transcript,
  authorId,
  templateId,
  state,
  setState,
  setSow,
  setReview,
  setConfidence,
  setHistoricalSowsUsed,
  setHistoricalRisksConsidered,
  setStructuredProposal,
}: {
  mode: DocMode;
  transcript: string;
  authorId?: number | "";
  templateId?: string;
  state: any;
  setState: (v: any) => void;
  setSow: (v: string) => void;
  setReview: (value: any) => void;
  setConfidence: (value: any) => void;
  setHistoricalSowsUsed: (value: any[]) => void;
  setHistoricalRisksConsidered: (value: any[]) => void;
  setStructuredProposal: (value: any) => void;
}, ref) {
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  async function runDiscovery() {
    if (!transcript) return;
    setLoading(true);

    try {
      setSow("");
      setReview(null);
      setConfidence(null);
      setHistoricalSowsUsed([]);
      setHistoricalRisksConsidered([]);
      setStructuredProposal(null);

      const extractUrl =
        mode === "proposal"
          ? "http://localhost:8000/api/proposal/extract"
          : "http://localhost:8000/api/discovery/extract";

      const res = await fetch(extractUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: mode === "proposal" ? "Proposal Discovery Session" : "Discovery Session",
          transcript,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.error || "Discovery request failed");
      }

      setState(data.state);
      setShowDetails(false);

      if (!data.state || data.state.error) {
        setSow("");
        return;
      }

      if (mode === "proposal") {
        // Proposal mode never calls the AI reviewer agents — no review/
        // confidence/historical-grounding calls happen here at all.
        const proposalRes = await fetch("http://localhost:8000/api/proposal/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            state: data.state,
            author_id: authorId || undefined,
          }),
        });

        const proposalData = await proposalRes.json();

        if (!proposalRes.ok) {
          throw new Error(proposalData?.error || "Proposal generation failed");
        }

        if (proposalData.error) {
          throw new Error(proposalData.error);
        }

        setSow(proposalData.sow || "");
        setStructuredProposal(proposalData.structured_proposal ?? null);
        setReview(null);
        setConfidence(null);
        setHistoricalSowsUsed([]);
        setHistoricalRisksConsidered([]);
        return;
      }

      const sowRes = await fetch("http://localhost:8000/api/sow/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state: data.state,
          template_id: templateId || undefined,
          author_id: authorId || undefined,
        }),
      });

      const sowData = await sowRes.json();

      if (!sowRes.ok) {
        throw new Error(sowData?.error || "SOW generation failed");
      }

      if (sowData.error) {
        throw new Error(sowData.error);
      }

      setSow(sowData.sow || "");
      setReview(sowData.review ?? null);
      setConfidence(sowData.confidence ?? null);
      setHistoricalSowsUsed(sowData.historical_sows_used ?? []);
      setHistoricalRisksConsidered(
        sowData.historical_risks_considered ?? []
      );
    } catch (err: any) {
      console.error("Discovery failed:", err);

      setSow("");
      setReview(null);
      setConfidence(null);
      setHistoricalSowsUsed([]);
      setHistoricalRisksConsidered([]);
      setStructuredProposal(null);

      setState((prev: any) => ({
        ...(prev || {}),
        frontend_error:
          err?.message || "Discovery or generation failed",
      }));
    } finally {
      setLoading(false);
    }
  }

  useImperativeHandle(ref, () => ({
    runDiscovery,
  }));

  const fieldCount = state
    ? Object.keys(state).filter(
        (key) => key !== "error" && key !== "frontend_error" && key !== "raw_response"
      ).length
    : 0;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      <div className="flex items-center gap-2">
        <div className="rounded-lg bg-[#c90c61]/10 p-1.5 text-[#c90c61]">
          <Sparkles size={16} />
        </div>
        <div>
          <h2 className="text-lg font-medium">Discovery Engine</h2>
          <p className="text-xs text-zinc-400">
            {mode === "proposal"
              ? "Extract structured proposal fields from client context"
              : "Extract structured project state from client context"}
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

      {state?.error && (
        <div className="mt-3 rounded-lg border border-red-900/50 bg-red-950/30 px-3 py-2 text-xs text-red-300">
          Discovery extraction failed: {state.error}
        </div>
      )}

      {state?.frontend_error && (
        <div className="mt-3 rounded-lg border border-amber-900/50 bg-amber-950/30 px-3 py-2 text-xs text-amber-300">
          {state.frontend_error}
        </div>
      )}

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
            <pre className="dark-scrollbar max-h-64 overflow-auto border-t border-zinc-800 p-4 text-xs text-zinc-300">
              {JSON.stringify(state, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
});

export default DiscoveryPanel;