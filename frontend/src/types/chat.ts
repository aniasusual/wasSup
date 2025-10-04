export type ChatRole = "user" | "assistant" | "system" | "tool";

export type ChatMessageStatus = "pending" | "sent" | "error";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  status?: ChatMessageStatus;
  metadata?: Record<string, unknown>;
}

export interface ChatSuggestion {
  id: string;
  label: string;
  prompt: string;
}

export interface ChatLogReference {
  id?: string;
  service_type?: string;
  service_name?: string;
  description?: string;
  severity?: string;
  count?: number;
  pages_analyzed?: number;
  filter?: string;
  summary?: string;
  time_range?: {
    start?: string;
    end?: string;
  };
}

export interface ChatSessionState {
  messages: ChatMessage[];
  isStreaming: boolean;
  error?: string | null;
}

export type InvestigationStepStatus = "pending" | "in_progress" | "complete";

export interface InvestigationStep {
  id: string;
  title: string;
  description: string;
  status: InvestigationStepStatus;
}

export interface InvestigationPlan {
  focus: string;
  summary: string;
  steps: InvestigationStep[];
  suggestedQueries: string[];
}

export interface ChatTurnResponse {
  sessionId: string;
  reply: ChatMessage;
  plan: InvestigationPlan;
  followUpQuestions: string[];
  contextSummary: string;
  queryAnalysis?: QueryUnderstandingResult | null;
  queryHistory: QueryHistoryEntry[];
}

export interface QueryIntent {
  description: string;
  confidence: number;
  serviceHints: string[];
}

export interface FilterSuggestion {
  key: string;
  value: string;
  confidence: number;
}

export interface QueryUnderstandingResult {
  summary?: string | null;
  intents: QueryIntent[];
  clarifyingQuestions: string[];
  filterSuggestions: FilterSuggestion[];
}

export interface QueryHistoryEntry {
  messageId: string;
  analysis: QueryUnderstandingResult;
  generatedAt?: string;
}
