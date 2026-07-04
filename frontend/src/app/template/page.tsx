"use client";

import { useState } from "react";

export default function TemplatePage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);

  async function upload() {
    if (!file) return;

    setLoading(true);

    try {
      const form = new FormData();
      form.append("file", file);

      const res = await fetch("http://localhost:8000/api/template/upload", {
        method: "POST",
        body: form,
      });

      const data = await res.json();
      setResponse(data);
      console.log("Template uploaded:", data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-6">
      <div className="max-w-2xl mx-auto space-y-6">

        <div>
          <h1 className="text-xl font-semibold">Template Manager</h1>
          <p className="text-sm text-zinc-400">
            Upload DOCX templates for SOW generation
          </p>
        </div>

        {/* UPLOAD BOX */}
        <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900">
          <input
            type="file"
            accept=".docx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />

          <button
            onClick={upload}
            disabled={!file || loading}
            className="mt-4 px-4 py-2 bg-white text-black rounded-lg disabled:opacity-50"
          >
            {loading ? "Uploading..." : "Upload Template"}
          </button>
        </div>

        {/* RESPONSE PREVIEW */}
        {response && (
          <pre className="p-4 bg-black border border-zinc-800 rounded-lg text-xs overflow-auto">
            {JSON.stringify(response, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}