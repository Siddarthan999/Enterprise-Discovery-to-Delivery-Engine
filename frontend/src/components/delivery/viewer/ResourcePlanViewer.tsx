"use client";

import { Users, CalendarDays, BriefcaseBusiness, Clock3 } from "lucide-react";

type Props = {
  data: any;
};

function allocationColor(allocation: string = "") {
  const value = parseInt(allocation);

  if (value >= 80) return "border-rose-500/20 bg-rose-500/10 text-rose-300";
  if (value >= 50) return "border-amber-500/20 bg-amber-500/10 text-amber-300";
  return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
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

export default function ResourcePlanViewer({ data }: Props) {
  const resources = data?.resources ?? [];
  const roleCount = new Set(resources.map((r: any) => r.role)).size;

  return (
    <div className="space-y-6">
      <div className="grid gap-3 md:grid-cols-3">
        <StatCard icon={Users} label="Resources" value={resources.length} tone="bg-cyan-500/10 text-cyan-300" />
        <StatCard icon={BriefcaseBusiness} label="Roles" value={roleCount} tone="bg-violet-500/10 text-violet-300" />
        <StatCard icon={CalendarDays} label="Active plan" value="Ready" tone="bg-emerald-500/10 text-emerald-300" />
      </div>

      {resources.length > 0 ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {resources.map((resource: any, index: number) => (
            <div
              key={index}
              className="overflow-hidden rounded-3xl border border-white/8 bg-white/[0.03] transition hover:border-cyan-500/20 hover:bg-white/[0.045]"
            >
              <div className="flex items-start justify-between gap-4 border-b border-white/8 p-5">
                <div className="min-w-0">
                  <h3 className="truncate text-lg font-semibold text-cyan-300">
                    {resource.role}
                  </h3>
                  <p className="mt-1 text-sm text-zinc-500">Project resource</p>
                </div>

                <span className={`shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium ${allocationColor(resource.allocation)}`}>
                  {resource.allocation}
                </span>
              </div>

              <div className="space-y-5 p-5">
                <div className="flex items-center gap-3 rounded-2xl border border-white/8 bg-black/10 px-4 py-3 text-sm">
                  <Clock3 size={16} className="text-zinc-400" />
                  <span className="text-zinc-400">Duration</span>
                  <span className="ml-auto font-medium text-white">{resource.duration}</span>
                </div>

                <div>
                  <p className="mb-3 text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                    Responsibilities
                  </p>

                  <div className="space-y-2">
                    {(resource.responsibilities ?? []).map((task: string, i: number) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 rounded-2xl border border-white/8 bg-white/[0.02] px-4 py-3"
                      >
                        <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-cyan-400" />
                        <span className="text-sm leading-6 text-zinc-300">{task}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-3xl border border-dashed border-white/10 bg-white/[0.02] py-20 text-center text-zinc-500">
          No resources available.
        </div>
      )}
    </div>
  );
}