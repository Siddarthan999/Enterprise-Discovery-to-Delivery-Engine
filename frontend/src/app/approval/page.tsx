"use client";

import { useEffect, useState } from "react";
import { Trash2, FileX, Layers } from "lucide-react";
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

  const [sows, setSows] = useState<any[]>([]);
  const [selectedSowId, setSelectedSowId] = useState<number | null>(null);

  const [selectedSow, setSelectedSow] = useState<any>(null);
  const [comments, setComments] = useState<any[]>([]);

  const [versions, setVersions] = useState<any[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);

  const [loadingList, setLoadingList] = useState(true);
  const [loadingDocument, setLoadingDocument] = useState(false);

  async function loadSows() {
    setLoadingList(true);

    try {
      const data = await getApprovalSows();

      setSows(data);

      if (data.length > 0 && selectedSowId == null) {
        setSelectedSowId(data[0].id);
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
    if (selectedSowId != null) {
      loadSelectedSow(selectedSowId);
    }
  }, [selectedSowId]);

  async function handleVersionChange(version: number) {
    if (!selectedSowId) return;

    const data = await getVersion(selectedSowId, version);

    setSelectedVersion(version);

    setSelectedSow({
      ...selectedSow,
      version: data,
    });
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

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_45%),_linear-gradient(135deg,_#050816_0%,_#0b1120_45%,_#020617_100%)] text-white">
      <AppNav />

      <div className="mx-auto max-w-7xl px-6 py-6">

        {/* Header */}
        <div className="mb-5 flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/5 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-[#c90c61]/10 p-2 text-[#c90c61]">
              <Layers size={20} />
            </div>
            <div>
              <h1 className="text-xl font-semibold">Approval Workflow</h1>
              <p className="mt-0.5 text-sm text-zinc-400">
                Review generated SOWs, leave comments and progress approvals.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs text-zinc-500">Viewing as</label>
            <select
              value={viewerRole}
              onChange={(e) => setViewerRole(e.target.value)}
              className="rounded-lg border border-white/10 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-cyan-500/50"
            >
              {ROLES.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-6">

          {/* Left */}
          <div className="col-span-4">
            <SowList
              loading={loadingList}
              sows={sows}
              selectedId={selectedSowId}
              onSelect={setSelectedSowId}
            />
          </div>

          {/* Right */}
          <div className="col-span-8 space-y-4">
            {selectedSow && (
              <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3">
                <div>
                  <p className="text-sm font-medium">Version History</p>
                  <p className="text-xs text-zinc-500">
                    Browse previous revisions of this SOW
                  </p>
                </div>

                <div className="flex items-center gap-2">
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
                      className="inline-flex items-center justify-center rounded-lg border border-white/10 p-2 text-zinc-400 transition hover:border-red-500/50 hover:bg-red-500/10 hover:text-red-400"
                    >
                      <Trash2 size={15} />
                    </button>
                  )}

                  <button
                    onClick={handleDeleteSow}
                    title="Delete entire SOW"
                    className="inline-flex items-center justify-center rounded-lg border border-white/10 p-2 text-zinc-400 transition hover:border-red-600/60 hover:bg-red-600/10 hover:text-red-500"
                  >
                    <FileX size={15} />
                  </button>
                </div>
              </div>
            )}

            <SowApprovalViewer
              loading={loadingDocument}
              viewerRole={viewerRole}
              sow={selectedSow}
              comments={comments}
              refresh={refreshCurrent}
            />
          </div>
        </div>
      </div>
    </div>
  );
}