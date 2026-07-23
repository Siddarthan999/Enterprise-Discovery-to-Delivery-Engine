"use client";

import { CheckCircle2, Loader2, Sparkles, Wand2, KanbanSquare, ShieldAlert, CalendarRange, Rocket, Users2, Network, ClipboardList, Compass, Link2, CloudUpload, } from "lucide-react";
import JiraIcon from "../icons/JiraIcon";

const ACCENT = "#c90c61";

const DEFINITIONS = [
  {
    id: "jira_backlog",
    title: "Jira Backlog",
    description: "Epics, Features & Stories",
    icon: KanbanSquare,
    color: "#3b82f6",
  },
  {
    id: "raid_register",
    title: "RAID Register",
    description: "Risks, Assumptions, Issues & Dependencies",
    icon: ShieldAlert,
    color: "#f59e0b",
  },
  {
    id: "project_plan",
    title: "Project Plan",
    description: "Implementation phases",
    icon: CalendarRange,
    color: "#22d3ee",
  },
  {
    id: "sprint_plan",
    title: "Sprint Plan",
    description: "Sprint roadmap",
    icon: Rocket,
    color: "#a78bfa",
  },
  {
    id: "resource_plan",
    title: "Resource Plan",
    description: "Resource allocation",
    icon: Users2,
    color: "#34d399",
  },
  {
    id: "stakeholder_matrix",
    title: "Stakeholder Matrix",
    description: "Stakeholders",
    icon: Network,
    color: "#fb7185",
  },
  {
    id: "raci_matrix",
    title: "RACI Matrix",
    description: "Responsibilities",
    icon: ClipboardList,
    color: "#facc15",
  },
  {
    id: "development_order",
    title: "Development Order",
    description: "Execution order",
    icon: Compass,
    color: "#38bdf8",
  },
];

type Props = {
  artifacts: any[];
  selected: string | null;

  onSelect: (artifact: string) => void;

  onGenerate: (artifact: string) => void;
  onGenerateAll: () => void;

  onPublishToJira: (artifact: string) => void;

  generating: string | null;
  generatingAll: boolean;

  publishing: string | null;
};

export default function ArtifactCards({
  artifacts,
  selected,
  onSelect,
  onGenerate,
  onGenerateAll,
  onPublishToJira,
  generating,
  generatingAll,
  publishing,
}: Props) {
  const generatedCount = DEFINITIONS.filter((item) =>
    artifacts.some(
      (a) =>
        a.artifact_type === item.id &&
        a.status === "Generated"
    )
  ).length;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white">
            Delivery Artifacts
          </h2>

          <p className="mt-0.5 text-xs text-zinc-500">
            {generatedCount} of {DEFINITIONS.length} generated
          </p>
        </div>

        <button
            onClick={onGenerateAll}
            disabled={generatingAll}
            title="Generate all artifacts"
            className="group flex items-center gap-2 rounded-lg border border-[#c90c61]/30 bg-[#c90c61]/10 px-3 py-2 text-xs font-medium text-[#c90c61] transition-all hover:border-[#c90c61] hover:bg-[#c90c61]/20 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
            {generatingAll ? (
                <Loader2 size={14} className="animate-spin" />
            ) : (
                <Wand2
                size={14}
                className="transition-transform duration-200 group-hover:rotate-12"
                />
            )}

            {generatingAll ? "Generating" : "Generate All"}
        </button>
      </div>

      <div className="grid gap-3.5 md:grid-cols-2 xl:grid-cols-4">
        {DEFINITIONS.map((item) => {
          const state =
            artifacts.find(
              (a) => a.artifact_type === item.id
            ) ?? {
              status: "Not Generated",
              jira_created: false,
            };

          const active = selected === item.id;
          const generated =
            state.status === "Generated";
          const isGeneratingThis =
            generating === item.id;

          const Icon = item.icon;

          return (
            <div
              key={item.id}
              onClick={() => onSelect(item.id)}
              className="group relative cursor-pointer overflow-hidden rounded-xl border p-4 transition"
              style={{
                borderColor: active
                  ? `${item.color}55`
                  : "rgba(255,255,255,0.08)",
                backgroundColor: active
                  ? `${item.color}0f`
                  : "rgba(255,255,255,0.03)",
              }}
            >
              <div
                className="absolute inset-x-0 top-0 h-0.5 opacity-70"
                style={{
                  backgroundColor: item.color,
                }}
              />

              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <div
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
                    style={{
                      backgroundColor: `${item.color}1a`,
                      color: item.color,
                    }}
                  >
                    <Icon size={16} />
                  </div>

                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold text-white">
                      {item.title}
                    </h3>

                    <p className="mt-0.5 text-xs leading-snug text-zinc-400">
                      {item.description}
                    </p>
                  </div>
                </div>

                {generated && (
                  <CheckCircle2
                    size={16}
                    className="shrink-0 text-emerald-400"
                  />
                )}
              </div>

              <div className="mt-4 flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[11px] ${
                      generated
                        ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                        : "border-white/10 bg-white/5 text-zinc-500"
                    }`}
                  >
                    {state.status}
                  </span>

                  {state.jira_created && (
                    <span className="flex items-center gap-1 rounded-full bg-blue-500/10 px-2 py-0.5 text-[11px] text-blue-300">
                      <Link2 size={10} />
                      Jira
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1">
                 <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onGenerate(item.id);
                    }}
                    disabled={isGeneratingThis}
                    title={generated ? "Regenerate" : "Generate"}
                    className="rounded-lg border border-[#c90c61]/30 bg-[#c90c61]/10 p-1.5 text-[#c90c61] transition-all hover:border-[#c90c61] hover:bg-[#c90c61]/20 hover:text-white disabled:opacity-50"
                    >
                    {isGeneratingThis ? (
                        <Loader2
                        size={15}
                        className="animate-spin"
                        />
                    ) : (
                        <Sparkles size={15} />
                    )}
                </button>

                  {item.id === "jira_backlog" &&
                    generated &&
                    !state.jira_created && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onPublishToJira(item.id);
                        }}
                        disabled={publishing === item.id}
                        title="Publish to Jira"
                        className="rounded-lg border border-[#2684FF]/30 bg-[#2684FF]/5 p-1.5 text-[#2684FF] transition-all duration-200 hover:border-[#2684FF]/60 hover:bg-[#2684FF]/10 hover:shadow-[0_0_10px_rgba(38,132,255,0.25)] disabled:opacity-50"
                      >
                        {publishing === item.id ? (
                          <Loader2
                            size={15}
                            className="animate-spin"
                          />
                        ) : (
                          <JiraIcon size={15} />
                        )}
                      </button>
                    )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}