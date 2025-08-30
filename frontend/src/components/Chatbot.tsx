import { useState, useRef, useEffect } from "react";
import {
  MessageSquare,
  Send,
  Bot,
  User,
  History,
  Trash2,
  Wrench,
  Database,
} from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/Auth";
import axios from "axios";

type Message = {
  id: number;
  text: string;
  sender: "user" | "ai";
  timestamp: string;
  toolResults?: any;
  actions?: any[];
  needsClarification?: boolean;
  isStreaming?: boolean;
  streamingStep?: string;
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
          toolResults: msg.metadata?.toolResults || null,
          actions: msg.metadata?.actions || [],
          needsClarification: msg.metadata?.needsClarification || false,
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

    // Create a streaming AI response message
    const streamingMessageId = Date.now() + 1;
    const streamingMessage: Message = {
      id: streamingMessageId,
      text: "🔄 Starting intelligent analysis...",
      sender: "ai",
      timestamp: new Date().toLocaleTimeString(),
      toolResults: null,
      actions: [],
      needsClarification: false,
      isStreaming: true,
      streamingStep: "initialization",
    };

    setMessages((prev: Message[]) => [...prev, streamingMessage]);

    try {
      // Use the streaming endpoint
      const response = await fetch("/api/v1/agent/query/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: input,
          projectId,
          sessionId: currentSessionId,
          services: selectedServices,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body reader available");
      }

      const decoder = new TextDecoder();
      let buffer = "";
      let finalResult: any = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep the last incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6)); // Remove "data: " prefix

              switch (data.type) {
                case "status":
                  // Update the streaming message with status
                  setMessages((prev: Message[]) =>
                    prev.map((msg) =>
                      msg.id === streamingMessageId
                        ? {
                            ...msg,
                            text: `🔄 ${data.message}`,
                            streamingStep: data.step,
                          }
                        : msg
                    )
                  );
                  break;

                case "result":
                  // Final result received
                  finalResult = data.data;
                  setMessages((prev: Message[]) =>
                    prev.map((msg) =>
                      msg.id === streamingMessageId
                        ? {
                            ...msg,
                            text: finalResult.analysis || "",
                            toolResults: finalResult.toolResults || null,
                            actions: finalResult.actions || [],
                            needsClarification:
                              finalResult.needsClarification || false,
                            isStreaming: false,
                            streamingStep: "complete",
                          }
                        : msg
                    )
                  );
                  break;

                case "error":
                  // Error occurred
                  setMessages((prev: Message[]) =>
                    prev.map((msg) =>
                      msg.id === streamingMessageId
                        ? {
                            ...msg,
                            text: `❌ Error: ${data.message}`,
                            isStreaming: false,
                            streamingStep: "error",
                          }
                        : msg
                    )
                  );
                  toast.error(`Streaming error: ${data.message}`);
                  break;
              }
            } catch (parseError) {
              console.warn("Failed to parse streaming data:", parseError);
            }
          }
        }
      }

      // Store the session ID if this is a new session
      if (finalResult?.sessionId && !currentSessionId) {
        setCurrentSessionId(finalResult.sessionId);
      }

      // Reload sessions to get updated context
      await loadUserSessions();
    } catch (error: any) {
      console.error("Error generating AI response:", error);
      let errorMessage = "Failed to generate AI response";
      if (error.message) {
        errorMessage = `Network error: ${error.message}`;
      }

      // Update the streaming message with error
      setMessages((prev: Message[]) =>
        prev.map((msg) =>
          msg.id === streamingMessageId
            ? {
                ...msg,
                text: `❌ ${errorMessage}`,
                isStreaming: false,
                streamingStep: "error",
              }
            : msg
        )
      );

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

  const renderToolResults = (toolResults: any) => {
    if (!toolResults) return null;

    return (
      <div className="mt-3 space-y-3">
        {/* User Parameters */}
        {toolResults.user_parameters && (
          <div className="p-3 bg-blue-950/40 border border-blue-800/50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Database className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-medium text-blue-400">
                Search Parameters Used
              </span>
            </div>
            <div className="text-xs text-blue-300 space-y-1">
              {toolResults.user_parameters.search_query && (
                <div>Query: {toolResults.user_parameters.search_query}</div>
              )}
              {toolResults.user_parameters.resource_filters[
                "resource.type"
              ] && (
                <div>
                  Services:{" "}
                  {toolResults.user_parameters.resource_filters[
                    "resource.type"
                  ].join(", ")}
                </div>
              )}
              {toolResults.user_parameters.severity_filters &&
                toolResults.user_parameters.severity_filters.length > 0 && (
                  <div>
                    Severity:{" "}
                    {toolResults.user_parameters.severity_filters.join(", ")}
                  </div>
                )}
              {toolResults.user_parameters.time_range &&
                (toolResults.user_parameters.time_range.start_time ||
                  toolResults.user_parameters.time_range.end_time) && (
                  <div>
                    Time:{" "}
                    {toolResults.user_parameters.time_range.start_time || "any"}{" "}
                    to{" "}
                    {toolResults.user_parameters.time_range.end_time || "now"}
                  </div>
                )}
            </div>
          </div>
        )}

        {/* Fetched Logs */}
        {toolResults.fetched_logs && (
          <div className="p-3 bg-green-950/40 border border-green-800/50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Wrench className="w-4 h-4 text-green-400" />
              <span className="text-sm font-medium text-green-400">
                Logs Fetched
              </span>
            </div>
            <div className="text-xs text-green-300">
              <div>Total logs: {toolResults.fetched_logs.total_fetched}</div>
              <div>
                Filter applied: {toolResults.fetched_logs.filter_applied}
              </div>
            </div>
          </div>
        )}

        {/* Log Analysis */}
        {toolResults.log_analysis && (
          <div className="p-3 bg-purple-950/40 border border-purple-800/50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Wrench className="w-4 h-4 text-purple-400" />
              <span className="text-sm font-medium text-purple-400">
                Log Analysis Results
              </span>
            </div>
            <div className="text-xs text-purple-300 space-y-1">
              <div>Focus: {toolResults.log_analysis.analysis_focus}</div>
              <div>
                Total logs analyzed: {toolResults.log_analysis.total_logs}
              </div>
              {toolResults.log_analysis.severity_distribution && (
                <div>
                  Severity:{" "}
                  {Object.entries(
                    toolResults.log_analysis.severity_distribution
                  )
                    .map(([sev, count]) => `${sev}:${count}`)
                    .join(", ")}
                </div>
              )}
              {toolResults.log_analysis.key_insights && (
                <div>
                  Key insights: {toolResults.log_analysis.key_insights.length}{" "}
                  found
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderActions = (actions: any[]) => {
    if (!actions || actions.length === 0) return null;

    return (
      <div className="mt-3 space-y-2">
        <div className="text-xs text-gray-400 font-medium">
          Suggested Actions:
        </div>
        <div className="flex flex-wrap gap-2">
          {actions.map((action, index) => (
            <button
              key={index}
              className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-xs rounded-lg border border-blue-700/50 hover:border-blue-600/70 transition-all duration-200"
              onClick={() => {
                // Handle action clicks
                console.log("Action clicked:", action);
                toast.success(`Action: ${action.label}`);
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>
    );
  };

  const renderStreamingProgress = (message: Message) => {
    if (!message.isStreaming) return null;

    const getStepIcon = (step: string) => {
      switch (step) {
        case "initialization":
          return "🚀";
        case "intelligent_analysis":
          return "🧠";
        case "context_retrieval":
          return "🔍";
        case "log_fetching":
          return "📡";
        case "log_analysis":
          return "🤖";
        case "action_generation":
          return "⚡";
        case "completion":
          return "✅";
        default:
          return "🔄";
      }
    };

    const getStepDescription = (step: string) => {
      switch (step) {
        case "initialization":
          return "Initializing analysis...";
        case "intelligent_analysis":
          return "Analyzing your query...";
        case "context_retrieval":
          return "Discovering GCP resources...";
        case "log_fetching":
          return "Fetching logs from GCP...";
        case "log_analysis":
          return "AI analyzing logs...";
        case "action_generation":
          return "Generating suggestions...";
        case "completion":
          return "Finalizing results...";
        default:
          return "Processing...";
      }
    };

    return (
      <div className="mt-2 p-2 bg-blue-950/30 border border-blue-800/50 rounded-lg">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <span className="text-sm">
              {getStepIcon(message.streamingStep || "processing")}
            </span>
            <span className="text-xs text-blue-300 font-medium">
              {getStepDescription(message.streamingStep || "processing")}
            </span>
          </div>
          <div className="flex-1 h-1 bg-blue-900/50 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full animate-pulse"
              style={{ width: "60%" }}
            ></div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 border-b border-gray-800 px-4 py-3">
        <div className="flex items-center justify-between">
          <h3 className="text-white font-semibold flex items-center gap-2">
            <Bot className="w-5 h-5 text-blue-400" />
            AI Agent (Real-Time Streaming)
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
            <p className="text-sm">Ask me about your GCP logs!</p>
            <p className="text-xs mt-2">
              I'll help you fetch and analyze logs with real-time streaming
              updates
            </p>
            <p className="text-xs mt-1">
              Try: "Show me authentication errors from Cloud Run services in the
              last hour" or "Find performance issues in my GCE instances"
            </p>
            <div className="mt-3 p-3 bg-gray-800/40 rounded-lg border border-gray-700/50">
              <p className="text-xs text-gray-400 font-medium mb-2">
                Example patterns:
              </p>
              <div className="text-xs text-gray-500 space-y-1">
                <div>
                  • "Show me [search terms] from [services] in [time range]"
                </div>
                <div>
                  • "Find [severity] logs for [services] containing [keywords]"
                </div>
                <div>
                  • "Check [services] for [issues] between [start] and [end]"
                </div>
              </div>
            </div>
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

                {/* Clarification Needed Indicator */}
                {message.needsClarification && (
                  <div className="mt-2 p-2 bg-yellow-950/40 border border-yellow-800/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-yellow-400 font-medium">
                        Clarification Needed
                      </span>
                    </div>
                    <div className="text-xs text-yellow-300">
                      Please provide the missing information so I can help you
                      fetch the right logs.
                    </div>
                  </div>
                )}

                {/* Streaming Progress */}
                {renderStreamingProgress(message)}

                {/* Tool Results */}
                {message.toolResults && renderToolResults(message.toolResults)}

                {/* Actions */}
                {message.actions && renderActions(message.actions)}

                <p
                  className={`text-[10px] mt-1 ${
                    message.sender === "user"
                      ? "text-blue-100/80"
                      : "text-gray-400"
                  }`}
                >
                  {message.timestamp}
                </p>
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
              sending
                ? "AI is analyzing..."
                : "Specify search query, services, time range, and severity... (Enter to send)"
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
