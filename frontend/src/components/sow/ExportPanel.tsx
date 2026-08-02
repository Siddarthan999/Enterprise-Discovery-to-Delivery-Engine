"use client";

import { useState } from "react";
import { FileText, FileType, FileCode, Download, Loader2 } from "lucide-react";

const BASE_FORMATS = [
  { id: "md", label: "Markdown", icon: FileCode },
  { id: "docx", label: "DOCX", icon: FileType },
  { id: "pdf", label: "PDF", icon: FileText },
];

type DocMode = "sow" | "proposal";

export default function ExportPanel({
  mode,
  state,
  sow,
  templateId,
  templateType,
  structuredProposal,
  transcript,
}: {
  mode: DocMode;
  state: any;
  sow: string;
  templateId: string;
  templateType?: string;
  structuredProposal?: any;
  transcript?: string;
}) {
  const [format, setFormat] = useState("md");
  const [loading, setLoading] = useState(false);

  const isPptxTemplate = templateType === "pptx";
  const FORMATS =
    mode === "proposal"
      ? [...BASE_FORMATS, { id: "pptx", label: "PPTX", icon: FileType }]
      : BASE_FORMATS;

  async function exportFile() {
    if (format === "pptx") {
      if (!templateId || !isPptxTemplate) {
        alert("Select a PPTX/POTX template first.");
        return;
      }
      if (!structuredProposal) {
        alert("Generate a proposal via Discovery before exporting to PPTX.");
        return;
      }

      setLoading(true);
      try {
        const res = await fetch("http://localhost:8000/api/proposal/export-pptx", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            structured_proposal: structuredProposal,
            template_id: templateId,
          }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "PPTX export failed");
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "proposal.pptx";
        a.click();
      } catch (err: any) {
        alert(err.message || "PPTX export failed");
      } finally {
        setLoading(false);
      }
      return;
    }

    if (!state) return;
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/sow/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sow,
          format,
          template_id: templateId,
          state,
          transcript,
        }),
      });

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = mode === "proposal" ? `proposal.${format}` : `sow.${format}`;
      a.click();
    } finally {
      setLoading(false);
    }
  }

  const label = mode === "proposal" ? "Proposal" : "SOW";

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-emerald-500/10 p-1.5 text-emerald-400">
            <Download size={16} />
          </div>
          <div>
            <h2 className="text-lg font-medium">Export {label}</h2>
            <p className="text-xs text-zinc-400">Download the final deliverable</p>
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          {/* Format segmented control */}
          <div className="flex gap-1 rounded-lg border border-zinc-800 bg-zinc-950 p-1">
            {FORMATS.map((f) => {
              const Icon = f.icon;
              const active = format === f.id;
              const disabled = f.id === "pptx" ? !isPptxTemplate : isPptxTemplate;
              return (
                <button
                  key={f.id}
                  onClick={() => !disabled && setFormat(f.id)}
                  disabled={disabled}
                  title={
                    disabled
                      ? f.id === "pptx"
                        ? "Select a PPTX/POTX template to enable this"
                        : "A PPTX/POTX template is selected — choose the PPTX format"
                      : undefined
                  }
                  className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${
                    active
                      ? "bg-white text-black"
                      : disabled
                      ? "text-zinc-700 cursor-not-allowed"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  <Icon size={12} />
                  {f.label}
                </button>
              );
            })}
          </div>

          <button
            onClick={exportFile}
            disabled={!sow || loading}
            className="flex items-center justify-center gap-2 rounded-lg bg-[#c90c61] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#a70a4d] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Download size={14} />
            )}
            {loading ? "Exporting..." : "Download"}
          </button>
        </div>
      </div>

      {!sow && (
        <p className="mt-3 text-xs text-zinc-600">
          Generate a {label} via Discovery before exporting.
        </p>
      )}
    </div>
  );
}