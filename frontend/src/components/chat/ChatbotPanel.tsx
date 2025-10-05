import { useMemo } from "react";

import type {
  ChatMessage,
  ChatSuggestion,
  InvestigationPlan,
  QueryUnderstandingResult,
  QueryHistoryEntry,
  FilterSuggestion,
  ChatLogReference,
  ChatSessionSummary,
} from "../../types/chat";
import { ChatHeader } from "./ChatHeader";
import { ChatMessageList } from "./ChatMessageList";
import { ChatSuggestionBar } from "./ChatSuggestionBar";
import { ChatComposer } from "./ChatComposer";
import { ChatPlanSummary } from "./ChatPlanSummary";

interface ChatbotPanelProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  error?: string | null;
  suggestions?: ChatSuggestion[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onSuggestionSelect: (prompt: string) => void;
  onReset: () => void;
  onToggleExpand?: () => void;
  isExpanded?: boolean;
  plan?: InvestigationPlan | null;
  contextSummary?: string;
  queryAnalysis?: QueryUnderstandingResult | null;
  queryHistory?: QueryHistoryEntry[];
  onApplyFilterSuggestion?: (suggestion: FilterSuggestion) => void;
  onLogReferenceSelect?: (reference: ChatLogReference) => void;
  sessions?: ChatSessionSummary[];
  activeSessionId?: string | null;
  isLoadingSessions?: boolean;
  onSessionSelect?: (sessionId: string) => void;
}

export const ChatbotPanel = ({
  messages,
  isStreaming,
  error = null,
  suggestions = [],
  inputValue,
  onInputChange,
  onSend,
  onSuggestionSelect,
  onReset,
  onToggleExpand,
  isExpanded = false,
  plan = null,
  contextSummary = "",
  queryAnalysis = null,
  queryHistory = [],
  onApplyFilterSuggestion,
  onLogReferenceSelect,
  sessions = [],
  activeSessionId = null,
  isLoadingSessions = false,
  onSessionSelect,
}: ChatbotPanelProps) => {
  const hasInsights = useMemo(() => {
    if (!queryAnalysis) return false;
    return Boolean(
      queryAnalysis.summary ||
        (queryAnalysis.intents && queryAnalysis.intents.length > 0) ||
        (queryAnalysis.clarifyingQuestions && queryAnalysis.clarifyingQuestions.length > 0) ||
        (queryAnalysis.filterSuggestions && queryAnalysis.filterSuggestions.length > 0)
    );
  }, [queryAnalysis]);

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <ChatHeader
        isStreaming={isStreaming}
        isExpanded={isExpanded}
        onReset={onReset}
        sessions={sessions}
        activeSessionId={activeSessionId}
        isLoadingSessions={isLoadingSessions}
        onSessionSelect={onSessionSelect}
        onToggleExpand={onToggleExpand}
      />

      {error && (
        <div className="mx-4 mt-3 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-200">
          {error}
        </div>
      )}

      <div className="flex-1 min-h-0 px-4 py-4">
        <div className="h-full overflow-y-auto space-y-4 pr-2">
          <ChatMessageList
            messages={messages}
            isStreaming={isStreaming}
            onLogReferenceSelect={onLogReferenceSelect}
          />
          {(plan || (isStreaming && !plan) || hasInsights) && (
            <ChatPlanSummary
              plan={plan ?? null}
              contextSummary={contextSummary}
              isLoading={isStreaming && !plan}
              queryAnalysis={queryAnalysis}
              queryHistory={queryHistory}
              onApplyFilterSuggestion={onApplyFilterSuggestion}
            />
          )}
        </div>
      </div>

      <div className="px-4 pb-3">
        <ChatSuggestionBar
          suggestions={suggestions}
          onSelect={onSuggestionSelect}
          disabled={isStreaming}
        />
      </div>

      <div className="px-4 pb-4">
        <ChatComposer
          value={inputValue}
          onChange={onInputChange}
          onSend={onSend}
          isBusy={isStreaming}
        />
      </div>
    </div>
  );
};

export default ChatbotPanel;
