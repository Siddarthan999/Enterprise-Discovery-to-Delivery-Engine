"use client";

import { useEffect, useState } from "react";
import { ClipboardCheck, Trash2, FileX, Check, GitCompare, ArrowRight, X } from "lucide-react";
import AppNav from "@/components/layout/AppNav";

import SowList from "@/components/approval/SowList";
import SowApprovalViewer from "@/components/approval/SowApprovalViewer";

import {
  getApprovalSows,
  getApprovalSow,
  getApprovalComments,
  getVersions,
  getVersion,
  deleteSow,
  deleteVersion,
  compareVersions,
  getAuthors,
} from "@/lib/api";

const ROLES = [
  "Architect",
  "Practice Lead",
  "Legal",
  "CFO",
  "Client",
];

export default function ApprovalPage() {
  const [viewerRole, setViewerRole] = useState("Architect");

  const [authors, setAuthors] = useState<any[]>([]);
  const [selectedAuthor, setSelectedAuthor] = useState<string>("all");

  const [sows, setSows] = useState<any[]>([]);
  const [selectedSowId, setSelectedSowId] = useState<number | null>(null);

  const [selectedSow, setSelectedSow] = useState<any>(null);
  const [comments, setComments] = useState<any[]>([]);

  const [versions, setVersions] = useState<any[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);

  const [compareOpen, setCompareOpen] = useState(false);
  const [compareFrom, setCompareFrom] = useState<number | null>(null);
  const [compareTo, setCompareTo] = useState<number | null>(null);
  const [compareData, setCompareData] = useState<{ left: any; right: any } | null>(null);

  const [loadingList, setLoadingList] = useState(true);
  const [loadingDocument, setLoadingDocument] = useState(false);

  function normalizeAuthor(value: string | null | undefined) {
    return (value ?? "").trim().toLowerCase();
  }

  function matchesAuthorFilter(authorName: string | null | undefined) {
    if (selectedAuthor === "all") return true;
    return normalizeAuthor(authorName) === normalizeAuthor(selectedAuthor);
  }

  async function loadSows() {
    setLoadingList(true);

    try {
      const data = await getApprovalSows();

      setSows(data);

      const filteredAfterLoad = data.filter((sow: any) => matchesAuthorFilter(sow.author));

      if (filteredAfterLoad.length > 0 && selectedSowId == null) {
        setSelectedSowId(filteredAfterLoad[0].id);
      }

      if (filteredAfterLoad.length === 0) {
        setSelectedSowId(null);
      }
    } finally {
      setLoadingList(false);
    }
  }

  async function loadSelectedSow(id: number) {
    setLoadingDocument(true);

    try {
      const sow = await getApprovalSow(id);
      const comments = await getApprovalComments(id);
      const versionList = await getVersions(id);

      setSelectedSow(sow);
      setComments(comments);

      setVersions(versionList);

      if (sow?.document?.current_version) {
        setSelectedVersion(sow.document.current_version);
      }
    } finally {
      setLoadingDocument(false);
    }
  }

  useEffect(() => {
    loadSows();
  }, []);

  useEffect(() => {
    async function loadAuthors() {
      try {
        const data = await getAuthors();
        setAuthors(data);
      } catch (err) {
        console.error("Failed to load authors", err);
      }
    }

    loadAuthors();
  }, []);

  useEffect(() => {
    if (selectedSowId != null) {
      loadSelectedSow(selectedSowId);
      setCompareOpen(false);
      setCompareFrom(null);
      setCompareTo(null);
      setCompareData(null);
    }
  }, [selectedSowId]);

  useEffect(() => {
    const filtered = sows.filter((sow) => matchesAuthorFilter(sow.author));

    if (filtered.length === 0) {
      if (selectedSowId !== null) {
        setSelectedSowId(null);
      }
      setSelectedSow(null);
      setComments([]);
      setVersions([]);
      setSelectedVersion(null);
      return;
    }

    if (!filtered.some((sow) => sow.id === selectedSowId)) {
      setSelectedSowId(filtered[0].id);
    }
  }, [selectedAuthor, sows]);

  async function handleVersionChange(version: number) {
    if (!selectedSowId) return;

    const data = await getVersion(selectedSowId, version);

    setSelectedVersion(version);

    setSelectedSow({
      ...selectedSow,
      version: data,
    });
  }

  async function handleCompareVersions() {
    if (
      !selectedSowId ||
      compareFrom == null ||
      compareTo == null
    )
      return;

    const data = await compareVersions(
      selectedSowId,
      compareFrom,
      compareTo
    );

    setCompareData(data);
  }

  function clearCompare() {
    setCompareData(null);
    setCompareFrom(null);
    setCompareTo(null);
    setCompareOpen(false);
  }

  async function handleDeleteSow() {
    if (!selectedSowId) return;

    if (!confirm("Delete this entire SOW and all versions?")) return;

    await deleteSow(selectedSowId);

    setSelectedSow(null);
    setComments([]);
    setVersions([]);
    setSelectedVersion(null);
    setSelectedSowId(null);

    await loadSows();
  }

  async function handleDeleteVersion() {
    if (!selectedSowId || !selectedVersion) return;

    if (
      !confirm(
        `Delete Version ${selectedVersion}? This cannot be undone.`
      )
    )
      return;

    await deleteVersion(selectedSowId, selectedVersion);

    await refreshCurrent();
  }

  async function refreshCurrent() {
    if (selectedSowId == null) return;

    await loadSelectedSow(selectedSowId);
    await loadSows();
  }

  const currentStage: string | undefined = selectedSow?.document?.current_stage;
  const documentStatus: string | undefined = selectedSow?.document?.status;
  const currentStageIndex = currentStage ? ROLES.indexOf(currentStage) : -1;
  const isFullyApproved = documentStatus === "Approved";

  const canRunCompare = compareFrom != null && compareTo != null && compareFrom !== compareTo;

  const filteredSows = sows.filter((sow) => matchesAuthorFilter(sow.author));
  const hasAnySows = sows.length > 0;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_45%),_linear-gradient(135deg,_#050816_0%,_#0b1120_45%,_#020617_100%)] text-white">
      <AppNav />

      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-2xl shadow-cyan-950/20">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-[#c90c61]/10 p-2 text-[#c90c61]">
                <ClipboardCheck size={20} />
              </div>
              <div>
                <h1 className="text-2xl font-semibold text-white">
                  Approval Workflow
                </h1>
                <p className="mt-0.5 text-sm text-zinc-400">
                  Review generated SOWs, leave comments and progress approvals.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-3">
              <div className="flex items-center gap-2">
                <label className="text-xs text-zinc-500">Viewing as</label>
                <select
                  value={viewerRole}
                  onChange={(e) => setViewerRole(e.target.value)}
                  className="rounded-lg border border-white/10 bg-zinc-900 px-3 py-1.5 text-sm outline-none focus:border-cyan-500/50"
                >
                  {ROLES.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </div>

              {hasAnySows && (
                <div className="flex items-center gap-2">
                  <label className="text-xs text-zinc-500">Filter by author</label>
                  <select
                    value={selectedAuthor}
                    onChange={(e) => setSelectedAuthor(e.target.value)}
                    className="rounded-lg border border-white/10 bg-zinc-900 px-3 py-1.5 text-sm outline-none focus:border-cyan-500/50"
                  >
                    <option value="all">All authors</option>
                    {authors.map((author) => (
                      <option key={author.id} value={author.name}>
                        {author.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>

          {/* Stage pipeline */}
          {selectedSow && (
            <div className="mt-4 flex items-center gap-1 overflow-x-auto pb-1">
              {ROLES.map((role, i) => {
                const isDone = isFullyApproved || i < currentStageIndex;
                const isActive = !isFullyApproved && i === currentStageIndex;

                return (
                  <div key={role} className="flex flex-1 items-center gap-1">
                    <div className="flex flex-1 flex-col items-center gap-1 min-w-[72px]">
                      <div
                        className={`flex h-6 w-6 items-center justify-center rounded-full border text-[10px] font-medium transition ${
                          isDone
                            ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-400"
                            : isActive
                            ? "border-[#c90c61]/50 bg-[#c90c61]/15 text-[#c90c61] ring-2 ring-[#c90c61]/20"
                            : "border-white/10 bg-zinc-900 text-zinc-600"
                        }`}
                      >
                        {isDone ? <Check size={12} /> : i + 1}
                      </div>
                      <span
                        className={`whitespace-nowrap text-[11px] ${
                          isActive
                            ? "font-medium text-white"
                            : isDone
                            ? "text-zinc-400"
                            : "text-zinc-600"
                        }`}
                      >
                        {role}
                      </span>
                    </div>

                    {i < ROLES.length - 1 && (
                      <div
                        className={`mb-3.5 h-px flex-1 ${
                          isDone ? "bg-emerald-500/40" : "bg-white/10"
                        }`}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* SOW selector — horizontal strip instead of a tall left column,
            frees full width below for the document + comments layout */}
        <div className="mt-4">
          <SowList
            loading={loadingList}
            sows={filteredSows}
            selectedId={selectedSowId}
            activeAuthor={selectedAuthor === "all" ? null : selectedAuthor}
            onSelect={setSelectedSowId}
          />
        </div>

        {/* Version bar */}
        {selectedSow && (
          <div className="mt-4 rounded-xl border border-white/10 bg-white/5">
            <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
              <div>
                <p className="text-sm font-medium">Version History</p>
                <p className="text-xs text-zinc-500">
                  Browse previous revisions of this SOW
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCompareOpen((v) => !v)}
                  title="Compare versions"
                  className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-2 text-xs transition ${
                    compareOpen || compareData
                      ? "border-cyan-500/40 bg-cyan-500/10 text-cyan-300"
                      : "border-white/10 text-zinc-400 hover:border-cyan-500/30 hover:bg-cyan-500/5 hover:text-cyan-300"
                  }`}
                >
                  <GitCompare size={15} />
                  Compare
                </button>

                <select
                  value={selectedVersion ?? ""}
                  onChange={(e) =>
                    handleVersionChange(Number(e.target.value))
                  }
                  className="rounded-lg border border-white/10 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-cyan-500/50"
                >
                  {versions.map((v) => (
                    <option key={v.version} value={v.version}>
                      Version {v.version}
                    </option>
                  ))}
                </select>

                {selectedVersion !== selectedSow.document.current_version && (
                  <button
                    onClick={handleDeleteVersion}
                    title={`Delete Version ${selectedVersion}`}
                    className="group flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-2 text-zinc-400 transition hover:border-amber-500/40 hover:bg-amber-500/10 hover:text-amber-400"
                  >
                    <Trash2 size={15} />
                    <span className="text-xs">Version</span>
                  </button>
                )}

                <button
                  onClick={handleDeleteSow}
                  title="Delete entire SOW and all versions"
                  className="group flex items-center gap-1.5 rounded-lg border border-red-900/40 bg-red-950/20 px-2.5 py-2 text-red-400 transition hover:border-red-500/60 hover:bg-red-500/15 hover:text-red-300"
                >
                  <FileX size={15} />
                  <span className="text-xs font-medium">Delete SOW</span>
                </button>
              </div>
            </div>

            {compareOpen && (
              <div className="flex flex-wrap items-center gap-2 border-t border-white/10 px-4 py-3">
                <select
                  value={compareFrom ?? ""}
                  onChange={(e) => setCompareFrom(Number(e.target.value))}
                  className="rounded-lg border border-white/10 bg-zinc-900 px-3 py-1.5 text-sm outline-none focus:border-cyan-500/50"
                >
                  <option value="">From version</option>
                  {versions.map((v) => (
                    <option key={v.version} value={v.version}>
                      v{v.version}
                    </option>
                  ))}
                </select>

                <ArrowRight size={14} className="text-zinc-600" />

                <select
                  value={compareTo ?? ""}
                  onChange={(e) => setCompareTo(Number(e.target.value))}
                  className="rounded-lg border border-white/10 bg-zinc-900 px-3 py-1.5 text-sm outline-none focus:border-cyan-500/50"
                >
                  <option value="">To version</option>
                  {versions.map((v) => (
                    <option key={v.version} value={v.version}>
                      v{v.version}
                    </option>
                  ))}
                </select>

                <button
                  onClick={handleCompareVersions}
                  disabled={!canRunCompare}
                  className="ml-1 rounded-lg bg-cyan-600 px-3 py-1.5 text-sm font-medium transition hover:bg-cyan-500 disabled:opacity-40"
                >
                  View diff
                </button>

                {compareData && (
                  <button
                    onClick={clearCompare}
                    title="Clear comparison"
                    className="ml-auto flex items-center gap-1 text-xs text-zinc-500 transition hover:text-zinc-300"
                  >
                    <X size={13} />
                    Clear
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Document + Comments — full width now, internal two-column split */}
        <div className="mt-4">
          <SowApprovalViewer
            loading={loadingDocument}
            viewerRole={viewerRole}
            sow={selectedSow}
            comments={comments}
            refresh={refreshCurrent}
            compareData={compareData}
            compareFrom={compareFrom}
            compareTo={compareTo}
            onClearCompare={clearCompare}
          />
        </div>
      </div>
    </div>
  );
}
