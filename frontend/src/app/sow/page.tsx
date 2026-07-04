"use client";

import { useState } from "react";
import { useEffect } from "react";
import TranscriptPanel from "@/components/sow/TranscriptPanel";
import DiscoveryPanel from "@/components/sow/DiscoveryPanel";
import SowViewer from "@/components/sow/SowViewer";
import ExportPanel from "@/components/sow/ExportPanel";

export default function SOWPage() {
  const [transcript, setTranscript] = useState("");
  const [state, setState] = useState<any>(null);
  const [sow, setSow] = useState<string>("");
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");

  useEffect(() => {
    async function loadTemplates() {
      const res = await fetch("http://localhost:8000/api/template/list");
      const data = await res.json();

      setTemplates(data);
      if (data.length > 0) {
        setSelectedTemplate(data[0].id);
      }
    }

    loadTemplates();
  }, []);

  return (
    <div className="min-h-screen bg-zinc-950 text-white px-6 py-8">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div>
          <h1 className="text-2xl font-semibold">SOW Generator</h1>
          <p className="text-sm text-zinc-400 mt-1">
            Discovery → Structured State → Statement of Work
          </p>
        </div>

        <div className="mt-4 flex items-center gap-3">
          <label className="text-sm text-zinc-400">Template:</label>

          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 px-3 py-2 rounded-lg text-sm"
          >
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">

          <TranscriptPanel
            transcript={transcript}
            setTranscript={setTranscript}
          />

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
          />
        </div>

      </div>
    </div>
  );
}