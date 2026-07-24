"use client";

import { useState, useEffect } from "react";
import { FileText, Sparkles, Download, ChevronRight, FilePenLine, Plus, Trash2, Check, X, } from "lucide-react";
import TranscriptPanel from "@/components/sow/TranscriptPanel";
import DiscoveryPanel from "@/components/sow/DiscoveryPanel";
import SowViewer from "@/components/sow/SowViewer";
import ExportPanel from "@/components/sow/ExportPanel";
import AppNav from "@/components/layout/AppNav";
import { getTemplates, getAuthors, addAuthor, deleteAuthor } from "@/lib/api";
import ReviewPanel from "@/components/sow/ReviewPanel";

type Step = {
  label: string;
  icon: React.ReactNode;
  done: boolean;
};

export default function SOWPage() {
  const [transcript, setTranscript] = useState("");
  const [state, setState] = useState<any>(null);
  const [sow, setSow] = useState<string>("");
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");
  const [review, setReview] = useState<any>(null);
  const [confidence, setConfidence] = useState<any>(null);
  const [historicalSowsUsed, setHistoricalSowsUsed] = useState<any[]>([]);
  const [historicalRisksConsidered, setHistoricalRisksConsidered] = useState<any[]>([]);
  const [authors, setAuthors] = useState<any[]>([]);
  const [selectedAuthor, setSelectedAuthor] = useState<number | "">("");
  const [newAuthor, setNewAuthor] = useState("");
  const [showNewAuthor, setShowNewAuthor] = useState(false);

  useEffect(() => {
    async function loadTemplates() {
      const data = await getTemplates();
      setTemplates(data);
      if (data.length > 0) {
        setSelectedTemplate(data[0].id);
      }
    }

    loadTemplates();
    async function loadAuthors() {
      const data = await getAuthors();

      setAuthors(data);

      if (data.length > 0) {
        setSelectedAuthor(data[0].id);
      }
    }

    loadAuthors();
  }, []);

  const steps: Step[] = [
    { label: "Context", icon: <FileText size={14} />, done: !!transcript },
    { label: "Discovery", icon: <Sparkles size={14} />, done: !!state },
    { label: "Export", icon: <Download size={14} />, done: !!sow },
  ];

  async function handleAddAuthor() {
    if (!newAuthor.trim()) return;
    await addAuthor(newAuthor);
    const data = await getAuthors();
    setAuthors(data);
    const added = data.find(
      (a: any) => a.name === newAuthor.trim()
    );
    if (added) {
      setSelectedAuthor(added.id);
    }
    setNewAuthor("");
    setShowNewAuthor(false);
  }

  async function handleDeleteAuthor() {
    if (!selectedAuthor) return;
    if (!confirm("Delete this author?")) return;
    await deleteAuthor(Number(selectedAuthor));
    const data = await getAuthors();
    setAuthors(data);
    if (data.length) {
      setSelectedAuthor(data[0].id);
    } else {
      setSelectedAuthor("");
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_45%),_linear-gradient(135deg,_#050816_0%,_#0b1120_45%,_#020617_100%)] text-white">
      <AppNav />
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-cyan-950/20">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">

            {/* Left side */}
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-[#c90c61]/10 p-2 text-[#c90c61]">
                <FilePenLine size={20} />
              </div>

              <div>
                <h1 className="text-2xl font-semibold text-white">
                  SOW Generator
                </h1>

                <p className="mt-0.5 text-sm text-zinc-400">
                  Discovery → Structured State → Statement of Work
                </p>
              </div>
            </div>

            {/* Step Progress - Right side */}
            <div className="flex flex-wrap items-center gap-1.5">
              {steps.map((step, i) => (
                <div key={step.label} className="flex items-center gap-1.5">
                  <div
                    className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                      step.done
                        ? "border-[#c90c61]/40 bg-[#c90c61]/10 text-[#c90c61]"
                        : "border-white/10 bg-zinc-900/60 text-zinc-500"
                    }`}
                  >
                    {step.icon}
                    {step.label}
                  </div>

                  {i < steps.length - 1 && (
                    <ChevronRight
                      size={14}
                      className="text-zinc-700"
                    />
                  )}
                </div>
              ))}
            </div>

          </div>
        </div>

        {/* Template selector */}
        <div className="mt-4 flex flex-wrap items-center gap-3 rounded-2xl border border-white/10 bg-zinc-900/80 p-4 shadow-lg shadow-black/20">
          <label className="text-sm text-zinc-400">
            Template
          </label>

          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="rounded-lg border border-white/10 bg-zinc-950/70 px-3 py-2 text-sm text-white"
          >
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>

          <label className="ml-6 text-sm text-zinc-400">
            Author
          </label>

          <div className="flex items-center gap-2">
            <select
              value={selectedAuthor}
              onChange={(e) => setSelectedAuthor(Number(e.target.value))}
              className="rounded-lg border border-white/10 bg-zinc-950/70 px-3 py-2 text-sm text-white"
            >
              {authors.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>

            {!showNewAuthor ? (
              <>
                <button
                  onClick={() => setShowNewAuthor(true)}
                  className="rounded-lg border border-white/10 p-2 text-zinc-400 transition hover:border-[#c90c61] hover:text-[#c90c61]"
                  title="Add author"
                >
                  <Plus size={16} />
                </button>

                <button
                  onClick={handleDeleteAuthor}
                  className="rounded-lg border border-white/10 p-2 text-zinc-400 transition hover:border-red-500 hover:text-red-400"
                  title="Delete author"
                >
                  <Trash2 size={16} />
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <input
                  autoFocus
                  value={newAuthor}
                  onChange={(e) => setNewAuthor(e.target.value)}
                  placeholder="Author name"
                  className="w-40 rounded-lg border border-white/10 bg-zinc-950/70 px-3 py-2 text-sm text-white"
                />

                <button
                  onClick={handleAddAuthor}
                  className="rounded-lg border border-emerald-500/40 p-2 text-emerald-400 transition hover:bg-emerald-500/10"
                >
                  <Check size={16} />
                </button>

                <button
                  onClick={() => {
                    setShowNewAuthor(false);
                    setNewAuthor("");
                  }}
                  className="rounded-lg border border-white/10 p-2 text-zinc-400 transition hover:text-white"
                >
                  <X size={16} />
                </button>
              </div>
            )}
          </div>

          {templates.length === 0 && (
            <span className="text-xs text-zinc-500">
              Upload one from the Resources page
            </span>
          )}
        </div>

        {/* Grid */}
        <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <TranscriptPanel transcript={transcript} setTranscript={setTranscript} />

          <DiscoveryPanel
            transcript={transcript}
            authorId={selectedAuthor}
            templateId={selectedTemplate}
            state={state}
            setState={setState}
            setSow={setSow}
            setReview={setReview}
            setConfidence={setConfidence}
            setHistoricalSowsUsed={setHistoricalSowsUsed}
            setHistoricalRisksConsidered={setHistoricalRisksConsidered}
          />
        </div>

        {/* SOW Viewer */}
        <div className="mt-6">
          <SowViewer sow={sow} />
        </div>
        {/* Review Panel */}
        <ReviewPanel review={review} confidence={confidence} />
        {/* Export */}
        <div className="mt-6">
          <ExportPanel
            state={state}
            sow={sow}
            templateId={selectedTemplate}
            transcript={transcript}
          />
        </div>
      </div>
    </div>
  );
}