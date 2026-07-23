"use client";

import { Users, BadgeCheck, MessagesSquare, ArrowUpRight } from "lucide-react";

type Props = {
  data: any;
};

function interestColor(level: string = "") {
  switch (level.toLowerCase()) {
    case "high":
      return "border-rose-500/20 bg-rose-500/10 text-rose-300";
    case "medium":
      return "border-amber-500/20 bg-amber-500/10 text-amber-300";
    default:
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
  }
}

function influenceColor(level: string = "") {
  switch (level.toLowerCase()) {
    case "high":
      return "border-cyan-500/20 bg-cyan-500/10 text-cyan-300";
    case "medium":
      return "border-violet-500/20 bg-violet-500/10 text-violet-300";
    default:
      return "border-zinc-700 bg-zinc-800 text-zinc-300";
  }
}

function StatCard({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: any;
  label: string;
  value: string | number;
  tone: string;
}) {
  return (
    <div className="rounded-3xl border border-white/8 bg-white/[0.03] p-4">
      <div className="flex items-center gap-3">
        <div className={`rounded-xl border border-white/8 p-2 ${tone}`}>
          <Icon size={18} />
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">{label}</p>
          <p className="mt-1 text-lg font-semibold text-white">{value}</p>
        </div>
      </div>
    </div>
  );
}

export default function StakeholderMatrixViewer({ data }: Props) {
  const stakeholders = data?.stakeholders ?? [];
  const highInfluence = stakeholders.filter((s: any) => s.influence?.toLowerCase() === "high").length;
  const highInterest = stakeholders.filter((s: any) => s.interest?.toLowerCase() === "high").length;

  return (
    <div className="space-y-6">
      <div className="grid gap-3 md:grid-cols-3">
        <StatCard icon={Users} label="Stakeholders" value={stakeholders.length} tone="bg-cyan-500/10 text-cyan-300" />
        <StatCard icon={ArrowUpRight} label="High influence" value={highInfluence} tone="bg-violet-500/10 text-violet-300" />
        <StatCard icon={BadgeCheck} label="High interest" value={highInterest} tone="bg-emerald-500/10 text-emerald-300" />
      </div>

      {stakeholders.length > 0 ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {stakeholders.map((stakeholder: any, index: number) => (
            <div
              key={index}
              className="overflow-hidden rounded-3xl border border-white/8 bg-white/[0.03] transition hover:border-cyan-500/20 hover:bg-white/[0.045]"
            >
              <div className="border-b border-white/8 p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="truncate text-lg font-semibold text-cyan-300">
                      {stakeholder.name}
                    </h3>
                    <p className="mt-1 text-sm text-zinc-400">
                      {stakeholder.role || "Stakeholder"}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-2.5 text-cyan-300">
                    <Users size={18} />
                  </div>
                </div>
              </div>

              <div className="space-y-4 p-5">
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <p className="mb-2 text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                      Interest
                    </p>
                    <span className={`inline-flex rounded-full border px-3 py-1.5 text-xs font-medium ${interestColor(stakeholder.interest)}`}>
                      {stakeholder.interest || "-"}
                    </span>
                  </div>

                  <div>
                    <p className="mb-2 text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                      Influence
                    </p>
                    <span className={`inline-flex rounded-full border px-3 py-1.5 text-xs font-medium ${influenceColor(stakeholder.influence)}`}>
                      {stakeholder.influence || "-"}
                    </span>
                  </div>
                </div>

                <div className="rounded-2xl border border-white/8 bg-black/10 p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <MessagesSquare size={15} className="text-cyan-400" />
                    <span className="text-sm font-medium text-white">Communication</span>
                  </div>
                  <p className="text-sm leading-6 text-zinc-400">
                    {stakeholder.communication || "Not defined"}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-3xl border border-dashed border-white/10 bg-white/[0.02] py-20 text-center text-zinc-500">
          No stakeholders available.
        </div>
      )}
    </div>
  );
}