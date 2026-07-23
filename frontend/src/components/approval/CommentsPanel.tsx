"use client";

import { useState } from "react";
import { MessageSquare, Send, Trash2, Bot, Square, CheckSquare, Loader2, } from "lucide-react";

import {
  addApprovalComment,
  deleteComment,
  requestChanges,
} from "@/lib/api";

type Props = {
  sowId: number;
  version: number;
  viewerRole: string;
  currentStage: string;
  comments: any[];
  refresh: () => Promise<void>;
};

export default function CommentsPanel({
  sowId,
  version,
  viewerRole,
  currentStage,
  comments,
  refresh,
}: Props) {
  const [section, setSection] = useState("");
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);

  const [selected, setSelected] = useState<number[]>([]);
  const [runningAI, setRunningAI] = useState(false);

  const canComment = viewerRole === currentStage;

  async function submit() {
    if (!section.trim() || !comment.trim()) return;

    setSaving(true);

    try {
      await addApprovalComment({
        sow_id: sowId,
        version,
        reviewer_role: viewerRole,
        section,
        comment,
      });

      setSection("");
      setComment("");

      await refresh();
    } finally {
      setSaving(false);
    }
  }

  function toggle(id: number) {
    if (selected.includes(id)) {
      setSelected(selected.filter((x) => x !== id));
    } else {
      setSelected([...selected, id]);
    }
  }

  async function runAI() {
    if (selected.length === 0) return;

    setRunningAI(true);

    try {
      await requestChanges({
        sow_id: sowId,
        reviewer_role: viewerRole,
        comment_ids: selected,
      });

      setSelected([]);

      await refresh();

      alert("New AI revision created.");
    } catch (err: any) {
      alert(err?.response?.data?.error || "Failed");
    } finally {
      setRunningAI(false);
    }
  }

  async function removeComment(id: number) {
    if (!confirm("Delete this comment?")) return;

    try {
      await deleteComment(id, viewerRole);

      setSelected((prev) => prev.filter((x) => x !== id));

      await refresh();
    } catch (err: any) {
      alert(err?.response?.data?.error || "Unable to delete comment");
    }
  }

  return (
    <div className="flex h-full flex-col rounded-2xl border border-white/10 bg-zinc-900/70">

      {/* Header — pinned, never scrolls away */}
      <div className="flex shrink-0 items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-2">
          <MessageSquare size={16} className="text-zinc-400" />
          <h2 className="text-sm font-semibold">Comments</h2>
          {comments.length > 0 && (
            <span className="rounded-full bg-white/5 px-1.5 py-0.5 text-[11px] text-zinc-500">
              {comments.length}
            </span>
          )}
        </div>

        {selected.length > 0 && (
          <button
            onClick={runAI}
            disabled={runningAI}
            title={`Generate AI revision from ${selected.length} selected comment(s)`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-fuchsia-600 px-2.5 py-1.5 text-[11px] font-medium transition hover:bg-fuchsia-500 disabled:opacity-40"
          >
            {runningAI ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Bot size={12} />
            )}
            {runningAI ? "Optimizing" : `AI (${selected.length})`}
          </button>
        )}
      </div>

      {/* Comments — the ONLY part that scrolls internally, fills all
          remaining vertical space in the panel */}
      <div className="dark-scrollbar max-h-[420px] overflow-y-auto">
        {comments.length === 0 ? (
          <div className="px-4 py-6 text-center text-sm text-zinc-500">
            No comments yet.
          </div>
        ) : (
          comments.map((c) => (
            <div key={c.id} className="border-b border-white/5 px-4 py-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="rounded bg-cyan-500/10 px-1.5 py-0.5 text-[10px] text-cyan-300">
                      {c.section || "General"}
                    </span>
                    {c.status === "Closed" && (
                      <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] text-emerald-400">
                        Optimized
                      </span>
                    )}
                  </div>

                  {c.selected_text && (
                    <div className="mt-2 rounded-lg border border-yellow-500/20 bg-yellow-500/5 px-2.5 py-1.5 text-xs italic text-yellow-200">
                      "{c.selected_text}"
                    </div>
                  )}

                  <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-200">
                    {c.comment}
                  </p>

                  <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[11px] text-zinc-500">
                    <span>{c.reviewer_role}</span>
                    <span>{new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-0.5">
                  {c.status === "Open" && (
                    <button
                      onClick={() => toggle(c.id)}
                      title={selected.includes(c.id) ? "Deselect" : "Select for AI revision"}
                      className="rounded-md p-1 text-zinc-400 transition hover:bg-white/5 hover:text-white"
                    >
                      {selected.includes(c.id) ? (
                        <CheckSquare size={14} />
                      ) : (
                        <Square size={14} />
                      )}
                    </button>
                  )}
                  <button
                    disabled={c.reviewer_role !== viewerRole}
                    onClick={() => removeComment(c.id)}
                    title="Delete comment"
                    className="rounded-md p-1 text-red-400 transition hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-25"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add Comment — pinned at bottom, always visible without scrolling */}
      <div className="shrink-0 space-y-2 border-t border-white/10 p-3">
        <input
          disabled={!canComment}
          value={section}
          onChange={(e) => setSection(e.target.value)}
          placeholder="Section (optional)"
          className="w-full rounded-lg border border-white/10 bg-zinc-950 px-2.5 py-1.5 text-xs outline-none focus:border-cyan-500 disabled:opacity-50"
        />

        <textarea
          disabled={!canComment}
          rows={2}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder={
            canComment
              ? "Leave a review comment..."
              : `Waiting for ${currentStage}`
          }
          className="w-full resize-none rounded-lg border border-white/10 bg-zinc-950 px-2.5 py-1.5 text-xs outline-none focus:border-cyan-500 disabled:opacity-50"
        />

        <div className="flex justify-end">
          <button
            disabled={saving || !canComment || !comment.trim()}
            onClick={submit}
            title="Add comment"
            className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-600 px-3 py-1.5 text-xs font-medium transition hover:bg-cyan-500 disabled:opacity-40"
          >
            {saving ? (
              <Loader2 size={13} className="animate-spin" />
            ) : (
              <Send size={13} />
            )}
            {saving ? "Saving" : "Post"}
          </button>
        </div>
      </div>
    </div>
  );
}