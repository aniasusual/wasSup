import axios from "axios";

import type {
  ChatRole,
  ChatTurnResponse,
  InvestigationPlan,
  InvestigationStep,
  QueryUnderstandingResult,
  QueryIntent,
  FilterSuggestion,
  QueryHistoryEntry,
} from "../types/chat";

export interface ChatTurnRequestPayload {
  message: string;
  sessionId?: string;
  projectId?: string;
  context?: Record<string, unknown>;
}

export const sendChatTurn = async (
  payload: ChatTurnRequestPayload,
  token: string
): Promise<ChatTurnResponse> => {
  const response = await axios.post(
    "/api/v1/conversations/respond",
    {
      message: payload.message,
      session_id: payload.sessionId,
      project_id: payload.projectId,
      context: payload.context ?? {},
    },
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    }
  );

  const data = response.data as {
    session_id: string;
    reply: {
      id: string;
      role: string;
      content: string;
      timestamp: string;
      metadata?: Record<string, unknown>;
    };
    plan: {
      focus: string;
      summary: string;
      steps: Array<{
        id: string;
        title: string;
        description: string;
        status: InvestigationStep["status"];
      }>;
      suggested_queries?: string[];
    };
    follow_up_questions?: string[];
    context_summary?: string;
    query_analysis?: RawQueryAnalysis | null;
    query_history?: RawQueryHistoryEntry[];
  };

  const plan: InvestigationPlan = {
    focus: data.plan.focus,
    summary: data.plan.summary,
    steps: data.plan.steps.map((step) => ({
      id: step.id,
      title: step.title,
      description: step.description,
      status: step.status,
    })),
    suggestedQueries: data.plan.suggested_queries ?? [],
  };

  return {
    sessionId: data.session_id,
    reply: {
      id: data.reply.id,
      role: data.reply.role as ChatRole,
      content: data.reply.content,
      timestamp: data.reply.timestamp,
      metadata: data.reply.metadata ?? {},
      status: "sent",
    },
    plan,
    followUpQuestions: data.follow_up_questions ?? [],
    contextSummary: data.context_summary ?? "",
    queryAnalysis: parseQueryAnalysis(data.query_analysis),
    queryHistory: parseQueryHistory(data.query_history),
  };
};

type RawQueryAnalysis = {
  summary?: string;
  intents?: Array<{
    description?: string;
    confidence?: number;
    service_hints?: string[];
  }>;
  clarifying_questions?: string[];
  filter_suggestions?: Array<{
    key?: string;
    value?: string;
    confidence?: number;
  }>;
};

const parseQueryAnalysis = (
  payload: RawQueryAnalysis | null | undefined
): QueryUnderstandingResult | null => {
  if (!payload) {
    return null;
  }

  const intents: QueryIntent[] = (payload.intents ?? [])
    .map((intent) => ({
      description: intent.description ?? "",
      confidence: intent.confidence ?? 0,
      serviceHints: intent.service_hints ?? [],
    }))
    .filter((intent) => intent.description.trim().length > 0);

  const filterSuggestions: FilterSuggestion[] = (payload.filter_suggestions ?? [])
    .map((suggestion) => ({
      key: suggestion.key ?? "",
      value: suggestion.value ?? "",
      confidence: suggestion.confidence ?? 0,
    }))
    .filter((suggestion) => suggestion.key.trim().length > 0 && suggestion.value.trim().length > 0);

  return {
    summary: payload.summary ?? null,
    intents,
    clarifyingQuestions: payload.clarifying_questions ?? [],
    filterSuggestions,
  };
};

type RawQueryHistoryEntry = {
  message_id?: string;
  analysis?: RawQueryAnalysis;
  generated_at?: string;
};

const parseQueryHistory = (
  entries: RawQueryHistoryEntry[] | undefined
): QueryHistoryEntry[] => {
  if (!entries || !entries.length) {
    return [];
  }

  return entries
    .map((entry) => {
      const analysis = parseQueryAnalysis(entry.analysis ?? null);
      if (!analysis) {
        return null;
      }
      return {
        messageId: entry.message_id ?? "",
        analysis,
        generatedAt: entry.generated_at,
      } as QueryHistoryEntry;
    })
    .filter((entry): entry is QueryHistoryEntry => Boolean(entry && entry.messageId));
};
