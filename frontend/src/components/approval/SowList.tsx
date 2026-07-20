"use client";

import { User } from "lucide-react";

type Props = {
  loading: boolean;
  sows: any[];
  selectedId: number | null;
  onSelect: (id: number) => void;
};

function statusColor(status: string) {
  switch (status) {
    case "Approved":
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    case "Pending":
      return "bg-amber-500/10 text-amber-400 border-amber-500/30";
    default:
      return "bg-zinc-700/20 text-zinc-400 border-zinc-700";
  }
}

export default function SowList({
  loading,
  sows,
  selectedId,
  onSelect,
}: Props) {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-zinc-900/70">
      <div className="border-b border-white/10 px-5 py-3.5">
        <h2 className="text-sm font-semibold text-white">Generated SOWs</h2>
        <p className="mt-0.5 text-xs text-zinc-500">
          Select a document to review
        </p>
      </div>

      {loading ? (
        <div className="p-6 text-sm text-zinc-500">Loading...</div>
      ) : sows.length === 0 ? (
        <div className="p-6 text-sm text-zinc-500">
          No generated SOWs found.
        </div>
      ) : (
        <div className="max-h-[calc(100vh-260px)] divide-y divide-white/5 overflow-y-auto">
          {sows.map((sow) => {
            const selected = sow.id === selectedId;

            return (
              <button
                key={sow.id}
                onClick={() => onSelect(sow.id)}
                className={`w-full px-5 py-3.5 text-left transition ${
                  selected ? "bg-cyan-500/10" : "hover:bg-white/5"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-medium text-white">
                      {sow.title}
                    </h3>

                    <p className="mt-1 flex items-center gap-1 text-xs text-zinc-500">
                      <User size={11} />
                      {sow.author ?? "Unknown"}
                      <span className="text-zinc-700">·</span>
                      v{sow.current_version}
                    </p>
                  </div>

                  <span
                    className={`shrink-0 rounded-full border px-2 py-0.5 text-[11px] ${statusColor(
                      sow.status
                    )}`}
                  >
                    {sow.status}
                  </span>
                </div>

                <div className="mt-2.5 flex items-center justify-between">
                  <span className="text-xs text-zinc-500">Current Stage</span>
                  <span className="rounded bg-white/5 px-2 py-0.5 text-xs text-cyan-300">
                    {sow.current_stage}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}