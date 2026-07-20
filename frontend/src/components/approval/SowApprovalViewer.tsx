"use client";

import { Clock3, FileText, User, MessageSquarePlus, Pencil, Save, X, Check, Loader2 } from "lucide-react";
import { addApprovalComment, approveSow, updateSowVersion } from "@/lib/api";
import CommentsPanel from "./CommentsPanel";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState, useEffect } from "react";

type Props = {
  loading: boolean;
  viewerRole: string;
  sow: any;
  comments: any[];
  refresh: () => Promise<void>;
};

function badge(status: string) {
  switch (status) {
    case "Approved":
      return "bg-emerald-500/10 border-emerald-500/30 text-emerald-400";

    case "Pending":
      return "bg-amber-500/10 border-amber-500/30 text-amber-400";

    default:
      return "bg-zinc-700/20 border-zinc-700 text-zinc-400";
  }
}

export default function SowApprovalViewer({loading, viewerRole, sow, comments, refresh,}: Props) {
  const document = sow?.document;
  const version = sow?.version;

  const [editing, setEditing] = useState(false);
  const [markdown, setMarkdown] = useState(version?.markdown ?? "");

  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveMode, setSaveMode] = useState<"current" | "new">("new");
  const [saving, setSaving] = useState(false);

  const [selection, setSelection] = useState("");
  const [selectionRange, setSelectionRange] = useState<{start: number; end: number;} | null>(null);

  const [popup, setPopup] = useState({visible: false, x: 0, y: 0,});

  const [showCommentDialog, setShowCommentDialog] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [postingComment, setPostingComment] = useState(false);

  const [approving, setApproving] = useState(false);

  useEffect(() => {
    setMarkdown(version?.markdown ?? "");
  }, [version]);

  if (loading) {
    return (
      <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-8">
        <p className="text-zinc-500">Loading...</p>
      </div>
    );
  }

  if (!sow || !document || !version) {
    return (
      <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-8">
        <p className="text-zinc-500">
          Select a SOW from the left panel.
        </p>
      </div>
    );
  }

  const canApprove =
    viewerRole === document.current_stage &&
    document.status !== "Approved";

  async function handleApprove() {
    setApproving(true);
    try {
      await approveSow({
        sow_id: document.id,
        reviewer_role: viewerRole,
      });

      await refresh();
    } finally {
      setApproving(false);
    }
  }

    function handleTextSelection() {
        const sel = window.getSelection();

        if (!sel || sel.toString().trim() === "") {
            setPopup({
            visible: false,
            x: 0,
            y: 0,
            });
            return;
        }

        const range = sel.getRangeAt(0);

        const rect = range.getBoundingClientRect();

        setSelection(sel.toString());

        setSelectionRange({
            start: sel.anchorOffset,
            end: sel.focusOffset,
        });

        setPopup({
            visible: true,
            x: rect.right + 8,
            y: rect.bottom + 8,
        });
  }

  async function handleSaveHighlightedComment() {
    setPostingComment(true);
    try {
      await addApprovalComment({
          sow_id: document.id,
          version: document.current_version,
          reviewer_role: viewerRole,
          section: selection,
          comment: commentText,
          selected_text: selection,
          start_offset: selectionRange?.start,
          end_offset: selectionRange?.end,
      });

      setShowCommentDialog(false);
      setCommentText("");

      setPopup({
          visible: false,
          x: 0,
          y: 0,
      });

      await refresh();
    } finally {
      setPostingComment(false);
    }
 }

  return (
    <div className="space-y-5">

      {/* HEADER */}
      <div className="rounded-2xl border border-white/10 bg-zinc-900/70">
        <div className="border-b border-white/10 p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <FileText size={18} className="shrink-0 text-zinc-400" />
                <h2 className="truncate text-lg font-semibold">
                  {document.title}
                </h2>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="flex items-center gap-1.5 rounded-lg bg-white/5 px-2.5 py-1.5 text-xs">
                  <User size={13} />
                  Version {document.current_version}
                </span>
                <span
                  className={`rounded-lg border px-2.5 py-1.5 text-xs ${badge(
                    document.status
                  )}`}
                >
                  {document.status}
                </span>
                <span className="rounded-lg bg-cyan-500/10 px-2.5 py-1.5 text-xs text-cyan-300">
                  {document.current_stage}
                </span>
              </div>
            </div>
            <div className="shrink-0 text-right">
              <p className="text-[11px] uppercase tracking-wide text-zinc-500">
                Viewing as
              </p>
              <p className="mt-0.5 text-sm font-medium">{viewerRole}</p>
            </div>
          </div>
        </div>

        {/* MARKDOWN */}
        <div className="relative max-h-[700px] overflow-y-auto border-b border-white/10">
            <article className="prose prose-invert max-w-none p-8" onMouseUp={handleTextSelection}>
                {editing ? (
                    <textarea
                        value={markdown}
                        onChange={(e)=>setMarkdown(e.target.value)}
                        className="h-[650px] w-full resize-none rounded-lg border border-white/10 bg-zinc-950 p-5 font-mono text-sm outline-none"
                    />
                    ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {markdown}
                    </ReactMarkdown>
                )}
            </article>

            {popup.visible && (
                <button
                onClick={() => {
                    setShowCommentDialog(true);
                }}
                title="Add comment on selection"
                className="fixed z-50 rounded-full bg-[#c90c61] p-3 shadow-xl transition hover:scale-105"
                style={{
                    left: popup.x,
                    top: popup.y,
                }}
                >
                <MessageSquarePlus size={18} />
                </button>
            )}
        </div>

        {/* ACTION BAR */}
        <div className="flex items-center justify-between px-5 py-3.5">
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <Clock3 size={15} />
            {canApprove
              ? "You are the active reviewer."
              : document.status === "Approved"
              ? "This SOW has been fully approved."
              : `Waiting for ${document.current_stage} review.`}
          </div>
          <div className="flex items-center gap-2">
            {editing ? (
                <>
                <button
                    onClick={() => setShowSaveDialog(true)}
                    title="Save changes"
                    className="rounded-lg bg-emerald-600 p-2 transition hover:bg-emerald-500"
                >
                    <Save size={17} />
                </button>
                <button
                    onClick={() => {
                    setEditing(false);
                    setMarkdown(version.markdown);
                    }}
                    title="Discard changes"
                    className="rounded-lg bg-zinc-700 p-2 transition hover:bg-zinc-600"
                >
                    <X size={17} />
                </button>
                </>
            ) : (
                <button
                onClick={() => setEditing(true)}
                title="Edit document"
                className="rounded-lg bg-cyan-600 p-2 transition hover:bg-cyan-500"
                >
                <Pencil size={17} />
                </button>
            )}

            <button
                onClick={handleApprove}
                disabled={!canApprove || approving}
                title={canApprove ? "Approve this SOW" : "Not your turn to approve"}
                className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium transition hover:bg-emerald-500 disabled:opacity-40"
            >
                {approving ? (
                  <Loader2 size={15} className="animate-spin" />
                ) : (
                  <Check size={15} />
                )}
                Approve
            </button>
          </div>
        </div>
      </div>

      {/* COMMENTS */}
      <CommentsPanel
        sowId={document.id}
        version={document.current_version}
        viewerRole={viewerRole}
        currentStage={document.current_stage}
        comments={comments}
        refresh={refresh}
      />

      {showCommentDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
            <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-zinc-900 p-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold">Add Comment</h3>
                  <button
                    onClick={() => {
                      setShowCommentDialog(false);
                      setCommentText("");
                    }}
                    title="Close"
                    className="rounded-md p-1 text-zinc-500 transition hover:bg-white/5 hover:text-white"
                  >
                    <X size={16} />
                  </button>
                </div>

                <p className="mt-4 text-xs uppercase tracking-wide text-zinc-500">
                    Selected Text
                </p>
                <div className="mt-2 rounded-lg border border-white/10 bg-zinc-950 p-3 text-sm italic text-zinc-300">
                    "{selection}"
                </div>
                <textarea
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    rows={4}
                    placeholder="Write your review comment..."
                    className="mt-4 w-full rounded-lg border border-white/10 bg-zinc-950 p-3 text-sm outline-none focus:border-cyan-500"
                />
                <div className="mt-5 flex justify-end gap-2">
                    <button
                        onClick={() => {
                            setShowCommentDialog(false);
                            setCommentText("");
                        }}
                        className="rounded-lg border border-white/10 px-3 py-2 text-sm transition hover:bg-white/5"
                        >
                        Cancel
                    </button>
                    <button
                        onClick={handleSaveHighlightedComment}
                        disabled={postingComment || !commentText.trim()}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-[#c90c61] px-3 py-2 text-sm font-medium transition hover:bg-[#a70a4d] disabled:opacity-40"
                        >
                        {postingComment && <Loader2 size={14} className="animate-spin" />}
                        Save Comment
                    </button>
                </div>
            </div>
        </div>
        )}
        {showSaveDialog && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
                <div className="w-full max-w-[420px] rounded-2xl border border-white/10 bg-zinc-900 p-6">
                <h3 className="text-base font-semibold">Save Changes</h3>

                <p className="mt-2 text-sm text-zinc-400">
                    Choose how you'd like to save your edits.
                </p>

                <div className="mt-4 space-y-2.5">
                    <label className="flex items-center gap-3 text-sm">
                    <input
                        type="radio"
                        checked={saveMode === "current"}
                        onChange={() => setSaveMode("current")}
                    />
                    Update Current Version
                    </label>

                    <label className="flex items-center gap-3 text-sm">
                    <input
                        type="radio"
                        checked={saveMode === "new"}
                        onChange={() => setSaveMode("new")}
                    />
                    Create New Version
                    </label>
                </div>

                <div className="mt-5 flex justify-end gap-2">
                    <button
                    onClick={() => setShowSaveDialog(false)}
                    className="rounded-lg border border-white/10 px-3 py-2 text-sm transition hover:bg-white/5"
                    >
                    Cancel
                    </button>

                    <button
                    disabled={saving}
                    onClick={async () => {
                        setSaving(true);
                        try {
                          await updateSowVersion({
                          sow_id: document.id,
                          markdown,
                          mode: saveMode,
                          });

                          setShowSaveDialog(false);
                          setEditing(false);

                          await refresh();
                        } finally {
                          setSaving(false);
                        }
                    }}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-600 px-3 py-2 text-sm font-medium transition hover:bg-cyan-500 disabled:opacity-40"
                    >
                    {saving && <Loader2 size={14} className="animate-spin" />}
                    Save
                    </button>
                </div>
                </div>
            </div>
        )}
    </div>
  );
}