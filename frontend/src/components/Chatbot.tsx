import { useState, useRef, useEffect } from "react";
import { MessageSquare, Send, Bot, User, History, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/Auth";
import axios from "axios";

type Message = {
  id: number;
  text: string;
  sender: "user" | "ai";
  timestamp: string;
  relevantLogs?: any[];
  investigationPlan?: any;
};

type Session = {
  session_id: string;
  project_id: string;
  created_at: string;
  last_updated: string;
  message_count: number;
  context_summary: string;
};

export const Chatbot = ({
  selectedServices = [],
  projectId = "",
  onOpenInsight,
  openTabs = [],
  activeTabId = "",
  tabLogs = {},
  pendingSearch = { searchQuery: "", startDate: "", endDate: "" },
  logCount = 100,
}: any) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const { token } = useAuth();
  const [sending, setSending] = useState<boolean>(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showSessions, setShowSessions] = useState<boolean>(false);
  const listRef = useRef<HTMLDivElement | null>(null);

  // Load user sessions on component mount
  useEffect(() => {
    if (token) {
      loadUserSessions();
    }
  }, [token]);

  const loadUserSessions = async () => {
    try {
      const response = await axios.get("/api/v1/agent/sessions", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setSessions(response.data.sessions || []);
    } catch (error) {
      console.error("Error loading sessions:", error);
    }
  };

  const loadSessionHistory = async (sessionId: string) => {
    try {
      const response = await axios.get(
        `/api/v1/agent/sessions/${sessionId}/history`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const history = response.data.history || [];
      const formattedMessages: Message[] = history.map(
        (msg: any, index: number) => ({
          id: index,
          text: msg.content,
          sender: msg.role === "user" ? "user" : "ai",
          timestamp: new Date(msg.timestamp).toLocaleTimeString(),
          relevantLogs: msg.metadata?.relevantLogs || [],
        })
      );

      setMessages(formattedMessages);
      setCurrentSessionId(sessionId);
      setShowSessions(false);
    } catch (error) {
      console.error("Error loading session history:", error);
      toast.error("Failed to load session history");
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await axios.delete(`/api/v1/agent/sessions/${sessionId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }

      await loadUserSessions();
      toast.success("Session deleted");
    } catch (error) {
      console.error("Error deleting session:", error);
      toast.error("Failed to delete session");
    }
  };

  const startNewSession = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setShowSessions(false);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    if (sending) return;

    const newMessage: Message = {
      id: Date.now(),
      text: input,
      sender: "user",
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev: Message[]) => [...prev, newMessage]);
    setInput("");
    setIsTyping(true);
    setSending(true);

    try {
      // Prepare tab context for the agent
      const tabContext = {
        openTabs: openTabs.map((tab: any) => ({
          id: tab.id,
          title: tab.title,
          serviceId: tab.serviceId,
          filters: tab.filters,
          query: tab.query,
          type: tab.type,
          logCount: tabLogs[tab.id]?.length || 0,
        })),
        activeTabId,
        globalFilters: {
          searchQuery: pendingSearch.searchQuery,
          startDate: pendingSearch.startDate,
          endDate: pendingSearch.endDate,
          logCount,
        },
      };

      const response = await axios.post(
        "/api/v1/agent/query",
        {
          question: input,
          projectId,
          sessionId: currentSessionId, // Include session ID for context
          services: selectedServices,
          tabContext, // Send tab context to the agent
        },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = response.data;

      // Store the session ID if this is a new session
      if (data.sessionId && !currentSessionId) {
        setCurrentSessionId(data.sessionId);
      }

      const aiResponse: Message = {
        id: Date.now() + 1,
        text: data.analysis || "",
        sender: "ai",
        timestamp: new Date().toLocaleTimeString(),
        relevantLogs: data.relevantLogs || [],
        investigationPlan: data.investigationPlan || null,
      };

      setMessages((prev: Message[]) => [...prev, aiResponse]);

      // Reload sessions to get updated context
      await loadUserSessions();
    } catch (error: any) {
      console.error("Error generating AI response:", error);
      let errorMessage = "Failed to generate AI response";
      if (error.response?.data?.detail) {
        errorMessage = `AI response error: ${error.response.data.detail}`;
      } else if (error.response?.status) {
        errorMessage = `AI response error: ${error.response.status} - ${
          error.response.statusText || "Unknown error"
        }`;
      } else if (error.message) {
        errorMessage = `Network error: ${error.message}`;
      } else {
        errorMessage = `Unknown error: ${String(error)}`;
      }
      toast.error(errorMessage);
    } finally {
      setIsTyping(false);
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  };

  useEffect(() => {
    const el = listRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, isTyping]);

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 border-b border-gray-800 px-4 py-3">
        <div className="flex items-center justify-between">
          <h3 className="text-white font-semibold flex items-center gap-2">
            <Bot className="w-5 h-5 text-blue-400" />
            AI Assistant
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSessions(!showSessions)}
              className="p-1.5 rounded-lg hover:bg-gray-800 transition-colors"
              title="Session History"
            >
              <History className="w-4 h-4 text-gray-400" />
            </button>
            <span className="text-[10px] uppercase tracking-wider text-gray-400">
              Model
            </span>
            <span className="px-2 py-0.5 rounded-full text-[11px] bg-blue-900/40 text-blue-300 border border-blue-800">
              Gemini 1.5 Flash
            </span>
          </div>
        </div>

        {/* Session Management Panel */}
        {showSessions && (
          <div className="mt-3 p-3 bg-gray-950/60 rounded-lg border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-300">
                Conversation Sessions
              </h4>
              <button
                onClick={startNewSession}
                className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                New Session
              </button>
            </div>

            {sessions.length === 0 ? (
              <p className="text-xs text-gray-500">No active sessions</p>
            ) : (
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {sessions.map((session) => (
                  <div
                    key={session.session_id}
                    className={`flex items-center justify-between p-2 rounded border cursor-pointer transition-colors ${
                      currentSessionId === session.session_id
                        ? "bg-blue-900/40 border-blue-700"
                        : "bg-gray-900/40 border-gray-700 hover:bg-gray-800/40"
                    }`}
                  >
                    <div
                      className="flex-1 min-w-0"
                      onClick={() => loadSessionHistory(session.session_id)}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">
                          {new Date(session.last_updated).toLocaleDateString()}
                        </span>
                        <span className="text-xs text-gray-500">
                          {session.message_count} messages
                        </span>
                      </div>
                      <p className="text-xs text-gray-300 truncate">
                        {session.context_summary || "No context"}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSession(session.session_id);
                      }}
                      className="p-1 text-gray-500 hover:text-red-400 transition-colors"
                      title="Delete session"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div
        ref={listRef}
        className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4 bg-gray-950/30"
      >
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-700" />
            <p className="text-sm">Ask me about your logs!</p>
            <p className="text-xs mt-2">
              Try: "Show me all errors in the last hour"
            </p>
            {currentSessionId && (
              <p className="text-xs mt-1 text-blue-400">
                Continuing conversation session
              </p>
            )}
          </div>
        )}

        {messages.map((message: Message) => (
          <div
            key={message.id}
            className={`flex ${
              message.sender === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div className="flex items-start gap-2 max-w-[80%]">
              {message.sender === "ai" ? (
                <div className="flex-shrink-0 w-7 h-7 rounded-full bg-blue-900/40 border border-blue-800 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-blue-300" />
                </div>
              ) : (
                <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center">
                  <User className="w-4 h-4 text-gray-300" />
                </div>
              )}
              <div
                className={`rounded-2xl px-4 py-2 border ${
                  message.sender === "user"
                    ? "bg-blue-600 text-white border-blue-500"
                    : "bg-gray-900 text-gray-200 border-gray-800"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap leading-relaxed">
                  {message.text}
                </p>

                {/* Investigation Plan Indicator */}
                {message.investigationPlan && (
                  <div className="mt-2 p-2 bg-blue-950/40 border border-blue-800/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-blue-400 font-medium">
                        Investigation Plan
                      </span>
                    </div>
                    <div className="text-xs text-blue-300">
                      <div>
                        <strong>Approach:</strong>{" "}
                        {message.investigationPlan.approach}
                      </div>
                      <div>
                        <strong>Reason:</strong>{" "}
                        {message.investigationPlan.reason}
                      </div>
                      {message.investigationPlan.suggested_question && (
                        <div className="mt-1 text-blue-200">
                          <strong>Question:</strong>{" "}
                          {message.investigationPlan.suggested_question}
                        </div>
                      )}
                    </div>
                  </div>
                )}
                <p
                  className={`text-[10px] mt-1 ${
                    message.sender === "user"
                      ? "text-blue-100/80"
                      : "text-gray-400"
                  }`}
                >
                  {message.timestamp}
                </p>
                {message.sender === "ai" &&
                  message.relevantLogs &&
                  message.relevantLogs.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                        <p className="text-xs text-purple-400 font-medium">
                          AI-Recommended Logs
                        </p>
                        <span className="text-xs text-gray-500">
                          ({message.relevantLogs.length} found)
                        </span>
                      </div>
                      <div className="grid grid-cols-1 gap-2">
                        {message.relevantLogs
                          .slice(0, 8)
                          .map((log: any, index: number) => (
                            <button
                              key={log.id}
                              className="group text-left p-3 rounded-lg bg-gradient-to-r from-purple-950/40 to-blue-950/40 hover:from-purple-900/60 hover:to-blue-900/60 border border-purple-800/50 hover:border-purple-600/70 transition-all duration-200 relative overflow-hidden"
                              onClick={() =>
                                onOpenInsight &&
                                onOpenInsight({
                                  sourceMessageId: message.id,
                                  log,
                                })
                              }
                              title="Open in AI Insight tab"
                            >
                              {/* Glow effect on hover */}
                              <div className="absolute inset-0 bg-gradient-to-r from-purple-500/0 to-blue-500/0 group-hover:from-purple-500/10 group-hover:to-blue-500/10 transition-all duration-300"></div>

                              <div className="relative z-10">
                                <div className="flex items-center justify-between gap-2 mb-2">
                                  <div className="flex items-center gap-2">
                                    <span
                                      className={`px-2 py-1 rounded-full text-[10px] font-semibold ${
                                        (log.severity || "INFO") === "ERROR"
                                          ? "bg-red-600 text-white shadow-lg"
                                          : (log.severity || "INFO") ===
                                            "WARNING"
                                          ? "bg-yellow-600 text-white shadow-lg"
                                          : (log.severity || "INFO") === "INFO"
                                          ? "bg-blue-600 text-white shadow-lg"
                                          : "bg-gray-600 text-white shadow-lg"
                                      }`}
                                    >
                                      {log.severity || "INFO"}
                                    </span>
                                    {log.serviceId && (
                                      <span className="text-purple-300 text-xs font-medium bg-purple-900/40 px-2 py-1 rounded">
                                        {log.serviceId}
                                      </span>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-1">
                                    <span className="text-gray-400 text-xs">
                                      {log.timestamp}
                                    </span>
                                    {log.score && (
                                      <span className="text-purple-400 text-xs bg-purple-900/40 px-1.5 py-0.5 rounded">
                                        {Math.round(log.score * 100)}% match
                                      </span>
                                    )}
                                  </div>
                                </div>
                                <div className="text-gray-200 text-sm line-clamp-2 group-hover:text-white transition-colors">
                                  {log.messageSnippet}
                                </div>
                                {log.traceId && (
                                  <div className="mt-2 flex items-center gap-1">
                                    <span className="text-purple-400 text-xs">
                                      🔗 Trace:
                                    </span>
                                    <span className="text-gray-400 text-xs font-mono">
                                      {log.traceId.slice(0, 8)}...
                                    </span>
                                  </div>
                                )}
                              </div>

                              {/* Click indicator */}
                              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <div className="w-2 h-2 bg-purple-400 rounded-full animate-ping"></div>
                              </div>
                            </button>
                          ))}
                      </div>
                      {message.relevantLogs.length > 8 && (
                        <p className="text-xs text-gray-500 text-center">
                          Showing top 8 of {message.relevantLogs.length}{" "}
                          relevant logs
                        </p>
                      )}
                    </div>
                  )}
              </div>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex items-center gap-2">
            <div className="flex-shrink-0 w-7 h-7 rounded-full bg-blue-900/40 border border-blue-800 flex items-center justify-center">
              <Bot className="w-4 h-4 text-blue-300" />
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-2xl px-4 py-2">
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" />
                <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce [animation-delay:120ms]" />
                <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce [animation-delay:240ms]" />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-gray-800 p-3">
        <div className="flex items-center gap-2 bg-gray-900 border border-gray-800 rounded-xl px-3 py-2 focus-within:border-blue-700/60">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              sending ? "Analyzing…" : "Ask about your logs… (Enter to send)"
            }
            className="flex-1 px-2 py-2 bg-transparent text-white placeholder-gray-500 focus:outline-none"
            disabled={sending}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || sending}
            className={`inline-flex items-center justify-center px-3 py-2 rounded-lg transition-colors ${
              !input.trim() || sending
                ? "bg-gray-800 text-gray-500 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700"
            }`}
            title="Send"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};
