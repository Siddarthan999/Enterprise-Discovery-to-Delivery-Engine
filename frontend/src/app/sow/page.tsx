"use client";

import { useState, useEffect } from "react";
import { FileText, Sparkles, Download, ChevronRight, Layers } from "lucide-react";
import TranscriptPanel from "@/components/sow/TranscriptPanel";
import DiscoveryPanel from "@/components/sow/DiscoveryPanel";
import SowViewer from "@/components/sow/SowViewer";
import ExportPanel from "@/components/sow/ExportPanel";
import AppNav from "@/components/layout/AppNav";
import { getTemplates } from "@/lib/api";

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

  useEffect(() => {
    async function loadTemplates() {
      const data = await getTemplates();
      setTemplates(data);
      if (data.length > 0) {
        setSelectedTemplate(data[0].id);
      }
    }

    loadTemplates();
  }, []);

  const steps: Step[] = [
    { label: "Transcript", icon: <FileText size={14} />, done: !!transcript },
    { label: "Discovery", icon: <Sparkles size={14} />, done: !!state },
    { label: "Export", icon: <Download size={14} />, done: !!sow },
  ];

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
                <Layers size={20} />
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
          <label className="text-sm text-zinc-400">Template</label>

          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="rounded-lg border border-white/10 bg-zinc-950/70 px-3 py-2 text-sm text-white outline-none focus:border-[#c90c61]/50"
          >
            {templates.length === 0 && <option value="">No templates uploaded</option>}
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>

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
            state={state}
            setState={setState}
            setSow={setSow}
          />
        </div>

        {/* SOW Viewer */}
        <div className="mt-6">
          <SowViewer sow={sow} />
        </div>

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