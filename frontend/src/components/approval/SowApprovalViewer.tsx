"use client";

import { Clock3, FileText, User, MessageSquarePlus, Pencil, Save, X, Check, Loader2, GitCompare, Download, FileType, FileCode, ChevronDown } from "lucide-react";
import { addApprovalComment, approveSow, updateSowVersion, updateSowTitle, getTemplates, exportSow } from "@/lib/api";
import CommentsPanel from "./CommentsPanel";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useState, useEffect, useRef } from "react";

type Props = {
  loading: boolean;
  viewerRole: string;
  sow: any;
  comments: any[];
  refresh: () => Promise<void>;
  compareData: any;
  compareFrom?: number | null;
  compareTo?: number | null;
  onClearCompare?: () => void;
};

const EXPORT_FORMATS = [
  { id: "md", label: "Markdown", icon: FileCode },
  { id: "docx", label: "DOCX", icon: FileType },
  { id: "pdf", label: "PDF", icon: FileText },
];

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

export default function SowApprovalViewer({loading, viewerRole, sow, comments, refresh, compareData, compareFrom, compareTo, onClearCompare}: Props) {
  const document = sow?.document;
  const version = sow?.version;

  const [editing, setEditing] = useState(false);
  const [editingTitle,setEditingTitle]=useState(false);
  const [title,setTitle]=useState("");
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

  const compareContainerRef = useRef<HTMLDivElement | null>(null);
  const diffScopeRef = useRef<HTMLDivElement | null>(null);

  // --- Export state ---
  const [templates, setTemplates] = useState<any[]>([]);
  const [exportTemplateId, setExportTemplateId] = useState<string>("");
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMarkdown(version?.markdown ?? "");
  }, [version]);

  useEffect(() => {
    setTitle(document?.title ?? "");
  }, [document]);

  useEffect(() => {
    async function loadTemplates() {
      try {
        const data = await getTemplates();
        setTemplates(data);

        // Default to the template used during SOW generation (matched by name)
        if (data.length > 0 && document?.template_reference) {
          const matchedTemplate = data.find(
            (t: any) => t.name === document.template_reference
          );
          setExportTemplateId(matchedTemplate?.id || data[0].id);
        } else if (data.length > 0) {
          setExportTemplateId(data[0].id);
        }
      } catch {
        // Template list is optional for export
      }
    }
    loadTemplates();
  }, [document?.template_reference]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        exportMenuRef.current &&
        !exportMenuRef.current.contains(e.target as Node)
      ) {
        setExportMenuOpen(false);
      }
    }
    window.document.addEventListener("mousedown", handleClickOutside);
    return () =>
      window.document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!compareData) return;

    const timer = setTimeout(() => {
      compareContainerRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });

      const scope = diffScopeRef.current;
      if (!scope) return;

      const firstChange = scope.querySelector<HTMLElement>(
        ".diff_add, .diff_chg, .diff_sub"
      );

      if (firstChange) {
        setTimeout(() => {
          firstChange.scrollIntoView({
            behavior: "smooth",
            block: "center",
          });

          firstChange.classList.add("diff-jump-highlight");
          setTimeout(() => {
            firstChange.classList.remove("diff-jump-highlight");
          }, 2200);
        }, 350);
      }
    }, 50);

    return () => clearTimeout(timer);
  }, [compareData]);

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

 async function handleExport(format: string) {
    setExporting(true);

    try {
      const res = await exportSow(
        markdown,
        format,
        exportTemplateId || undefined,
        null,
        null
      );
      const blob = res.data;
      const url = window.URL.createObjectURL(blob);

      const a = window.document.createElement("a");
      a.href = url;
      a.download = `${document.title || "sow"}-v${version.version}.${format}`;
      a.click();

      window.URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
      setExportMenuOpen(false);
    }
  }

  return (
    <div className="space-y-4">

      {/* COMPARE RESULT — full width, only appears when active, sits
          above the document/comments row so it never pushes comments
          out of reach */}
      {compareData && (
        <div
          ref={compareContainerRef}
          className="overflow-hidden rounded-2xl border border-cyan-500/20 bg-zinc-900/70"
        >
          <div className="flex items-center justify-between border-b border-cyan-500/20 bg-cyan-500/5 px-5 py-3.5">
            <div className="flex items-center gap-2 text-sm">
              <GitCompare size={16} className="text-cyan-400" />
              <span className="font-medium text-white">Comparing</span>
              <span className="rounded bg-white/5 px-2 py-0.5 text-xs text-zinc-300">
                v{compareFrom}
              </span>
              <span className="text-zinc-600">→</span>
              <span className="rounded bg-white/5 px-2 py-0.5 text-xs text-zinc-300">
                v{compareTo}
              </span>
            </div>

            {onClearCompare && (
              <button
                onClick={onClearCompare}
                title="Close comparison"
                className="rounded-md p-1.5 text-zinc-500 transition hover:bg-white/5 hover:text-white"
              >
                <X size={16} />
              </button>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-4 border-b border-white/10 px-5 py-2.5 text-xs text-zinc-500">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-emerald-500/70" />
              Added
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-amber-400/70" />
              Changed
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-rose-500/70" />
              Removed
            </span>
          </div>

          <div
            ref={diffScopeRef}
            className="dark-scrollbar sow-diff-scope max-h-[420px] overflow-auto"
          >
            <div
              dangerouslySetInnerHTML={{
                __html: compareData.diff,
              }}
            />
          </div>
        </div>
      )}

      {/* DOCUMENT + COMMENTS — two-column, both height-matched to the
          viewport with independent scroll. Comments are ALWAYS visible
          beside the document, never below a long scroll chain. */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_340px] xl:items-start">

        {/* Document column */}
        <div className="flex max-h-[calc(100vh-160px)] flex-col overflow-hidden rounded-2xl border border-white/10 bg-zinc-900/70">
          <div className="shrink-0 border-b border-white/10 p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <FileText size={17} className="shrink-0 text-zinc-400" />
                  <div className="flex min-w-0 items-center gap-2">
                    {editingTitle ? (
                      <>
                        <input
                          value={title}
                          onChange={(e)=>setTitle(e.target.value)}
                          className="rounded border border-white/10 bg-zinc-950 px-2 py-1 text-sm"
                        />
                        <button onClick={async()=>{await updateSowTitle({sow_id:document.id,title});setEditingTitle(false);await refresh();}}>
                          <Save size={16}/>
                        </button>
                        <button onClick={()=>{setTitle(document.title);setEditingTitle(false);}}>
                          <X size={16}/>
                        </button>
                      </>
                    ) : (
                      <>
                        <h2 className="truncate text-lg font-semibold">{document.title}</h2>
                        <button onClick={()=>setEditingTitle(true)} className="shrink-0 text-zinc-500 hover:text-white">
                          <Pencil size={13}/>
                        </button>
                      </>
                    )}
                  </div>
                </div>
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  <span className="flex items-center gap-1 rounded-lg bg-white/5 px-2 py-1 text-[11px]">
                    <User size={11} />
                    v{document.current_version}
                  </span>
                  <span
                    className={`rounded-lg border px-2 py-1 text-[11px] ${badge(
                      document.status
                    )}`}
                  >
                    {document.status}
                  </span>
                  <span className="rounded-lg bg-cyan-500/10 px-2 py-1 text-[11px] text-cyan-300">
                    {document.current_stage}
                  </span>
                </div>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-[10px] uppercase tracking-wide text-zinc-500">
                  Viewing as
                </p>
                <p className="text-xs font-medium">{viewerRole}</p>
              </div>
            </div>
          </div>

          {/* MARKDOWN — this is the part that scrolls internally */}
          <div className="dark-scrollbar relative flex-1 overflow-y-auto">
              <article className="prose prose-invert prose-sm max-w-none p-6" onMouseUp={handleTextSelection}>
                  {editing ? (
                      <textarea
                          value={markdown}
                          onChange={(e)=>setMarkdown(e.target.value)}
                          className="h-[600px] w-full resize-none rounded-lg border border-white/10 bg-zinc-950 p-4 font-mono text-sm outline-none"
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

          {/* ACTION BAR — pinned at bottom of the document column */}
          <div className="flex shrink-0 items-center justify-between border-t border-white/10 px-4 py-3">
            <div className="flex items-center gap-1.5 text-xs text-zinc-400">
              <Clock3 size={13} />
              <span className="hidden sm:inline">
                {canApprove
                  ? "You are the active reviewer."
                  : document.status === "Approved"
                  ? "Fully approved."
                  : `Waiting for ${document.current_stage}.`}
              </span>
            </div>

            <div className="flex items-center gap-2">

              {/* EXPORT */}
              <div className="relative" ref={exportMenuRef}>
                <button
                  onClick={() => setExportMenuOpen((v) => !v)}
                  title={`Export Version ${version.version}`}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-700 px-2.5 py-1.5 text-xs font-medium transition hover:bg-zinc-600"
                >
                  {exporting ? (
                    <Loader2 size={15} className="animate-spin" />
                  ) : (
                    <Download size={15} />
                  )}
                  <ChevronDown size={11} />
                </button>

                {exportMenuOpen && (
                  <div className="absolute bottom-full right-0 z-50 mb-2 w-64 rounded-xl border border-white/10 bg-zinc-900 p-3 shadow-2xl">
                    <p className="px-1 pb-2 text-[11px] uppercase tracking-wide text-zinc-500">
                      Export Version {version.version}
                    </p>

                    {templates.length > 0 && (
                      <select
                        value={exportTemplateId}
                        onChange={(e) => setExportTemplateId(e.target.value)}
                        className="mb-2 w-full rounded-lg border border-white/10 bg-zinc-950 px-2.5 py-1.5 text-xs text-white outline-none"
                      >
                        {templates.map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.name}
                          </option>
                        ))}
                      </select>
                    )}

                    <div className="flex flex-col gap-1">
                      {EXPORT_FORMATS.map((f) => {
                        const Icon = f.icon;
                        return (
                          <button
                            key={f.id}
                            onClick={() => handleExport(f.id)}
                            disabled={exporting}
                            className="flex items-center gap-2 rounded-lg px-2.5 py-2 text-left text-sm text-zinc-300 transition hover:bg-white/5 disabled:opacity-40"
                          >
                            <Icon size={14} />
                            {f.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {editing ? (
                  <>
                  <button
                      onClick={() => setShowSaveDialog(true)}
                      title="Save changes"
                      className="rounded-lg bg-emerald-600 p-1.5 transition hover:bg-emerald-500"
                  >
                      <Save size={15} />
                  </button>
                  <button
                      onClick={() => {
                      setEditing(false);
                      setMarkdown(version.markdown);
                      }}
                      title="Discard changes"
                      className="rounded-lg bg-zinc-700 p-1.5 transition hover:bg-zinc-600"
                  >
                      <X size={15} />
                  </button>
                  </>
              ) : (
                  <button
                  onClick={() => setEditing(true)}
                  title="Edit document"
                  className="rounded-lg bg-cyan-600 p-1.5 transition hover:bg-cyan-500"
                  >
                  <Pencil size={15} />
                  </button>
              )}

              <button
                  onClick={handleApprove}
                  disabled={!canApprove || approving}
                  title={canApprove ? "Approve this SOW" : "Not your turn to approve"}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-2.5 py-1.5 text-xs font-medium transition hover:bg-emerald-500 disabled:opacity-40"
              >
                  {approving ? (
                    <Loader2 size={13} className="animate-spin" />
                  ) : (
                    <Check size={13} />
                  )}
                  Approve
              </button>
            </div>
          </div>
        </div>

        {/* Comments column — sticky, height-matched to document column,
            scrolls independently. This is the actual fix: comments are
            beside the document, always in view, never below the fold. */}
        <div className="max-h-[calc(100vh-160px)] xl:sticky xl:top-6">
          <CommentsPanel
            sowId={document.id}
            version={document.current_version}
            viewerRole={viewerRole}
            currentStage={document.current_stage}
            comments={comments}
            refresh={refresh}
          />
        </div>
      </div>

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