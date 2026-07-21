"use client";

import { useState } from "react";
import { Upload, ClipboardPaste, FileCheck2, Loader2 } from "lucide-react";

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
  const [fileName, setFileName] = useState<string | null>(null);
  const [mode, setMode] = useState<"upload" | "paste">("upload");

  async function handleFileUpload(file: File) {
    setLoading(true);
    setFileName(file.name);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://localhost:8000/api/transcript/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      const extracted = data.transcript || data.text || data.content || "";
      setTranscript(extracted);
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
        body: JSON.stringify({ text: transcript }),
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

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">Transcript</h2>
          <p className="mt-0.5 text-xs text-zinc-400">
            Upload or paste a meeting transcript
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
              accept=".txt,.md,.vtt,.json,.docx"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileUpload(file);
              }}
            />

            <div className={`rounded-full p-3 ${fileName ? "bg-[#c90c61]/10 text-[#c90c61]" : "bg-zinc-900 text-zinc-500"}`}>
              {loading ? (
                <Loader2 size={20} className="animate-spin" />
              ) : fileName ? (
                <FileCheck2 size={20} />
              ) : (
                <Upload size={20} />
              )}
            </div>

            <p className="text-sm text-zinc-300">
              {loading
                ? "Uploading & processing..."
                : fileName
                ? fileName
                : "Click to upload transcript file"}
            </p>
            <p className="text-xs text-zinc-600">
              TXT · VTT · MD · JSON · DOCX
            </p>
          </label>
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