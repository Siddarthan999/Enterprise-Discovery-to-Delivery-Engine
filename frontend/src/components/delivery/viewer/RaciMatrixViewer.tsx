"use client";

import { Users, CheckCircle2, ClipboardList } from "lucide-react";

type Props = {
  data: any;
};

const ROLE_HEADERS = [
  { key: "architect", label: "Architect", color: "bg-cyan-500/10 text-cyan-300 border-cyan-500/20" },
  { key: "delivery_manager", label: "Delivery", color: "bg-violet-500/10 text-violet-300 border-violet-500/20" },
  { key: "practice_lead", label: "Practice", color: "bg-amber-500/10 text-amber-300 border-amber-500/20" },
  { key: "client", label: "Client", color: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20" },
  { key: "qa", label: "QA", color: "bg-pink-500/10 text-pink-300 border-pink-500/20" },
];

function roleMark(value: string) {
  switch (value) {
    case "R":
      return "border-cyan-500/20 bg-cyan-500/10 text-cyan-300";
    case "A":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
    case "C":
      return "border-amber-500/20 bg-amber-500/10 text-amber-300";
    case "I":
      return "border-zinc-700 bg-zinc-800 text-zinc-300";
    default:
      return "border-white/8 bg-white/[0.03] text-zinc-500";
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

export default function RaciMatrixViewer({ data }: Props) {
  const activities = data?.activities ?? [];

  const legend = [
    ["R", "Responsible"],
    ["A", "Accountable"],
    ["C", "Consulted"],
    ["I", "Informed"],
  ] as const;

  return (
    <div className="space-y-6">
      <div className="grid gap-3 md:grid-cols-3">
        <StatCard icon={ClipboardList} label="Activities" value={activities.length} tone="bg-cyan-500/10 text-cyan-300" />
        <StatCard icon={Users} label="Roles" value={ROLE_HEADERS.length} tone="bg-violet-500/10 text-violet-300" />
        <StatCard icon={CheckCircle2} label="Matrix" value="Ready" tone="bg-emerald-500/10 text-emerald-300" />
      </div>

      <div className="rounded-3xl border border-white/8 bg-white/[0.03] p-5 md:p-6">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-white">Responsibility legend</h3>
          <p className="mt-1 text-xs text-zinc-500">
            RACI assignments used across the matrix
          </p>
        </div>

        <div className="flex flex-wrap gap-2.5">
          {legend.map(([code, label]) => (
            <div
              key={code}
              className="flex items-center gap-2 rounded-full border border-white/8 bg-white/[0.03] px-3 py-2"
            >
              <span
                className={`flex h-7 w-7 items-center justify-center rounded-full border text-[11px] font-semibold ${roleMark(code)}`}
              >
                {code}
              </span>
              <span className="text-sm text-zinc-300">{label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="overflow-hidden rounded-3xl border border-white/8 bg-white/[0.03]">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead className="border-b border-white/8 bg-white/[0.02]">
              <tr>
                <th className="px-5 py-4 text-left text-xs font-medium uppercase tracking-[0.18em] text-zinc-500">
                  Activity
                </th>
                {ROLE_HEADERS.map((role) => (
                  <th key={role.key} className="px-3 py-4 text-center">
                    <span
                      className={`inline-flex rounded-full border px-3 py-1.5 text-xs font-medium ${role.color}`}
                    >
                      {role.label}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {activities.map((activity: any, index: number) => (
                <tr
                  key={index}
                  className="border-b border-white/5 transition last:border-b-0 hover:bg-white/[0.02]"
                >
                  <td className="px-5 py-4 align-top">
                    <div className="text-sm font-medium text-white">
                      {activity.activity}
                    </div>
                  </td>

                  {ROLE_HEADERS.map((role) => {
                    const value = activity[role.key];
                    return (
                      <td key={role.key} className="px-3 py-4 text-center align-top">
                        <span
                          className={`inline-flex h-9 w-9 items-center justify-center rounded-full border text-sm font-semibold ${roleMark(
                            value
                          )}`}
                          title={value || "-"}
                        >
                          {value || "-"}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}