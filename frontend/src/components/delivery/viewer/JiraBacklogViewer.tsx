"use client";

import { useState } from "react";
import {
  ChevronRight,
  ChevronDown,
  FolderKanban,
  Layers3,
  CheckSquare2,
  User,
  Flag,
  Hash,
} from "lucide-react";

type Props = {
  data: any;
};

function PriorityBadge({ priority }: { priority?: string }) {
  const value = (priority || "Medium").toLowerCase();

  const cls =
    value === "high"
      ? "border-rose-500/30 bg-rose-500/10 text-rose-300"
      : value === "low"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
      : "border-amber-500/30 bg-amber-500/10 text-amber-300";

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] ${cls}`}>
      <Flag size={11} />
      {priority || "Medium"}
    </span>
  );
}

function MetaItem({
  icon: Icon,
  children,
}: {
  icon: any;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-2 text-sm text-zinc-400">
      <Icon size={14} className="shrink-0 text-zinc-500" />
      <span className="truncate">{children}</span>
    </div>
  );
}

function StoryCard({ story }: any) {
  const title = story.summary || story.title || story.storyName || "Untitled Story";
  const hasAC = Array.isArray(story.acceptanceCriteria) && story.acceptanceCriteria.length > 0;

  return (
    <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 transition hover:border-white/15 hover:bg-white/[0.045]">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h4 className="truncate text-sm font-medium text-white">{title}</h4>
          {(story.description || hasAC) && (
            <p className="mt-1.5 line-clamp-2 text-sm leading-6 text-zinc-400">
              {story.description || " "}
            </p>
          )}
        </div>

        <PriorityBadge priority={story.priority} />
      </div>

      <div className="mt-4 grid gap-2 md:grid-cols-3">
        <MetaItem icon={User}>
          {story.assignee || story.owner || story.responsibleParty || "Unassigned"}
        </MetaItem>

        <MetaItem icon={Hash}>
          {story.storyPoints ?? story.story_points ?? story.points ?? "-"} SP
        </MetaItem>

        {(story.estimatedDuration || story.duration) && (
          <MetaItem icon={Flag}>
            {story.estimatedDuration || story.duration}
          </MetaItem>
        )}
      </div>

      {hasAC && (
        <div className="mt-4 border-t border-white/8 pt-4">
          <h5 className="mb-3 text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-500">
            Acceptance criteria
          </h5>
          <ul className="space-y-2">
            {story.acceptanceCriteria.map((item: string, i: number) => (
              <li key={i} className="flex gap-2 text-sm leading-6 text-zinc-300">
                <CheckSquare2 size={14} className="mt-1 shrink-0 text-emerald-400" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function FeatureCard({ feature }: any) {
  const [open, setOpen] = useState(true);
  const title = feature.summary || feature.title || feature.featureName || "Untitled Feature";
  const stories = feature.stories || [];

  return (
    <div className="ml-6 rounded-2xl border border-cyan-500/15 bg-cyan-500/[0.04]">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-3 p-4 text-left transition hover:bg-white/[0.02]"
      >
        <span className="rounded-lg border border-cyan-500/15 bg-cyan-500/10 p-1.5 text-cyan-300">
          {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </span>

        <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-300">
          <Layers3 size={16} />
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold text-cyan-200">{title}</h3>
          {feature.description && (
            <p className="mt-1 line-clamp-1 text-sm text-zinc-400">{feature.description}</p>
          )}
        </div>

        <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] text-zinc-300">
          {stories.length} stories
        </span>
      </button>

      {open && (
        <div className="space-y-3 border-t border-cyan-500/10 p-4">
          {stories.map((story: any, i: number) => (
            <StoryCard key={i} story={story} />
          ))}
        </div>
      )}
    </div>
  );
}

function EpicCard({ epic }: any) {
  const [open, setOpen] = useState(true);
  const title = epic.summary || epic.title || epic.epicName || "Untitled Epic";
  const features = epic.features || [];

  return (
    <div className="overflow-hidden rounded-3xl border border-violet-500/15 bg-gradient-to-b from-violet-500/[0.08] to-white/[0.02]">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-4 p-5 text-left transition hover:bg-white/[0.02]"
      >
        <span className="rounded-xl border border-violet-500/15 bg-violet-500/10 p-2 text-violet-300">
          {open ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
        </span>

        <div className="rounded-xl bg-violet-500/10 p-2.5 text-violet-300">
          <FolderKanban size={18} />
        </div>

        <div className="min-w-0 flex-1">
          <h2 className="truncate text-lg font-semibold text-white">{title}</h2>
          {epic.description && (
            <p className="mt-1.5 line-clamp-2 text-sm leading-6 text-zinc-400">
              {epic.description}
            </p>
          )}
        </div>

        <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-zinc-300">
          {features.length} features
        </span>
      </button>

      {open && (
        <div className="space-y-4 border-t border-white/8 p-5">
          {features.map((feature: any, i: number) => (
            <FeatureCard key={i} feature={feature} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function JiraBacklogViewer({ data }: Props) {
  const epics = data?.epics || [];

  if (!epics.length) {
    return (
      <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-10 text-center text-zinc-500">
        No backlog generated yet.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {epics.map((epic: any, index: number) => (
        <EpicCard key={epic.id ?? index} epic={epic} />
      ))}
    </div>
  );
}