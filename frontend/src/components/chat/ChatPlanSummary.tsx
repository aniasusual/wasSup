import type {
  InvestigationPlan,
  QueryHistoryEntry,
  QueryUnderstandingResult,
  FilterSuggestion,
} from "../../types/chat";

interface ChatPlanSummaryProps {
  plan: InvestigationPlan | null;
  contextSummary: string;
  isLoading: boolean;
  queryAnalysis?: QueryUnderstandingResult | null;
  queryHistory?: QueryHistoryEntry[];
  onApplyFilterSuggestion?: (suggestion: FilterSuggestion) => void;
  className?: string;
}

const statusTone: Record<string, string> = {
  pending: "border-amber-400/40 text-amber-200",
  in_progress: "border-blue-400/40 text-blue-200",
  complete: "border-emerald-400/40 text-emerald-200",
};

export const ChatPlanSummary = ({
  plan,
  contextSummary,
  isLoading,
  queryAnalysis,
  queryHistory,
  onApplyFilterSuggestion,
  className = "",
}: ChatPlanSummaryProps) => {
  if (isLoading) {
    return (
      <div className={`rounded-xl border border-blue-500/30 bg-blue-500/10 p-4 ${className}`}>
        <div className="h-4 w-28 rounded skeleton mb-3" />
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="h-3 w-full rounded skeleton" />
          ))}
        </div>
      </div>
    );
  }

  const hasPlan = Boolean(plan);

  return (
    <div className={`rounded-2xl border border-blue-500/20 bg-gray-900/60 p-4 space-y-4 ${className}`}>
      {queryAnalysis && (
        <div className="rounded-xl border border-purple-400/20 bg-purple-500/10 px-4 py-3 space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-purple-200/70">Assistant Understanding</p>
              <p className="mt-1 text-sm text-purple-100/90 leading-snug">
                {queryAnalysis.summary ||
                  "The assistant interpreted your message and adjusted the plan accordingly."}
              </p>
            </div>
            {(queryAnalysis.intents?.length || queryAnalysis.clarifyingQuestions?.length) ? (
              <span className="text-[11px] text-purple-100/80 bg-purple-500/25 rounded-full px-3 py-1">
                {queryAnalysis.intents?.length ?? 0} intents
              </span>
            ) : null}
          </div>

          {queryAnalysis.intents?.length ? (
            <div>
              <p className="text-[11px] uppercase tracking-wide text-purple-200/60 mb-1">Detected intents</p>
              <div className="flex flex-wrap gap-2">
                {queryAnalysis.intents.map((intent, index) => (
                  <span
                    key={`${intent.description}-${index}`}
                    className="inline-flex items-center rounded-full bg-purple-500/25 px-3 py-1 text-[11px] text-purple-100/90"
                  >
                    {intent.description}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {queryAnalysis.filterSuggestions?.length ? (
            <div>
              <p className="text-[11px] uppercase tracking-wide text-purple-200/60 mb-1">Suggested filters</p>
              <div className="flex flex-wrap gap-2">
                {queryAnalysis.filterSuggestions.map((suggestion, index) => (
                  <button
                    key={`${suggestion.key}-${suggestion.value}-${index}`}
                    type="button"
                    onClick={() => onApplyFilterSuggestion?.(suggestion)}
                    className="inline-flex items-center rounded-full border border-purple-400/40 bg-purple-500/20 px-3 py-1 text-[11px] text-purple-100/90 hover:border-purple-200/60 hover:bg-purple-500/30 transition"
                    title="Apply filter to log view"
                  >
                    {suggestion.key}: {suggestion.value}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {queryAnalysis.clarifyingQuestions?.length ? (
            <div>
              <p className="text-[11px] uppercase tracking-wide text-purple-200/60 mb-1">Follow-up questions</p>
              <ul className="space-y-1.5 text-[11px] text-purple-100/80">
                {queryAnalysis.clarifyingQuestions.map((question, index) => (
                  <li key={`${question}-${index}`} className="rounded-lg bg-purple-500/20 px-3 py-2">
                    {question}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      )}

      {queryHistory && queryHistory.length > 1 && (
        <div className="rounded-xl border border-gray-800/60 bg-gray-950/60 px-4 py-3 space-y-2">
          <p className="text-[11px] uppercase tracking-wide text-gray-400/80">Recent interpretations</p>
          <ul className="space-y-1.5">
            {queryHistory
              .slice(-4, -1)
              .reverse()
              .map((entry) => (
                <li key={entry.messageId} className="text-[11px] text-gray-400">
                  <span className="text-gray-300">{entry.analysis.summary || "—"}</span>
                  {entry.generatedAt ? (
                    <span className="ml-2 text-gray-500">
                      {new Date(entry.generatedAt).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  ) : null}
                </li>
              ))}
          </ul>
        </div>
      )}

      {hasPlan ? (
        <>
          <div>
            <p className="text-xs uppercase tracking-wide text-blue-300/80">Investigation Focus</p>
            <h4 className="mt-1 text-base font-semibold text-gray-100">{plan!.focus}</h4>
            <p className="mt-2 text-sm text-gray-400 leading-relaxed">{plan!.summary}</p>
          </div>

          {contextSummary && (
            <div className="rounded-lg border border-gray-800/60 bg-gray-950/60 p-3">
              <p className="text-xs uppercase tracking-wide text-gray-500">Context</p>
              <p className="mt-1 text-sm text-gray-400 leading-snug">{contextSummary}</p>
            </div>
          )}

          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500">Planned Steps</p>
            <ul className="mt-2 space-y-2">
              {plan!.steps.map((step) => (
                <li
                  key={step.id}
                  className={`rounded-xl border ${statusTone[step.status] || statusTone.pending} bg-gray-950/60 p-3`}
                >
                  <p className="text-sm font-medium text-gray-100">{step.title}</p>
                  <p className="mt-1 text-xs text-gray-400 leading-snug">{step.description}</p>
                </li>
              ))}
            </ul>
          </div>

          {plan!.suggestedQueries.length > 0 && (
            <div>
              <p className="text-xs uppercase tracking-wide text-gray-500">Suggested Queries</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {plan!.suggestedQueries.map((query, index) => (
                  <span
                    key={`${query}-${index}`}
                    className="inline-flex items-center rounded-full border border-blue-500/40 bg-blue-500/10 px-3 py-1 text-xs text-blue-100/90"
                  >
                    {query}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="rounded-lg border border-gray-800/60 bg-gray-950/60 p-4 text-xs text-gray-400">
          The assistant is preparing an investigation plan. Provide more context or adjust filters to guide the next step.
        </div>
      )}
    </div>
  );
};

export default ChatPlanSummary;
