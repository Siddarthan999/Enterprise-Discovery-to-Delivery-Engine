"use client";

import { CalendarDays, User } from "lucide-react";

type Props = {
  data: any;
};

function StatPill({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-full border border-white/8 bg-white/[0.03] px-3 py-1.5 text-xs text-zinc-300">
      <span className="text-zinc-500">{label}:</span>{" "}
      <span className="text-white">{value}</span>
    </div>
  );
}

function StoryCard({ story }: any) {
  return (
    <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 transition hover:border-white/14 hover:bg-white/[0.045]">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-semibold text-white">
            {story.storyName || "Untitled Story"}
          </h3>
          {story.description && (
            <p className="mt-1.5 line-clamp-2 text-sm leading-6 text-zinc-400">
              {story.description}
            </p>
          )}
        </div>

        <span className="shrink-0 rounded-full border border-emerald-500/15 bg-emerald-500/10 px-2.5 py-1 text-[11px] text-emerald-300">
          Story
        </span>
      </div>

      <div className="mt-4 grid gap-2 md:grid-cols-2">
        <div className="flex items-center gap-2 rounded-xl border border-white/8 bg-black/10 px-3 py-2 text-sm">
          <User size={14} className="text-cyan-400" />
          <span className="text-zinc-500">Responsible</span>
          <span className="ml-auto truncate text-white">
            {story.responsibleParty || "Unassigned"}
          </span>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-white/8 bg-black/10 px-3 py-2 text-sm">
          <CalendarDays size={14} className="text-amber-400" />
          <span className="text-zinc-500">Duration</span>
          <span className="ml-auto truncate text-white">
            {story.estimatedDuration || "-"}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function SprintPlanViewer({ data }: Props) {
  const sprints = data?.sprints ?? [];

  if (!sprints.length) {
    return (
      <div className="rounded-3xl border border-dashed border-white/10 bg-white/[0.03] p-12 text-center text-zinc-500">
        No sprint plan available.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {sprints.map((sprint: any, index: number) => (
        <div
          key={index}
          className="overflow-hidden rounded-3xl border border-white/8 bg-white/[0.03]"
        >
          <div className="border-b border-white/8 bg-cyan-500/[0.06] p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0">
                <h2 className="truncate text-lg font-semibold text-cyan-300">
                  {sprint.name}
                </h2>
                {sprint.goal && (
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-400">
                    {sprint.goal}
                  </p>
                )}
              </div>

              <StatPill label="Duration" value={sprint.duration || "-"} />
            </div>
          </div>

          <div className="space-y-3 p-5">
            {(sprint.stories ?? []).map((story: any, i: number) => (
              <StoryCard key={i} story={story} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}