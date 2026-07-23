"use client";

import { useState } from "react";
import {
  ArrowDown,
  ArrowRight,
  CheckCircle2,
  Layers3,
  Rocket,
  Flag,
  Lightbulb,
} from "lucide-react";

type Props = {
  data: any;
};

function stepIcon(index: number) {
  switch (index) {
    case 0:
      return <Lightbulb size={18} />;
    case 1:
      return <Layers3 size={18} />;
    case 2:
      return <Rocket size={18} />;
    default:
      return <Flag size={18} />;
  }
}

const STEP_COLORS = [
  "bg-cyan-500/15 text-cyan-300 border-cyan-500/20",
  "bg-violet-500/15 text-violet-300 border-violet-500/20",
  "bg-emerald-500/15 text-emerald-300 border-emerald-500/20",
  "bg-amber-500/15 text-amber-300 border-amber-500/20",
  "bg-pink-500/15 text-pink-300 border-pink-500/20",
  "bg-blue-500/15 text-blue-300 border-blue-500/20",
];

function StatCard({
  icon: Icon,
  label,
  value,
  tone = "text-white",
}: {
  icon: any;
  label: string;
  value: string | number;
  tone?: string;
}) {
  return (
    <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
      <div className="flex items-center gap-3">
        <div className="rounded-xl border border-white/8 bg-white/[0.04] p-2 text-zinc-300">
          <Icon size={18} />
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            {label}
          </p>
          <p className={`mt-1 text-lg font-semibold ${tone}`}>{value}</p>
        </div>
      </div>
    </div>
  );
}

function StepCard({ step, index, total }: { step: any; index: number; total: number }) {
  const tone = STEP_COLORS[index % STEP_COLORS.length];

  return (
    <div className="relative">
      <div className="flex gap-4">
        <div className="flex flex-col items-center">
          <div className={`flex h-12 w-12 items-center justify-center rounded-full border ${tone}`}>
            {stepIcon(index)}
          </div>

          <div className="mt-2 text-[11px] font-medium text-zinc-500">
            #{step.order ?? index + 1}
          </div>

          {index !== total - 1 && (
            <div className="mt-3 h-full min-h-16 w-px bg-white/8" />
          )}
        </div>

        <div className="min-w-0 flex-1 rounded-2xl border border-white/8 bg-white/[0.03] p-5 transition hover:border-white/14 hover:bg-white/[0.045]">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <h3 className="truncate text-base font-semibold text-white">
                {step.title}
              </h3>
              {step.reason && (
                <p className="mt-2 text-sm leading-7 text-zinc-400">
                  {step.reason}
                </p>
              )}
            </div>

            <span className="shrink-0 rounded-full border border-cyan-500/15 bg-cyan-500/10 px-3 py-1 text-[11px] text-cyan-300">
              Step {step.order ?? index + 1}
            </span>
          </div>
        </div>
      </div>

      {index !== total - 1 && (
        <div className="ml-[23px] flex justify-center py-2 text-zinc-600">
          <ArrowDown size={18} />
        </div>
      )}
    </div>
  );
}

export default function DevelopmentOrderViewer({ data }: Props) {
  const steps = data?.steps ?? [];

  return (
    <div className="space-y-6">
      <div className="grid gap-3 md:grid-cols-3">
        <StatCard icon={Layers3} label="Total steps" value={steps.length} tone="text-white" />
        <StatCard icon={Rocket} label="Execution flow" value="Sequential" tone="text-violet-300" />
        <StatCard icon={CheckCircle2} label="Status" value="Ready" tone="text-emerald-300" />
      </div>

      {steps.length > 0 ? (
        <div className="rounded-3xl border border-white/8 bg-white/[0.02] p-6 md:p-8">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-white">Development order</h2>
              <p className="mt-1 text-xs text-zinc-500">
                Recommended sequence for delivery and implementation
              </p>
            </div>
          </div>

          <div className="space-y-2">
            {steps.map((step: any, index: number) => (
              <StepCard key={step.order ?? index} step={step} index={index} total={steps.length} />
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-3xl border border-dashed border-white/10 bg-white/[0.02] py-20 text-center text-zinc-500">
          No development order available.
        </div>
      )}
    </div>
  );
}