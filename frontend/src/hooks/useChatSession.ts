import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useAuth } from "../contexts/Auth";
import { sendChatTurn } from "../services/chatService";
import type {
  ChatMessage,
  ChatSuggestion,
  ChatTurnResponse,
  InvestigationPlan,
  QueryUnderstandingResult,
  QueryHistoryEntry,
} from "../types/chat";

export interface UseChatSessionConfig {
  projectId?: string;
  baseContext?: Record<string, unknown>;
}

export interface SendMessageOptions {
  context?: Record<string, unknown>;
  projectId?: string;
}

type UseChatSessionResult = {
  sessionId: string | null;
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  suggestions: ChatSuggestion[];
  lastPlan: InvestigationPlan | null;
  contextSummary: string;
  queryAnalysis: QueryUnderstandingResult | null;
  queryHistory: QueryHistoryEntry[];
  sendMessage: (content: string, options?: SendMessageOptions) => Promise<void>;
  runSuggestion: (prompt: string, options?: SendMessageOptions) => Promise<void>;
  resetChat: () => void;
};

const defaultSuggestions: ChatSuggestion[] = [
  {
    id: "suggestion-architecture",
    label: "Service health",
    prompt: "Tell me what are the errors in cloud run in last 1 minute",
  },
  {
    id: "suggestion-latency",
    label: "Latency spike",
    prompt: "Why did API latency spike in the last 30 minutes?",
  },
  {
    id: "suggestion-deploy",
    label: "Recent deploy",
    prompt: "Did the last deploy introduce new errors?",
  },
];

const createMessageId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;

const buildIntroMessage = (): ChatMessage => ({
  id: "intro-1",
  role: "assistant",
  content:
    "Hi there! I can help you investigate issues across your projects. Tell me what you're seeing and I'll pull the right log views for you.",
  timestamp: new Date().toISOString(),
  status: "sent",
  metadata: {},
});

const toSuggestionLabel = (text: string, index: number) => {
  const trimmed = text.trim();
  if (trimmed.length <= 40) {
    return trimmed;
  }
  return `${trimmed.slice(0, 37)}… (${index + 1})`;
};

const extractStructuredReply = (rawContent: string) => {
  const fencePattern = /```json\s*([\s\S]*?)```/i;
  const match = fencePattern.exec(rawContent);

  if (!match) {
    return {
      markdown: rawContent.trim(),
      json: null as string | null,
    };
  }

  const jsonContent = match[1].trim();
  const before = rawContent.slice(0, match.index).trim();
  const after = rawContent.slice(match.index + match[0].length).trim();
  const markdown = [before, after].filter(Boolean).join("\n\n");

  return {
    markdown,
    json: jsonContent,
  };
};

const mapReplyToMessage = (reply: ChatTurnResponse["reply"]): ChatMessage => {
  const { markdown, json } = extractStructuredReply(reply.content);
  const metadata: Record<string, unknown> = {
    ...(reply.metadata ?? {}),
    rawContent: reply.content,
  };

  if (markdown && markdown !== reply.content) {
    metadata.markdown = markdown;
  }

  if (json) {
    metadata.jsonPayload = json;
  }

  return {
    id: reply.id,
    role: reply.role,
    content: markdown,
    timestamp: reply.timestamp,
    status: reply.status ?? "sent",
    metadata,
  };
};

export const useChatSession = (
  config: UseChatSessionConfig = {}
): UseChatSessionResult => {
  const { token, forceLogout } = useAuth();

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([buildIntroMessage()]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<ChatSuggestion[]>(defaultSuggestions);
  const [lastPlan, setLastPlan] = useState<InvestigationPlan | null>(null);
  const [contextSummary, setContextSummary] = useState<string>("");
  const [queryAnalysis, setQueryAnalysis] = useState<QueryUnderstandingResult | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryHistoryEntry[]>([]);

  const projectIdRef = useRef<string | undefined>(config.projectId);
  const baseContextRef = useRef<Record<string, unknown>>(config.baseContext ?? {});

  useEffect(() => {
    projectIdRef.current = config.projectId;
  }, [config.projectId]);

  useEffect(() => {
    baseContextRef.current = config.baseContext ?? {};
  }, [config.baseContext]);

  const appendMessages = useCallback((newMessages: ChatMessage[]) => {
    setMessages((prev) => [...prev, ...newMessages]);
  }, []);

  const updateMessageById = useCallback(
    (messageId: string, updater: (message: ChatMessage) => ChatMessage) => {
      setMessages((prev) =>
        prev.map((message) => (message.id === messageId ? updater(message) : message))
      );
    },
    []
  );

  const effectiveSuggestions = useMemo(() => suggestions, [suggestions]);

  const sendMessage = useCallback(
    async (content: string, options?: SendMessageOptions) => {
      const trimmed = content.trim();
      if (!trimmed || isStreaming) {
        return;
      }

      if (!token) {
        setError("You must be signed in to chat with the investigation assistant.");
        return;
      }

      const effectiveProjectId = sessionId
        ? undefined
        : options?.projectId ?? projectIdRef.current;

      if (!sessionId && !effectiveProjectId) {
        setError("Select a project to anchor the investigation before chatting.");
        return;
      }

      const effectiveContext = {
        ...baseContextRef.current,
        ...(options?.context ?? {}),
      };

      const userMessage: ChatMessage = {
        id: createMessageId(),
        role: "user",
        content: trimmed,
        timestamp: new Date().toISOString(),
        status: "sent",
        metadata: { context: effectiveContext },
      };

      const assistantMessageId = createMessageId();

      const pendingAssistant: ChatMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
        status: "pending",
        metadata: {},
      };

      appendMessages([userMessage, pendingAssistant]);
      setIsStreaming(true);
      setError(null);


      try {
        const response = await sendChatTurn(
          {
            message: trimmed,
            sessionId: sessionId ?? undefined,
            projectId: effectiveProjectId,
            context: effectiveContext,
          },
          token
        );
        console.log("Sending chat turn response", response);

        updateMessageById(assistantMessageId, () => mapReplyToMessage(response));
      } catch (err: unknown) {
        const detail =
          err instanceof Error ? err.message : "Unexpected error contacting the assistant.";

        if (detail.toLowerCase().includes("401")) {
          forceLogout("Session expired. Please sign in again.");
        }

        setError(detail);
        updateMessageById(assistantMessageId, (message) => ({
          ...message,
          content: detail,
          status: "error",
          timestamp: new Date().toISOString(),
        }));
      } finally {
        setIsStreaming(false);
      }
    },
    [appendMessages, forceLogout, isStreaming, sessionId, token, updateMessageById]
  );

  const runSuggestion = useCallback(
    async (prompt: string, options?: SendMessageOptions) => {
      await sendMessage(prompt, options);
    },
    [sendMessage]
  );

  const resetChat = useCallback(() => {
    setMessages([buildIntroMessage()]);
    setSessionId(null);
    setIsStreaming(false);
    setError(null);
    setSuggestions(defaultSuggestions);
    setLastPlan(null);
    setContextSummary("");
    setQueryAnalysis(null);
    setQueryHistory([]);
  }, []);

  return {
    sessionId,
    messages,
    isStreaming,
    error,
    suggestions: effectiveSuggestions,
    lastPlan,
    contextSummary,
    queryAnalysis,
    queryHistory,
    sendMessage,
    runSuggestion,
    resetChat,
  };
};

export default useChatSession;
