"use client";

import { useState } from "react";

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

      const res = await fetch(
        "http://localhost:8000/api/transcript/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await res.json();

      /**
       * expected flexible backend response:
       * {
       *   transcript: "...",
       *   text: "...",
       *   content: "..."
       * }
       */
      const extracted =
        data.transcript || data.text || data.content || "";

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
      const res = await fetch(
        "http://localhost:8000/api/transcript/text",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: transcript,
          }),
        }
      );

      const data = await res.json();

      const extracted =
        data.transcript || data.text || data.content || transcript;

      setTranscript(extracted);
      onUploaded?.(extracted);
    } catch (err) {
      console.error("Paste ingestion failed:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-medium">Transcript Ingestion</h2>
          <p className="text-xs text-zinc-400 mt-1">
            Upload or paste meeting transcript
          </p>
        </div>

        <div className="flex gap-2 text-xs">
          <button
            onClick={() => setMode("upload")}
            className={`px-3 py-1 rounded-md border ${
              mode === "upload"
                ? "bg-white text-black border-white"
                : "bg-zinc-950 text-zinc-400 border-zinc-800"
            }`}
          >
            Upload
          </button>

          <button
            onClick={() => setMode("paste")}
            className={`px-3 py-1 rounded-md border ${
              mode === "paste"
                ? "bg-white text-black border-white"
                : "bg-zinc-950 text-zinc-400 border-zinc-800"
            }`}
          >
            Paste
          </button>
        </div>
      </div>

      {/* FILE UPLOAD MODE */}
      {mode === "upload" && (
        <div className="mt-5">
          <label className="flex flex-col items-center justify-center border border-dashed border-zinc-700 rounded-lg p-6 cursor-pointer hover:border-zinc-500 transition">
            <input
              type="file"
              accept=".txt,.md,.vtt,.json,.docx"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileUpload(file);
              }}
            />

            <p className="text-sm text-zinc-300">
              {loading
                ? "Uploading & processing..."
                : fileName
                ? `Selected: ${fileName}`
                : "Click to upload transcript file"}
            </p>

            <p className="text-xs text-zinc-500 mt-1">
              Supported: TXT, VTT, MD, JSON, DOCX
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
            className="w-full h-64 p-3 rounded-lg bg-zinc-950 border border-zinc-800 text-sm text-white focus:outline-none focus:border-zinc-600"
          />

          <div className="flex justify-between mt-3 items-center">
            <span className="text-xs text-zinc-500">
              {transcript.length} chars
            </span>

            <button
              onClick={handlePasteUpload}
              disabled={!transcript.trim() || loading}
              className="px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-zinc-200 disabled:opacity-50"
            >
              {loading ? "Processing..." : "Ingest Text"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}