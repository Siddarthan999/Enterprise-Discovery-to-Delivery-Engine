"use client";

import React from "react";

type Finding = {
  severity?: "critical" | "high" | "medium" | "low" | string;
  section?: string;
  issue?: string;
  why_it_matters?: string;
  recommended_fix?: string;
  [key: string]: unknown;
};

type Agent = {
  agent?: string;
  score?: number | string;
  status?: "pass" | "warning" | "fail" | string;
  findings?: Finding[];
  strengths?: unknown[];
  missing_items?: unknown[];
  red_flags?: unknown[];
  [key: string]: unknown;
};

type Confidence = {
  overall_confidence?: number | string;
  label?: string;
  [key: string]: unknown;
};

function isPlainRenderable(value: unknown): value is string | number | boolean {
  return (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  );
}

function renderText(value: unknown) {
  if (value == null) return "—";
  if (isPlainRenderable(value)) return String(value);

  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (isPlainRenderable(item)) return String(item);
        if (item && typeof item === "object") {
          const obj = item as Record<string, unknown>;
          if ("issue" in obj && typeof obj.issue === "string") return obj.issue;
          if ("agent" in obj && typeof obj.agent === "string") return obj.agent;
          if ("label" in obj && typeof obj.label === "string") return obj.label;
          if ("type" in obj && typeof obj.type === "string") return obj.type;
          if ("task_type" in obj && typeof obj.task_type === "string") {
            return String(obj.task_type);
          }
        }
        return JSON.stringify(item);
      })
      .join(", ");
  }

  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;

    if ("issue" in obj && typeof obj.issue === "string") return obj.issue;
    if ("agent" in obj && typeof obj.agent === "string") return obj.agent;
    if ("label" in obj && typeof obj.label === "string") return obj.label;
    if ("type" in obj && typeof obj.type === "string") return obj.type;
    if ("task_type" in obj && typeof obj.task_type === "string") {
      return String(obj.task_type);
    }
    if ("id" in obj && "type" in obj) {
      return `${String(obj.type)} (${String(obj.id)})`;
    }

    return JSON.stringify(obj, null, 2);
  }

  return String(value);
}

