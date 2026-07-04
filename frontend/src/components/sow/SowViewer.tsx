"use client";

export default function SowViewer({ sow }: { sow: string }) {
  return (
    <div className="p-5 rounded-xl border border-zinc-800 bg-zinc-900">
      
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium">SOW Preview</h2>
        <span className="text-xs text-zinc-500">
          Markdown Output
        </span>
      </div>

      <div className="mt-4">
        {sow ? (
          <pre className="text-sm text-zinc-200 whitespace-pre-wrap bg-zinc-950 p-4 rounded-lg border border-zinc-800">
            {sow}
          </pre>
        ) : (
          <div className="text-sm text-zinc-500">
            No SOW generated yet. Run discovery first.
          </div>
        )}
      </div>
    </div>
  );
}