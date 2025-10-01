import type { QueryUnderstandingResult } from "../../types/chat";

interface ChatQueryInsightsProps {
  analysis: QueryUnderstandingResult | null;
  collapsed?: boolean;
  onToggle?: () => void;
}

export const ChatQueryInsights = ({ analysis, collapsed = false, onToggle }: ChatQueryInsightsProps) => {
  if (!analysis) {
    return null;
  }

  const hasContent =
    !!analysis.summary ||
    (analysis.intents && analysis.intents.length > 0) ||
    (analysis.clarifyingQuestions && analysis.clarifyingQuestions.length > 0) ||
    (analysis.filterSuggestions && analysis.filterSuggestions.length > 0);

  if (!hasContent) {
    return null;
  }

  const hasDetails =
    (analysis.intents && analysis.intents.length > 0) ||
    (analysis.clarifyingQuestions && analysis.clarifyingQuestions.length > 0) ||
    (analysis.filterSuggestions && analysis.filterSuggestions.length > 0);

  const showDetails = !collapsed && hasDetails;
  const summaryText =
    analysis.summary ||
    "Based on your latest message, the assistant outlined how to frame the investigation.";

  return (
    <div className="rounded-2xl border border-purple-500/30 bg-purple-500/10 p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-purple-200/80">Query Insight</p>
          <p className="mt-1 text-sm text-purple-100/90 leading-snug">{summaryText}</p>
        </div>
        {hasDetails && onToggle && (
          <button
            type="button"
            onClick={onToggle}
            className="rounded-md border border-purple-400/40 bg-purple-500/20 px-3 py-1 text-[11px] font-medium text-purple-100 hover:bg-purple-500/30 transition"
          >
            {collapsed ? "Show details" : "Hide details"}
          </button>
        )}
      </div>

      {showDetails && (
        <div className="space-y-3">
          {analysis.intents?.length ? (
            <div>
              <p className="text-xs uppercase tracking-wide text-purple-200/70">Detected Intents</p>
              <ul className="mt-2 space-y-1.5">
                {analysis.intents.map((intent, index) => (
                  <li
                    key={`${intent.description}-${index}`}
                    className="rounded-lg bg-purple-500/10 px-3 py-2 text-xs text-purple-100/90"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-[13px] text-purple-100">
                        {intent.description}
                      </span>
                      <span className="text-[11px] text-purple-300/80">
                        {(intent.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    {intent.serviceHints?.length ? (
                      <p className="mt-1 text-[11px] text-purple-200/70">
                        Services: {intent.serviceHints.join(", ")}
                      </p>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {analysis.clarifyingQuestions?.length ? (
            <div>
              <p className="text-xs uppercase tracking-wide text-purple-200/70">Clarifying Questions</p>
              <ul className="mt-2 space-y-1.5 text-xs text-purple-100/90">
                {analysis.clarifyingQuestions.map((question, index) => (
                  <li key={`${question}-${index}`} className="rounded-lg bg-purple-500/10 px-3 py-2">
                    {question}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {analysis.filterSuggestions?.length ? (
            <div>
              <p className="text-xs uppercase tracking-wide text-purple-200/70">Suggested Filters</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {analysis.filterSuggestions.map((suggestion, index) => (
                  <span
                    key={`${suggestion.key}-${suggestion.value}-${index}`}
                    className="inline-flex items-center rounded-full border border-purple-500/40 bg-purple-500/20 px-3 py-1 text-[11px] text-purple-100/90"
                  >
                    {suggestion.key}: {suggestion.value}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};

export default ChatQueryInsights;
