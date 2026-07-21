"use client";

import { User } from "lucide-react";

type Props = {
  loading: boolean;
  sows: any[];
  selectedId: number | null;
  onSelect: (id: number) => void;
};

function statusDot(status: string) {
  switch (status) {
    case "Approved":
      return "bg-emerald-400";
    case "Pending":
      return "bg-amber-400";
    default:
      return "bg-zinc-500";
  }
}

export default function SowList({
  loading,
  sows,
  selectedId,
  onSelect,
}: Props) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-white/10 bg-zinc-900/70 px-5 py-4 text-sm text-zinc-500">
        Loading SOWs...
      </div>
    );
  }

  if (sows.length === 0) {
    return (
      <div className="rounded-2xl border border-white/10 bg-zinc-900/70 px-5 py-4 text-sm text-zinc-500">
        No generated SOWs found.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-3">
      <div className="dark-scrollbar flex items-center gap-2 overflow-x-auto pb-1">
        {sows.map((sow) => {
          const selected = sow.id === selectedId;

          return (
            <button
              key={sow.id}
              onClick={() => onSelect(sow.id)}
              className={`flex w-[220px] shrink-0 flex-col gap-1.5 rounded-xl border px-3.5 py-2.5 text-left transition ${
                selected
                  ? "border-cyan-500/40 bg-cyan-500/10"
                  : "border-white/5 bg-white/[0.02] hover:border-white/15 hover:bg-white/5"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <h3 className="min-w-0 truncate text-sm font-medium text-white">
                  {sow.title}
                </h3>
                <span
                  className={`h-1.5 w-1.5 shrink-0 rounded-full ${statusDot(
                    sow.status
                  )}`}
                  title={sow.status}
                />
              </div>

             <div className="flex items-center text-[11px] text-zinc-500">
                <span className="flex min-w-0 flex-1 items-center gap-1 truncate">
                  <User size={10} className="shrink-0" />
                  <span className="truncate">{sow.author ?? "Unknown"}</span>
                </span>

                <div className="ml-2 flex items-center gap-2 shrink-0">
                  <span>v{sow.current_version}</span>

                  <span className="rounded bg-cyan-500/10 px-1.5 py-0.5 text-[10px] text-cyan-300">
                    {sow.current_stage}
                  </span>
                </div>
            </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}