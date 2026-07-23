"use client";

import { CalendarRange, Package } from "lucide-react";

type Props = {
  data: any;
};

function PhaseNumber({ index }: { index: number }) {
  return (
    <div className="flex h-11 w-11 items-center justify-center rounded-full border border-cyan-500/20 bg-cyan-500/10 text-sm font-semibold text-cyan-300">
      {index + 1}
    </div>
  );
}

export default function ProjectPlanViewer({ data }: Props) {
  const phases = data?.phases ?? [];

  if (!phases.length) {
    return (
      <div className="rounded-3xl border border-dashed border-white/10 bg-white/[0.03] p-12 text-center text-zinc-500">
        No project plan generated.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="rounded-3xl border border-white/8 bg-white/[0.03] p-5 md:p-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-white">Project plan</h2>
            <p className="mt-1 text-xs text-zinc-500">
              Phases arranged in delivery order
            </p>
          </div>

          <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-zinc-300">
            {phases.length} phases
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {phases.map((phase: any, index: number) => {
          const deliverables = phase.deliverables || [];

          return (
            <div key={index} className="flex gap-4">
              <div className="flex flex-col items-center">
                <PhaseNumber index={index} />
                {index !== phases.length - 1 && (
                  <div className="mt-3 h-full min-h-10 w-px bg-white/8" />
                )}
              </div>

              <div className="min-w-0 flex-1 rounded-3xl border border-white/8 bg-white/[0.03] p-5 transition hover:border-white/14 hover:bg-white/[0.045]">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="truncate text-lg font-semibold text-cyan-300">
                      {phase.name}
                    </h3>

                    {phase.duration && (
                      <div className="mt-2 inline-flex items-center gap-2 rounded-full border border-white/8 bg-white/[0.03] px-2.5 py-1 text-sm text-zinc-400">
                        <CalendarRange size={14} />
                        <span>{phase.duration}</span>
                      </div>
                    )}
                  </div>

                  <span className="rounded-full border border-cyan-500/15 bg-cyan-500/10 px-3 py-1.5 text-xs text-cyan-300">
                    {deliverables.length} deliverables
                  </span>
                </div>

                {deliverables.length > 0 && (
                  <div className="mt-5 grid gap-2">
                    {deliverables.map((item: string, i: number) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 rounded-2xl border border-white/8 bg-black/10 px-4 py-3"
                      >
                        <div className="mt-0.5 rounded-lg bg-cyan-500/10 p-1.5 text-cyan-300">
                          <Package size={14} />
                        </div>

                        <div className="min-w-0 flex-1 text-sm leading-6 text-zinc-300">
                          {item}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}