"use client";

import { useState } from "react";
import { FileText, Copy, Check } from "lucide-react";

export default function SowViewer({ sow }: { sow: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (!sow) return;
    await navigator.clipboard.writeText(sow);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  const wordCount = sow ? sow.trim().split(/\s+/).filter(Boolean).length : 0;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-cyan-500/10 p-1.5 text-cyan-400">
            <FileText size={16} />
          </div>
          <h2 className="text-lg font-medium">SOW Preview</h2>
        </div>

        <div className="flex items-center gap-3">
          {sow && (
            <span className="text-xs text-zinc-500">
              {wordCount.toLocaleString()} words
            </span>
          )}

          {sow && (
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 rounded-md border border-zinc-800 px-2.5 py-1.5 text-xs text-zinc-400 transition hover:border-zinc-600 hover:text-zinc-200"
            >
              {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
              {copied ? "Copied" : "Copy"}
            </button>
          )}
        </div>
      </div>

      <div className="mt-4">
        {sow ? (
          <div className="max-h-[32rem] overflow-auto rounded-lg border border-zinc-800 bg-zinc-950 p-5">
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-zinc-200">
              {sow}
            </pre>
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-zinc-800 bg-zinc-950/40 p-8 text-center text-sm text-zinc-500">
            No SOW generated yet. Run discovery first.
          </div>
        )}
      </div>
    </div>
  );
}