function renderListItem(value: unknown): React.ReactNode {
  if (value == null) {
    return <span>—</span>;
  }

  if (isPlainRenderable(value)) {
    return <span>{String(value)}</span>;
  }

  if (Array.isArray(value)) {
    return (
      <div className="space-y-2">
        {value.map((item, idx) => (
          <div key={idx} className="min-w-0">
            {renderListItem(item)}
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;

    if ("issue" in obj || "task_type" in obj || "type" in obj || "agent" in obj) {
      return (
        <div className="rounded-md border border-white/10 bg-zinc-900/60 p-2">
          <div className="text-sm text-zinc-200 break-words">{renderText(value)}</div>

          {"score" in obj && obj.score != null && (
            <div className="mt-1 text-xs text-zinc-500">
              Score: {String(obj.score)}
            </div>
          )}

          {"status" in obj && obj.status != null && (
            <div className="mt-1 text-xs text-zinc-500">
              Status: {String(obj.status)}
            </div>
          )}

          {"section" in obj && obj.section != null && (
            <div className="mt-1 text-xs text-zinc-500">
              Section: {String(obj.section)}
            </div>
          )}

          {"parameters" in obj && obj.parameters != null && (
            <pre className="mt-2 whitespace-pre-wrap break-words text-[11px] text-zinc-500">
              {JSON.stringify(obj.parameters, null, 2)}
            </pre>
          )}
        </div>
      );
    }

    return (
      <pre className="whitespace-pre-wrap break-words text-[11px] text-zinc-500">
        {JSON.stringify(obj, null, 2)}
      </pre>
    );
  }

  return <span>{String(value)}</span>;
}

export default function ReviewPanel({
  review,
  confidence,
}: {
  review: any;
  confidence: any;
}) {
  if (!review && !confidence) return null;

  const agents: Agent[] = Array.isArray(review?.agents) ? review.agents : [];
  const topLevelRedFlags: unknown[] = Array.isArray(review?.red_flags)
    ? review.red_flags
    : [];

  const overallConfidence =
    confidence?.overall_confidence != null
      ? String(confidence.overall_confidence)
      : "—";

  const confidenceLabel =
    confidence?.label != null ? String(confidence.label) : "Unknown";

  return (
    <div className="mt-6 rounded-2xl border border-white/10 bg-zinc-900/80 p-5 shadow-lg shadow-black/20">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Reviewer agents</h2>
          <p className="text-sm text-zinc-400">
            Transparent validation, coverage, GRC, risk, and feasibility review
          </p>
        </div>

        {confidence && (
          <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/10 px-4 py-2 text-sm">
            <div className="text-zinc-400">Confidence</div>
            <div className="font-semibold text-cyan-300">
              {overallConfidence}/100 ({confidenceLabel})
            </div>
          </div>
        )}
      </div>

      {topLevelRedFlags.length > 0 && (
        <div className="mt-4 rounded-xl border border-rose-500/20 bg-rose-500/10 p-4">
          <h3 className="text-sm font-semibold text-rose-300">Red flags</h3>
          <ul className="mt-2 space-y-2 text-sm text-zinc-200">
            {topLevelRedFlags.map((flag, idx) => (
              <li key={idx} className="list-none">
                <div className="flex gap-2">
                  <span>•</span>
                  <div className="min-w-0 flex-1">{renderListItem(flag)}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {agents.map((agent: Agent, idx: number) => {
          const findings = Array.isArray(agent.findings) ? agent.findings : [];
          const strengths = Array.isArray(agent.strengths) ? agent.strengths : [];
          const missingItems = Array.isArray(agent.missing_items)
            ? agent.missing_items
            : [];
          const redFlags = Array.isArray(agent.red_flags) ? agent.red_flags : [];

          return (
            <div
              key={idx}
              className="rounded-xl border border-white/10 bg-zinc-950/70 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    {renderText(agent.agent)}
                  </h3>
                  <p className="mt-1 text-xs text-zinc-500">
                    Status: {renderText(agent.status)}
                  </p>
                </div>

                <div className="rounded-lg border border-white/10 bg-zinc-900 px-3 py-1 text-sm text-cyan-300">
                  {renderText(agent.score)}/100
                </div>
              </div>

              {strengths.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-emerald-300">
                    Strengths
                  </h4>
                  <ul className="mt-2 space-y-2 text-sm text-zinc-300">
                    {strengths.map((item: unknown, i: number) => (
                      <li key={i} className="list-none">
                        <div className="flex gap-2">
                          <span>•</span>
                          <div className="min-w-0 flex-1">{renderListItem(item)}</div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {missingItems.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-amber-300">
                    Missing items
                  </h4>
                  <ul className="mt-2 space-y-2 text-sm text-zinc-300">
                    {missingItems.map((item: unknown, i: number) => (
                      <li key={i} className="list-none">
                        <div className="flex gap-2">
                          <span>•</span>
                          <div className="min-w-0 flex-1">{renderListItem(item)}</div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {redFlags.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-rose-300">
                    Agent red flags
                  </h4>
                  <ul className="mt-2 space-y-2 text-sm text-zinc-300">
                    {redFlags.map((item: unknown, i: number) => (
                      <li key={i} className="list-none">
                        <div className="flex gap-2">
                          <span>•</span>
                          <div className="min-w-0 flex-1">{renderListItem(item)}</div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {findings.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-rose-300">
                    Findings
                  </h4>
                  <div className="mt-2 space-y-3">
                    {findings.map((f: Finding, i: number) => (
                      <div
                        key={i}
                        className="rounded-lg border border-white/10 bg-zinc-900/70 p-3"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-medium text-zinc-400">
                            {renderText(f.section)}
                          </span>
                          <span className="text-xs uppercase text-rose-300">
                            {renderText(f.severity)}
                          </span>
                        </div>

                        <p className="mt-2 text-sm font-medium text-white">
                          {renderText(f.issue)}
                        </p>

                        <p className="mt-1 text-sm text-zinc-400">
                          {renderText(f.why_it_matters)}
                        </p>

                        <p className="mt-2 text-sm text-cyan-300">
                          Fix: {renderText(f.recommended_fix)}
                        </p>

                        {Object.keys(f).some(
                          (key) =>
                            ![
                              "severity",
                              "section",
                              "issue",
                              "why_it_matters",
                              "recommended_fix",
                            ].includes(key)
                        ) && (
                          <pre className="mt-3 whitespace-pre-wrap break-words rounded-md border border-white/10 bg-zinc-950/80 p-2 text-[11px] text-zinc-500">
                            {JSON.stringify(
                              Object.fromEntries(
                                Object.entries(f).filter(
                                  ([key]) =>
                                    ![
                                      "severity",
                                      "section",
                                      "issue",
                                      "why_it_matters",
                                      "recommended_fix",
                                    ].includes(key)
                                )
                              ),
                              null,
                              2
                            )}
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {!agents.length && review && (
        <div className="mt-5 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4">
          <h3 className="text-sm font-semibold text-amber-300">Review payload</h3>
          <pre className="mt-2 whitespace-pre-wrap break-words text-xs text-zinc-300">
            {JSON.stringify(review, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}