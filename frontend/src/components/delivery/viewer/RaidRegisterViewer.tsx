"use client";

import { AlertTriangle, HelpCircle, Bug, Link2 } from "lucide-react";

type Props = {
  data: any;
};

function Section({
  title,
  icon,
  tone,
  items,
  emptyLabel,
}: {
  title: string;
  icon: React.ReactNode;
  tone: string;
  items: any[];
  emptyLabel: string;
}) {
  const impactTone = (impact?: string) => {
    switch ((impact || "").toLowerCase()) {
      case "high":
        return "border-rose-500/20 bg-rose-500/10 text-rose-300";
      case "medium":
        return "border-amber-500/20 bg-amber-500/10 text-amber-300";
      case "low":
        return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
      default:
        return "border-white/8 bg-white/[0.03] text-zinc-500";
    }
  };

  return (
    <div className="overflow-hidden rounded-3xl border border-white/8 bg-white/[0.03]">
      <div className="flex items-center gap-3 border-b border-white/8 px-5 py-4">
        <div className={`rounded-xl border border-white/8 p-2 ${tone}`}>{icon}</div>

        <div>
          <h2 className="text-sm font-semibold text-white">{title}</h2>
          <p className="mt-0.5 text-xs text-zinc-500">
            {items.length} item{items.length === 1 ? "" : "s"}
          </p>
        </div>

        <span className="ml-auto rounded-full border border-white/8 bg-white/[0.03] px-2.5 py-1 text-[11px] text-zinc-300">
          {items.length}
        </span>
      </div>

      {items.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead className="bg-white/[0.02]">
              <tr className="text-left text-xs uppercase tracking-[0.18em] text-zinc-500">
                <th className="px-5 py-3">ID</th>
                <th className="px-5 py-3">Description</th>
                <th className="px-5 py-3">Owner</th>
                <th className="px-5 py-3">Impact</th>
              </tr>
            </thead>

            <tbody>
              {items.map((item: any) => (
                <tr key={item.id} className="border-t border-white/5 transition hover:bg-white/[0.02]">
                  <td className="px-5 py-4 align-top">
                    <span className="font-medium text-white">{item.id}</span>
                  </td>

                  <td className="px-5 py-4 align-top text-sm leading-6 text-zinc-300">
                    {item.description}
                  </td>

                  <td className="px-5 py-4 align-top text-sm text-zinc-400">
                    {item.owner || "-"}
                  </td>

                  <td className="px-5 py-4 align-top">
                    <span
                      className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-medium ${impactTone(
                        item.impact
                      )}`}
                    >
                      {item.impact || "-"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="px-5 py-10 text-center text-sm text-zinc-500">
          {emptyLabel}
        </div>
      )}
    </div>
  );
}

export default function RaidRegisterViewer({ data }: Props) {
  const raid = data.raidRegister ?? data;

  return (
    <div className="space-y-5">
      <Section
        title="Risks"
        icon={<AlertTriangle size={16} />}
        tone="bg-rose-500/10 text-rose-300"
        items={raid.risks ?? []}
        emptyLabel="No risks recorded."
      />

      <Section
        title="Assumptions"
        icon={<HelpCircle size={16} />}
        tone="bg-cyan-500/10 text-cyan-300"
        items={raid.assumptions ?? []}
        emptyLabel="No assumptions recorded."
      />

      <Section
        title="Issues"
        icon={<Bug size={16} />}
        tone="bg-amber-500/10 text-amber-300"
        items={raid.issues ?? []}
        emptyLabel="No issues recorded."
      />

      <Section
        title="Dependencies"
        icon={<Link2 size={16} />}
        tone="bg-violet-500/10 text-violet-300"
        items={raid.dependencies ?? []}
        emptyLabel="No dependencies recorded."
      />
    </div>
  );
}