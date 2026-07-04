"use client";

import { useState } from "react";

export default function ExportPanel({
  state,
  sow,
  templateId,
}: {
  state: any;
  sow: string;
  templateId: string;
}) {
  const [format, setFormat] = useState("markdown");
  const [loading, setLoading] = useState(false);

  async function exportFile() {
    if (!state) return;

    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/sow/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sow,
          format,
          template_id: templateId,   // ✅ ADD THIS
        }),
      });

      const blob = await res.blob();

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `sow.${format}`;
      a.click();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900 flex items-center justify-between">
      
      <div>
        <h2 className="text-lg font-medium">Export SOW</h2>
        <p className="text-xs text-zinc-400 mt-1">
          Download final deliverable
        </p>
      </div>

      <div className="flex gap-2 items-center">
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value)}
          className="bg-zinc-950 border border-zinc-800 px-3 py-2 rounded-lg text-sm"
        >
          <option value="md">Markdown</option>
          <option value="docx">DOCX</option>
          <option value="pdf">PDF</option>
        </select>

        <button
          onClick={exportFile}
          disabled={!sow || loading}
          className="px-4 py-2 rounded-lg bg-white text-black text-sm font-medium hover:bg-zinc-200 disabled:opacity-50"
        >
          {loading ? "Exporting..." : "Download"}
        </button>
      </div>
    </div>
  );
}