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
  if (!analysis) {
    return [] as Array<{ header: string; details: string[] }>;
  }

  const normalized = analysis.replace(/\r?\n/g, "\n").trim();
  if (!normalized) {
    return [];
  }

  return normalized
    .split(/\n\s*\n/)
    .map((block) => {
      const lines = block
        .split(/\n/)
        .map((line) => sanitizeLine(line))
        .filter(Boolean);
      if (!lines.length) {
        return null;
      }

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

const HIDDEN_DETAIL_LABELS = new Set([
  "original query",
  "project id",
  "target services",
  "severity levels",
  "time indicators",
  "query type",
  "confidence",
  "reasoning",
  "needs clarification",
  "missing info",
  "pending questions",
  "strategy selected",
  "questions generated",
  "clarification item",
]);

const HIDDEN_SECTION_KEYWORDS = [
  "query analysis",
  "clarification requirements",
  "clarification engine",
  "contextual questions",
  "query classifier",
  "wait for user response",
  "intelligence assessment",
  "suggested investigation scope",
];

const HIDDEN_METADATA_PREFIXES = [
  "original query",
  "project id",
  "target services",
  "severity levels",
  "time indicators",
  "query type",
  "confidence",
  "reasoning",
  "needs clarification",
  "pending questions",
  "strategy selected",
  "questions generated",
  "scope:",
  "clarification item",
];

const shouldHideDetail = (content: string) => {
  const trimmed = content.trim();
  if (!trimmed) {
    return true;
  }

  const [label, ...restParts] = trimmed.split(":");
  const hasColon = restParts.length > 0;
  const normalizedLabel = label.trim().toLowerCase();

  if (hasColon && HIDDEN_DETAIL_LABELS.has(normalizedLabel)) {
    return true;
  }

  if (!hasColon && trimmed.toLowerCase().startsWith("scope:")) {
    return true;
  }

  return false;
};

const DetailLine: React.FC<{ content: string }> = ({ content }) => {
  if (shouldHideDetail(content)) {
    return null;
  }

  const trimmed = content.trim();
  const [label, ...restParts] = trimmed.split(":");
  const hasColon = restParts.length > 0;
  const value = restParts.join(":").trim();

  return (
    <li className="leading-6 text-sm text-slate-200/90">
      {hasColon ? (
        <>
          <span className="font-semibold text-slate-100">{label.trim()}:</span>{" "}
          <span>{value || "—"}</span>
        </>
      ) : (
        trimmed
      )}
    </li>
  );
};

export const MessageAnalysis: React.FC<MessageAnalysisProps> = ({
  analysis,
  isStreaming = false,
  needsClarification,
  clarifyingQuestions,
  missingInfo,
}) => {
  const structuredSections = useMemo(() => parseAnalysis(analysis), [analysis]);

  const filteredSections = useMemo(() => {
    return structuredSections
      .map((section) => {
        const header = section.header || "";
        const headerLower = header.toLowerCase();
        const normalizedHeader = headerLower.replace(/[^a-z]/g, "");

        if (normalizedHeader.startsWith("section") || normalizedHeader.startsWith("node")) {
          if (HIDDEN_SECTION_KEYWORDS.some((keyword) => headerLower.includes(keyword))) {
            return null;
          }
        }

        if (HIDDEN_SECTION_KEYWORDS.some((keyword) => headerLower.includes(keyword))) {
          return null;
        }

        const allowedKeywords = [
          "summary",
          "insight",
          "recommend",
          "next",
          "action",
          "takeaway",
          "finding",
          "result",
          "plan",
          "guidance",
        ];

        if (!allowedKeywords.some((keyword) => headerLower.includes(keyword))) {
          return null;
        }

        const visibleDetails = section.details.filter((detail) => !shouldHideDetail(detail));
        if (!visibleDetails.length) {
          return null;
        }

        return { header, details: visibleDetails };
      })
      .filter((section): section is { header: string; details: string[] } => Boolean(section));
  }, [structuredSections]);

  const hasStructuredView = filteredSections.length > 0;

  const clarificationPrompts = useMemo(() => {
    const seen = new Set<string>();
    return (clarifyingQuestions || [])
      .map((q) => (typeof q === "string" ? { question: q, context: "" } : q))
      .filter((q) => {
        const text = q?.question?.trim();
        if (!text) {
          return false;
        }
        const key = text.toLowerCase();
        if (seen.has(key)) {
          return false;
        }
        seen.add(key);
        return true;
      });
  }, [clarifyingQuestions]);
  const pendingMissingInfo = (missingInfo || []).filter((item) => Boolean(item?.trim()));
  const showClarificationCallout = needsClarification && (clarificationPrompts.length > 0 || pendingMissingInfo.length > 0);

  const sanitizedAnalysis = useMemo(() => {
    if (!analysis) {
      return "";
    }

    const lines = analysis.split(/\r?\n/);
    const kept: string[] = [];
    let skipBlock = false;

    for (const line of lines) {
      const trimmedLine = line.trim();

      if (/^(section|node)/i.test(trimmedLine)) {
        skipBlock = true;
        continue;
      }

      if (skipBlock) {
        if (trimmedLine === "") {
          skipBlock = false;
        }
        continue;
      }

      const lower = trimmedLine.toLowerCase();
      if (HIDDEN_METADATA_PREFIXES.some((prefix) => lower.startsWith(prefix))) {
        continue;
      }

      kept.push(line);
    }

    return kept.join("\n").trim();
  }, [analysis]);

  if (!analysis && !isStreaming && !showClarificationCallout) {
    return null;
  }

  const clarificationCallout =
    showClarificationCallout ? (
      <div className="rounded-xl border border-amber-500/30 bg-amber-500/15 px-4 py-3 text-sm leading-6 text-amber-100">
        <div className="text-[11px] uppercase tracking-[0.25em] text-amber-200">Clarification Needed</div>
        {clarificationPrompts.length > 0 && (
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-amber-50">
            {clarificationPrompts.map((prompt, idx) => (
              <li key={prompt.question ?? idx}>{prompt.question}</li>
            ))}
          </ol>
        )}
        {pendingMissingInfo.length > 0 && (
          <div className="mt-2 space-y-1">
            <div className="text-[12px] uppercase tracking-wide text-amber-200/80">Missing info</div>
            <ul className="list-disc space-y-1 pl-5 text-amber-50">
              {pendingMissingInfo.map((item, idx) => (
                <li key={`${item}-${idx}`}>{item}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="mt-3 text-[12px] text-amber-100/80">
          Share the answers and I will pick up the investigation from here.
        </div>
      </div>
    ) : null;

  if (needsClarification) {
    return <div className="space-y-4">{clarificationCallout}</div>;
  }

  return (
    <div className="space-y-4">
      {clarificationCallout}

      {hasStructuredView ? (
        <div className="space-y-3 text-sm leading-6 text-slate-200/90">
          {filteredSections.map((section, idx) => {
            const { badge, title } = deriveHeaderParts(section.header);
            const heading = [badge, title].filter(Boolean).join(" • ") || section.header;

            return (
              <div key={`${section.header}-${idx}`} className="space-y-1">
                {heading && <div className="font-semibold text-slate-100">{heading}</div>}
                <ul className="list-disc space-y-1 pl-5">
                  {section.details.map((detail, detailIdx) => (
                    <DetailLine key={`${section.header}-${detailIdx}`} content={detail} />
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="space-y-3 text-sm leading-6 text-slate-200/90">
          {sanitizedAnalysis ? (
            <ProperMarkdownRenderer content={sanitizedAnalysis} />
          ) : (
            <div className="flex items-center gap-2 text-slate-300">
              <span className="text-sm font-medium">Thinking…</span>
              <span className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
