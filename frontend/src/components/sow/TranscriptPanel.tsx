"use client";

import { useState } from "react";
import { Upload, ClipboardPaste, FileCheck2, Loader2, X, FileText } from "lucide-react";

export default function TranscriptPanel({
  transcript,
  setTranscript,
  onUploaded,
}: {
  transcript: string;
  setTranscript: (v: string) => void;
  onUploaded?: (text: string) => void;
}) {
  const [loading, setLoading] = useState(false);
  // Tracks every file that has contributed content to the current
  // transcript, in order — this is what makes it visible when something
  // was actually included vs silently dropped.
  const [includedFiles, setIncludedFiles] = useState<string[]>([]);
  const [mode, setMode] = useState<"upload" | "paste">("upload");

  function appendToTranscript(newContent: string, sourceLabel: string) {
    if (!newContent.trim()) return;

    // First upload: no separator needed. Subsequent uploads: append with
    // a clear header so multiple source documents stay distinguishable
    // instead of running together, and so it's obvious in the raw text
    // itself which upload contributed what.
    const trimmedPrev = transcript.trim();
    const block = `--- Source: ${sourceLabel} ---\n${newContent.trim()}`;
    setTranscript(trimmedPrev ? `${trimmedPrev}\n\n${block}` : block);
  }

  async function handleFileUpload(files: File[]) {
    setLoading(true);

    try {
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));

      const res = await fetch("http://localhost:8000/api/transcript/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      const extracted = data.transcript || data.text || data.content || "";

      const label = files.map((f) => f.name).join(", ");
      appendToTranscript(extracted, label);
      setIncludedFiles((prev) => [...prev, ...files.map((f) => f.name)]);

      onUploaded?.(extracted);
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handlePasteUpload() {
    if (!transcript.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/transcript/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript }),
      });

      const data = await res.json();
      const extracted = data.transcript || data.text || data.content || transcript;
      setTranscript(extracted);
      onUploaded?.(extracted);
    } catch (err) {
      console.error("Paste ingestion failed:", err);
    } finally {
      setLoading(false);
    }
  }

  function handleClearAll() {
    setTranscript("");
    setIncludedFiles([]);
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">Transcript/Context</h2>
          <p className="mt-0.5 text-xs text-zinc-400">
            Upload transcripts, emails, PDFs & supporting documents
          </p>
        </div>

        <div className="flex gap-1 rounded-lg border border-zinc-800 bg-zinc-950 p-1">
          <button
            onClick={() => setMode("upload")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition ${
              mode === "upload"
                ? "bg-white text-black"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            <Upload size={12} />
            Upload
          </button>
          <button
            onClick={() => setMode("paste")}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition ${
              mode === "paste"
                ? "bg-white text-black"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            <ClipboardPaste size={12} />
            Paste
          </button>
        </div>
      </div>

      {/* UPLOAD MODE */}
      {mode === "upload" && (
        <div className="mt-5">
          <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-700 bg-zinc-950/40 p-8 text-center transition hover:border-[#c90c61]/50 hover:bg-zinc-950/60">
            <input
              type="file"
              multiple
              accept=".txt, .md, .vtt, .json, .pdf, .docx, .pptx, .csv, .xls, .xlsx, .eml"
              className="hidden"
              onChange={(e) => {
                const files = e.target.files;
                if (files?.length) {
                  handleFileUpload(Array.from(files));
                }
                // Reset the input so selecting the SAME file again (e.g.
                // after Clear all) still fires onChange.
                e.target.value = "";
              }}
            />

            <div className={`rounded-full p-3 ${includedFiles.length ? "bg-[#c90c61]/10 text-[#c90c61]" : "bg-zinc-900 text-zinc-500"}`}>
              {loading ? (
                <Loader2 size={20} className="animate-spin" />
              ) : includedFiles.length ? (
                <FileCheck2 size={20} />
              ) : (
                <Upload size={20} />
              )}
            </div>

            <p className="text-sm text-zinc-300">
              {loading
                ? "Uploading & processing..."
                : includedFiles.length
                ? "Click to add another file"
                : "Click to upload client files"}
            </p>
            <p className="text-xs text-zinc-600">
              TXT · PDF · DOCX · PPTX · XLSX · CSV · EML · MD · VTT · JSON — select multiple
              at once, or upload one at a time.
            </p>
          </label>

          {/* Visible list of everything currently included — this is what
              makes it obvious if a file didn't actually make it in,
              instead of silently vanishing like before. */}
          {includedFiles.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-zinc-400">
                  Included in transcript ({includedFiles.length})
                </p>
                <button
                  onClick={handleClearAll}
                  className="flex items-center gap-1 text-xs text-zinc-500 hover:text-red-400"
                >
                  <X size={12} />
                  Clear all
                </button>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {includedFiles.map((name, i) => (
                  <span
                    key={`${name}-${i}`}
                    className="flex items-center gap-1.5 rounded-md border border-zinc-800 bg-zinc-950 px-2.5 py-1 text-xs text-zinc-300"
                  >
                    <FileText size={11} className="text-zinc-500" />
                    {name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* PASTE MODE */}
      {mode === "paste" && (
        <div className="mt-4">
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Paste meeting transcript here..."
            className="dark-scrollbar h-64 w-full rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-sm text-white outline-none focus:border-[#c90c61]/50"
          />

          <div className="mt-3 flex items-center justify-between">
            <span className="text-xs text-zinc-500">
              {transcript.length.toLocaleString()} characters
            </span>

            <button
              onClick={handlePasteUpload}
              disabled={!transcript.trim() || loading}
              className="flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-medium text-black transition hover:bg-zinc-200 disabled:opacity-50"
            >
              {loading && <Loader2 size={14} className="animate-spin" />}
              {loading ? "Processing..." : "Ingest Text"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}