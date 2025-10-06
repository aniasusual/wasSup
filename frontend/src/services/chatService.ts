import axios from "axios";
import toast from "react-hot-toast";

import type {
  ChatMessage,
  ChatMessageStatus,
  ChatSessionDetail,
  ChatSessionSummary,
} from "../types/chat";

export interface ChatTurnRequestPayload {
  message: string;
  sessionId?: string;
  projectId?: string;
  context?: Record<string, unknown>;
}

const withAuthHeaders = (token: string) => ({
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  },
});

const handleAuthErrors = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    if (status === 401 || status === 403) {
      toast.error("Session expired. Please log in again.");
      window.setTimeout(() => {
        window.location.replace("/login");
      }, 200);
    }
  }
};

const normalizeMessage = (message: unknown): ChatMessage | null => {
  if (!message || typeof message !== "object") {
    return null;
  }

  const record = message as Record<string, unknown>;
  const idValue = record.id;
  const id = typeof idValue === "string" && idValue.trim().length > 0 ? idValue : undefined;
  const role = record.role === "user" ? "user" : "assistant";
  const content = typeof record.content === "string" ? record.content : "";
  const timestamp =
    typeof record.timestamp === "string" ? record.timestamp : new Date().toISOString();
  const allowedStatuses: ChatMessageStatus[] = ["pending", "sent", "error"];
  const statusValue = record.status;
  const status: ChatMessageStatus =
    typeof statusValue === "string" && allowedStatuses.includes(statusValue as ChatMessageStatus)
      ? (statusValue as ChatMessageStatus)
      : "sent";
  const metadataValue = record.metadata;
  const metadata: Record<string, unknown> =
    typeof metadataValue === "object" && metadataValue !== null
      ? (metadataValue as Record<string, unknown>)
      : {};

  return {
    id: id ?? `${role}-${timestamp}`,
    role,
    content,
    timestamp,
    status,
    metadata,
  };
};

const normalizeSessionSummary = (item: unknown): ChatSessionSummary | null => {
  if (!item || typeof item !== "object") {
    return null;
  }

  const record = item as Record<string, unknown>;
  const sessionId = typeof record.sessionId === "string" ? record.sessionId : undefined;
  if (!sessionId) {
    return null;
  }

  return {
    sessionId,
    title:
      typeof record.title === "string"
        ? record.title
        : `Session ${sessionId.slice(-4).toUpperCase()}`,
    createdAt: typeof record.createdAt === "string" ? record.createdAt : undefined,
    updatedAt: typeof record.updatedAt === "string" ? record.updatedAt : undefined,
    lastMessagePreview:
      typeof record.lastMessagePreview === "string" ? record.lastMessagePreview : undefined,
  };
};

export const sendChatTurn = async (
  payload: ChatTurnRequestPayload,
  token: string
) => {
  try {
    const response = await axios.post(
      "/api/v1/conversations/respond",
      {
        message: payload.message,
        session_id: payload.sessionId,
        project_id: payload.projectId,
        context: payload.context ?? {},
      },
      withAuthHeaders(token)
    );

    return response.data;
  } catch (error) {
    handleAuthErrors(error);
    throw error;
  }
};

export const listChatSessions = async (token: string): Promise<ChatSessionSummary[]> => {
  try {
    const response = await axios.get("/api/v1/conversations/sessions", withAuthHeaders(token));
    const rawList = Array.isArray(response.data) ? response.data : [];
    return rawList
      .map((item) => normalizeSessionSummary(item))
      .filter((item): item is ChatSessionSummary => Boolean(item));
  } catch (error) {
    handleAuthErrors(error);
    throw error;
  }
};

export const fetchChatSession = async (
  sessionId: string,
  token: string
): Promise<ChatSessionDetail> => {
  try {
    const response = await axios.get(
      `/api/v1/conversations/sessions/${sessionId}`,
      withAuthHeaders(token)
    );

    const data = response.data ?? {};
    const summary = normalizeSessionSummary({
      sessionId: data.sessionId,
      title: data.title,
      createdAt: data.createdAt,
      updatedAt: data.updatedAt,
      lastMessagePreview: data.lastMessagePreview,
    });

    const messagesRaw = Array.isArray(data.messages) ? data.messages : [];
    const messages = messagesRaw
      .map((message: unknown) => normalizeMessage(message))
      .filter((message: ChatMessage | null): message is ChatMessage => Boolean(message));

    return {
      sessionId: summary?.sessionId ?? sessionId,
      title: summary?.title ?? `Session ${sessionId.slice(-4).toUpperCase()}`,
      createdAt: summary?.createdAt,
      updatedAt: summary?.updatedAt,
      lastMessagePreview: summary?.lastMessagePreview,
      messages,
    };
  } catch (error) {
    handleAuthErrors(error);
    throw error;
  }
};
