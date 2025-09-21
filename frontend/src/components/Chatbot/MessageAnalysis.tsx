import React, { useMemo } from "react";
import { ProperMarkdownRenderer } from "./ProperMarkdownRenderer";

interface MessageAnalysisProps {
  analysis: string;
  isStreaming?: boolean;
  // Keeping optional props for compatibility, but unused to reduce noise
  metadata?: any;
  needsClarification?: boolean;
  clarifyingQuestions?: Array<{ question: string; context: string }>;
  missingInfo?: string[];
  toolResults?: any;
  completeResult?: any;
}

const sanitizeLine = (line: string) => line.trim().replace(/\s+/g, " ");

const parseAnalysis = (analysis: string) => {
  if (!analysis) return [] as Array<{ header: string; details: string[] }>;
  const normalized = analysis.replace(/\r\n/g, "\n").trim();
  if (!normalized) return [];

  return normalized
    .split(/\n\s*\n/)
    .map((block) => {
      const lines = block
        .split("\n")
        .map((line) => sanitizeLine(line))
        .filter(Boolean);
      if (!lines.length) return null;

      const header = lines[0];
      const details = lines
        .slice(1)
        .filter((line) => !/^[-_]{3,}$/.test(line.replace(/\s/g, "")))
        .map((line) => line.replace(/^[-•]+\s*/, "").trim())
        .filter(Boolean);

      return { header, details };
    })
    .filter((section): section is { header: string; details: string[] } => Boolean(section));
};

const deriveHeaderParts = (header: string) => {
  if (!header) return { badge: "", title: "" };
  const pipeSplit = header.split("|");
  if (pipeSplit.length === 2) {
    return { badge: sanitizeLine(pipeSplit[0]), title: sanitizeLine(pipeSplit[1]) };
  }

  const colonSplit = header.split(":");
  if (colonSplit.length >= 2) {
    const [badge, ...rest] = colonSplit;
    return { badge: sanitizeLine(badge), title: sanitizeLine(rest.join(":")) };
  }

  return { badge: "", title: sanitizeLine(header) };
};

const DetailLine: React.FC<{ content: string }> = ({ content }) => {
  const trimmed = content.trim();
  const [label, ...restParts] = trimmed.split(":");
  const hasColon = restParts.length > 0;
  const value = restParts.join(":").trim();

  return (
    <div className="flex items-start gap-3 text-sm leading-6 text-slate-300">
      <span className="mt-[7px] h-2 w-2 rounded-full bg-gradient-to-r from-sky-400 via-cyan-400 to-violet-500 shadow-[0_0_10px_rgba(56,189,248,0.55)]"></span>
      <div className="flex-1 min-w-0">
        {hasColon ? (
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <span className="font-semibold text-slate-100">{label.trim()}:</span>
            <span className="text-slate-300/90">{value || "—"}</span>
          </div>
        ) : (
          <span className="text-slate-300/90">{trimmed}</span>
        )}
      </div>
    </div>
  );
};

export const MessageAnalysis: React.FC<MessageAnalysisProps> = ({ analysis, isStreaming = false }) => {
  const structuredSections = useMemo(() => parseAnalysis(analysis), [analysis]);
  const hasStructuredView = structuredSections.length > 0;

  if (!analysis && !isStreaming) {
    return null;
  }

  if (!hasStructuredView) {
    return (
      <div className="space-y-4">
        {analysis ? (
          <div className="relative">
            <ProperMarkdownRenderer content={analysis} />
            {isStreaming && (
              <div className="absolute bottom-0 right-0 w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center gap-3 text-slate-300 py-6">
            <div className="flex space-x-1.5">
              <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce"></div>
              <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0.12s" }}></div>
              <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0.24s" }}></div>
            </div>
            <span className="text-sm font-medium">Thinking…</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {structuredSections.map((section, idx) => {
        const { badge, title } = deriveHeaderParts(section.header);
        const badgeLabel = badge || "ANALYSIS";
        const titleLabel = title || section.header;

        return (
          <div
            key={`${section.header}-${idx}`}
            className="group relative overflow-hidden rounded-2xl border border-slate-800/70 bg-slate-900/45 backdrop-blur-md shadow-[0_10px_40px_rgba(15,23,42,0.35)] transition-all duration-500 hover:-translate-y-1 hover:border-slate-700/70 hover:shadow-[0_25px_60px_rgba(56,189,248,0.18)] animate-slide-up"
            style={{ animationDelay: `${idx * 0.05}s` }}
          >
            <div className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700 bg-[radial-gradient(120%_110%_at_50%_0%,rgba(56,189,248,0.12),rgba(168,85,247,0.05)_45%,transparent)]" />
            <div className="pointer-events-none absolute inset-x-0 top-0 h-[1.5px] bg-gradient-to-r from-sky-500/70 via-transparent to-violet-500/70" />

            <div className="relative z-10 px-4 py-4 sm:px-6 sm:py-6 space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="space-y-2">
                  <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-sky-500/40 bg-sky-500/10 text-[11px] font-semibold tracking-[0.2em] text-sky-200 uppercase">
                    {badgeLabel}
                  </span>
                  <h3 className="text-base sm:text-lg font-semibold text-slate-100 tracking-tight">
                    {titleLabel}
                  </h3>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-slate-400 uppercase tracking-[0.3em]">
                  <span className="h-2 w-2 rounded-full bg-gradient-to-r from-sky-400 via-cyan-400 to-violet-500 shadow-[0_0_12px_rgba(56,189,248,0.65)] animate-pulse" />
                  <span>{isStreaming && idx === 0 ? "Updating" : "Insight"}</span>
                </div>
              </div>

              <div className="space-y-3">
                {section.details.length > 0 ? (
                  section.details.map((detail, detailIdx) => (
                    <DetailLine key={`${section.header}-${detailIdx}`} content={detail} />
                  ))
                ) : (
                  <div className="text-sm text-slate-300/80">No additional details supplied.</div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
