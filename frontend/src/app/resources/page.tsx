"use client";

import { useState, useEffect, useCallback } from "react";
import AppNav from "@/components/layout/AppNav";
import {
  API_BASE,
  getTemplates,
  getDocuments,
  uploadTemplate,
  uploadDocument,
  deleteTemplate,
  deleteDocument,
} from "@/lib/api";

type Template = {
  id: string;
  name: string;
  filename: string;
  sections?: string[];
};

type KnowledgeDoc = {
  id: string;
  title: string;
  type: string;
  source: string;
  uploaded_at: string;
};

type Tab = "knowledge" | "templates";

function formatDate(value: string) {
  const date = new Date(value);
  if (isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function UploadIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 16V4M12 4l-4 4M12 4l4 4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 7h16M9 7V5a1 1 0 011-1h4a1 1 0 011 1v2m2 0v13a1 1 0 01-1 1H8a1 1 0 01-1-1V7h10z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function FileIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M7 3h7l5 5v13a1 1 0 01-1 1H7a1 1 0 01-1-1V4a1 1 0 011-1z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 3v5h5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function ResourcesPage() {
  const [tab, setTab] = useState<"knowledge" | "templates">("knowledge");

  const [templates, setTemplates] = useState<Template[]>([]);
  const [documents, setDocuments] = useState<KnowledgeDoc[]>([]);

  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadTemplates = useCallback(async () => {
    setTemplates(await getTemplates());
  }, []);

  const loadDocuments = useCallback(async () => {
    setDocuments(await getDocuments());
  }, []);

  useEffect(() => {
    loadTemplates();
    loadDocuments();
  }, [loadTemplates, loadDocuments]);

  async function handleUpload() {
    if (!file) return;
    setError(null);
    setUploading(true);

    try {
      const form = new FormData();
      form.append("file", file);

      if (tab === "templates") {
        await uploadTemplate(form);
      } else {
        await uploadDocument(form);
      }

      setFile(null);

      if (tab === "templates") {
        await loadTemplates();
      } else {
        await loadDocuments();
      }
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleDeleteTemplate(id: string) {
    if (!confirm("Delete this template? This can't be undone.")) return;
    setDeletingId(id);
    try {
      await deleteTemplate(id);
      await loadTemplates();
    } finally {
      setDeletingId(null);
    }
  }

  async function handleDeleteDocument(id: string) {
    if (!confirm("Delete this document from the knowledge base? This can't be undone.")) return;
    setDeletingId(id);
    try {
      await deleteDocument(id);
      await loadDocuments();
    } finally {
      setDeletingId(null);
    }
  }

  const isTemplates = tab === "templates";

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_45%),_linear-gradient(135deg,_#050816_0%,_#0b1120_45%,_#020617_100%)] text-white">
      <AppNav />

      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-cyan-950/20">
          <h1 className="text-2xl font-semibold text-white">Resources</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Manage SOW templates and knowledge base documents.
          </p>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[220px_1fr]">
          {/* Sidebar */}
          <div className="flex lg:flex-col gap-2">
            <button
              onClick={() => setTab("knowledge")}
              className={`flex-1 lg:flex-none rounded-xl px-4 py-3 text-left text-sm font-medium transition ${
                !isTemplates
                  ? "bg-[#c90c61] text-white shadow-lg shadow-[#c90c61]/20"
                  : "bg-zinc-900/80 text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
              }`}
            >
              Knowledge Base
              <div className="mt-0.5 text-xs font-normal opacity-70">
                {documents.length} document{documents.length === 1 ? "" : "s"}
              </div>
            </button>
            
            <button
              onClick={() => setTab("templates")}
              className={`flex-1 lg:flex-none rounded-xl px-4 py-3 text-left text-sm font-medium transition ${
                isTemplates
                  ? "bg-[#c90c61] text-white shadow-lg shadow-[#c90c61]/20"
                  : "bg-zinc-900/80 text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
              }`}
            >
              SOW Templates
              <div className="mt-0.5 text-xs font-normal opacity-70">
                {templates.length} file{templates.length === 1 ? "" : "s"}
              </div>
            </button>
          </div>

          {/* Main content */}
          <div className="flex flex-col gap-6">
            {/* Upload card */}
            <div className="rounded-2xl border border-white/10 bg-zinc-900/80 p-6 shadow-lg shadow-black/20">
              <h2 className="text-sm font-semibold text-white">
                {isTemplates ? "Upload a SOW template" : "Add a document to the knowledge base"}
              </h2>
              <p className="mt-1 text-xs text-zinc-400">
                {isTemplates
                  ? "DOCX files used as the base layout/branding for generated SOWs."
                  : "PDF, DOCX, TXT, PPTX, MD, or EML files — parsed and embedded for search and discovery context."}
              </p>

              <div className="mt-4 rounded-2xl border border-dashed border-[#c90c61]/30 bg-zinc-950/70 p-8 text-center">
                <label
                  htmlFor="file-upload"
                  className="mx-auto flex w-fit cursor-pointer flex-col items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-8 py-6 transition hover:border-[#c90c61]/50 hover:bg-white/[0.05]"
                >
                  <div className="rounded-full bg-[#c90c61]/15 p-4 text-[#c90c61]">
                    <UploadIcon />
                  </div>

                  <div>
                    <p className="text-sm font-medium text-white">
                      {file ? file.name : "Choose a file"}
                    </p>

                    <p className="mt-1 text-xs text-zinc-500">
                      Click to browse files
                    </p>
                  </div>
                </label>

                <input
                  id="file-upload"
                  key={tab}
                  type="file"
                  accept={isTemplates ? ".docx" : ".txt,.pdf,.docx,.pptx,.md,.eml"}
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                />

                {file && (
                  <button
                    onClick={handleUpload}
                    disabled={uploading}
                    className="mt-5 rounded-xl bg-[#c90c61] px-5 py-2 text-sm font-medium text-white transition hover:bg-[#a70a4d] disabled:opacity-50"
                  >
                    {uploading ? "Uploading..." : "Upload File"}
                  </button>
                )}

                {error && (
                  <p className="mt-4 text-xs text-red-400">
                    {error}
                  </p>
                )}
              </div>
            </div>

            {/* List */}
            <div className="rounded-2xl border border-white/10 bg-zinc-900/80 shadow-lg shadow-black/20">
              <div className="border-b border-white/10 px-6 py-4">
                <h2 className="text-sm font-semibold text-white">
                  {isTemplates ? "Templates" : "Documents"}
                </h2>
              </div>

              {isTemplates ? (
                templates.length === 0 ? (
                  <p className="px-6 py-8 text-center text-sm text-zinc-500">
                    No templates uploaded yet.
                  </p>
                ) : (
                  <ul className="divide-y divide-white/5">
                    {templates.map((t) => (
                      <li
                        key={t.id}
                        className="flex items-center justify-between gap-4 px-6 py-4"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          {/* <div className="rounded-lg bg-[#c90c61]/10 p-2 text-[#c90c61]"> */}
                          <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400">
                            <FileIcon />
                          </div>
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium text-white">
                              {t.name}
                            </p>
                            <p className="text-xs text-zinc-500">
                              {t.sections?.length || 0} section{t.sections?.length === 1 ? "" : "s"} detected
                            </p>
                          </div>
                        </div>

                        <button
                          onClick={() => handleDeleteTemplate(t.id)}
                          disabled={deletingId === t.id}
                          className="rounded-lg p-2 text-zinc-500 transition hover:bg-red-500/10 hover:text-red-400 disabled:opacity-40"
                          title="Delete template"
                        >
                          <TrashIcon />
                        </button>
                      </li>
                    ))}
                  </ul>
                )
              ) : documents.length === 0 ? (
                <p className="px-6 py-8 text-center text-sm text-zinc-500">
                  No documents in the knowledge base yet.
                </p>
              ) : (
                <ul className="divide-y divide-white/5">
                  {documents.map((d) => (
                    <li
                      key={d.id}
                      className="flex items-center justify-between gap-4 px-6 py-4"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400">
                          <FileIcon />
                        </div>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-white">
                            {d.title}
                          </p>
                          <p className="text-xs text-zinc-500">
                            {d.type} · uploaded {formatDate(d.uploaded_at)}
                          </p>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDeleteDocument(d.id)}
                        disabled={deletingId === d.id}
                        className="rounded-lg p-2 text-zinc-500 transition hover:bg-red-500/10 hover:text-red-400 disabled:opacity-40"
                        title="Delete document"
                      >
                        <TrashIcon />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}