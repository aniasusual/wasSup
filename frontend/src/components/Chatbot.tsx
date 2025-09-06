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
  Maximize2,
  Minimize2,
  Sparkles,
  Zap,
  Brain,
  Search,
  Filter,
} from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/Auth";
import axios from "axios";
import { RichTextRenderer } from "./RichTextRenderer";

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
  streamingProgress?: { page: number; totalLogs: number };
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
  projectArchitecture = "",
  onOpenInsight = () => {}, // For future use when implementing insight tabs
  isExpanded = false,
  onToggleExpand,
}: any) => {
  // Suppress unused parameter warning for future use
  void onOpenInsight;
  void projectArchitecture; // Will be used for AI context in future
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
                            // Store additional progress data if available
                            streamingProgress: data.page
                              ? { page: data.page, totalLogs: data.total_logs }
                              : undefined,
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
                <div>
                  Query:{" "}
                  <code className="bg-blue-900/30 px-1 rounded">
                    {toolResults.user_parameters.search_query}
                  </code>
                </div>
              )}
              {toolResults.user_parameters.resource_filters?.[
                "resource.type"
              ] && (
                <div>
                  Services:{" "}
                  <span className="inline-flex flex-wrap gap-1">
                    {toolResults.user_parameters.resource_filters[
                      "resource.type"
                    ].map((service: string, index: number) => (
                      <span
                        key={index}
                        className="px-1.5 py-0.5 bg-blue-900/30 rounded text-xs"
                      >
                        {service}
                      </span>
                    ))}
                  </span>
                </div>
              )}
              {toolResults.user_parameters.severity_filters &&
                toolResults.user_parameters.severity_filters.length > 0 && (
                  <div>
                    Severity:{" "}
                    <span className="inline-flex flex-wrap gap-1">
                      {toolResults.user_parameters.severity_filters.map(
                        (severity: string, index: number) => (
                          <span
                            key={index}
                            className={`px-1.5 py-0.5 rounded text-xs ${
                              severity === "ERROR"
                                ? "bg-red-900/30 text-red-300"
                                : severity === "WARNING"
                                ? "bg-yellow-900/30 text-yellow-300"
                                : severity === "INFO"
                                ? "bg-blue-900/30 text-blue-300"
                                : "bg-gray-900/30 text-gray-300"
                            }`}
                          >
                            {severity}
                          </span>
                        )
                      )}
                    </span>
                  </div>
                )}
              {toolResults.user_parameters.time_range &&
                (toolResults.user_parameters.time_range.start_time ||
                  toolResults.user_parameters.time_range.end_time) && (
                  <div>
                    Time:{" "}
                    <code className="bg-blue-900/30 px-1 rounded">
                      {toolResults.user_parameters.time_range.start_time ||
                        "any"}{" "}
                      to{" "}
                      {toolResults.user_parameters.time_range.end_time || "now"}
                    </code>
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
            <div className="text-xs text-green-300 space-y-1">
              <div className="flex items-center gap-2">
                <span>Total logs:</span>
                <span className="px-2 py-0.5 bg-green-900/30 rounded font-mono">
                  {toolResults.fetched_logs.total_fetched}
                </span>
              </div>
              <div>
                Filter applied:{" "}
                <code className="bg-green-900/30 px-1 rounded text-xs">
                  {toolResults.fetched_logs.filter_applied?.substring(0, 100)}
                  {toolResults.fetched_logs.filter_applied?.length > 100
                    ? "..."
                    : ""}
                </code>
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
            <div className="text-xs text-purple-300 space-y-2">
              <div className="flex items-center gap-2">
                <span>Focus:</span>
                <span className="px-2 py-0.5 bg-purple-900/30 rounded">
                  {toolResults.log_analysis.analysis_focus}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span>Total logs analyzed:</span>
                <span className="px-2 py-0.5 bg-purple-900/30 rounded font-mono">
                  {toolResults.log_analysis.total_logs}
                </span>
              </div>
              {toolResults.log_analysis.severity_distribution && (
                <div>
                  <span className="block mb-1">Severity Distribution:</span>
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(
                      toolResults.log_analysis.severity_distribution
                    ).map(([sev, count]) => (
                      <span
                        key={sev}
                        className={`px-2 py-0.5 rounded text-xs ${
                          sev === "ERROR"
                            ? "bg-red-900/30 text-red-300"
                            : sev === "WARNING"
                            ? "bg-yellow-900/30 text-yellow-300"
                            : sev === "INFO"
                            ? "bg-blue-900/30 text-blue-300"
                            : "bg-gray-900/30 text-gray-300"
                        }`}
                      >
                        {sev}: {String(count)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {toolResults.log_analysis.key_insights && (
                <div className="flex items-center gap-2">
                  <span>Key insights:</span>
                  <span className="px-2 py-0.5 bg-purple-900/30 rounded font-mono">
                    {toolResults.log_analysis.key_insights.length} found
                  </span>
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
        case "log_fetching_progress":
          return "📊";
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
        case "log_fetching_progress":
          return "Comprehensive log fetch in progress...";
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
          {message.streamingProgress && (
            <div className="text-xs text-blue-400 ml-2">
              Page {message.streamingProgress.page} •{" "}
              {message.streamingProgress.totalLogs.toLocaleString()} logs
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Modern Header with Glassmorphism */}
      <div className="bg-gradient-to-r from-slate-900/95 via-slate-800/95 to-slate-900/95 backdrop-blur-xl border-b border-slate-700/50 px-6 py-4 shadow-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-slate-900 animate-pulse"></div>
            </div>
            <div>
              <h3 className="text-white font-bold text-lg flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-400" />
                AI Log Analyst
              </h3>
              <p className="text-slate-400 text-sm">
                Real-time streaming analysis
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Model Badge */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/60 backdrop-blur-sm rounded-full border border-slate-700/50">
              <Zap className="w-3 h-3 text-yellow-400" />
              <span className="text-xs font-medium text-slate-300">
                Gemini 1.5 Flash
              </span>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowSessions(!showSessions)}
                className="p-2 rounded-xl bg-slate-800/60 hover:bg-slate-700/60 border border-slate-700/50 hover:border-slate-600/50 transition-all duration-200 group"
                title="Session History"
              >
                <History className="w-4 h-4 text-slate-400 group-hover:text-slate-300 transition-colors" />
              </button>

              {onToggleExpand && (
                <button
                  onClick={onToggleExpand}
                  className="p-2 rounded-xl bg-slate-800/60 hover:bg-slate-700/60 border border-slate-700/50 hover:border-slate-600/50 transition-all duration-200 group"
                  title={isExpanded ? "Minimize" : "Expand"}
                >
                  {isExpanded ? (
                    <Minimize2 className="w-4 h-4 text-slate-400 group-hover:text-slate-300 transition-colors" />
                  ) : (
                    <Maximize2 className="w-4 h-4 text-slate-400 group-hover:text-slate-300 transition-colors" />
                  )}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Modern Session Management Panel */}
        {showSessions && (
          <div className="mt-4 p-4 bg-slate-800/40 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-blue-400" />
                Conversation Sessions
              </h4>
              <button
                onClick={startNewSession}
                className="px-3 py-1.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white text-xs font-medium rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                + New Session
              </button>
            </div>

            {sessions.length === 0 ? (
              <div className="text-center py-6">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                <p className="text-sm text-slate-500">No active sessions</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-48 overflow-y-auto">
                {sessions.map((session) => (
                  <div
                    key={session.session_id}
                    className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all duration-200 ${
                      currentSessionId === session.session_id
                        ? "bg-blue-500/20 border-blue-500/50 shadow-lg"
                        : "bg-slate-700/40 border-slate-600/50 hover:bg-slate-700/60 hover:border-slate-500/50"
                    }`}
                  >
                    <div
                      className="flex-1 min-w-0"
                      onClick={() => loadSessionHistory(session.session_id)}
                    >
                      <div className="flex items-center gap-3 mb-1">
                        <span className="text-xs text-slate-400 font-medium">
                          {new Date(session.last_updated).toLocaleDateString()}
                        </span>
                        <div className="flex items-center gap-1 px-2 py-0.5 bg-slate-600/50 rounded-full">
                          <span className="text-xs text-slate-300">
                            {session.message_count} messages
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-slate-200 truncate font-medium">
                        {session.context_summary || "No context available"}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSession(session.session_id);
                      }}
                      className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all duration-200"
                      title="Delete session"
                    >
                      <Trash2 className="w-4 h-4" />
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
        className="flex-1 min-h-0 overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-slate-900/50 to-slate-950/50"
      >
        {messages.length === 0 && (
          <div className="text-center text-slate-400 mt-12">
            <div className="relative mb-6">
              <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-600/20 backdrop-blur-sm border border-slate-700/50 flex items-center justify-center">
                <Brain className="w-10 h-10 text-blue-400" />
              </div>
              <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full border-2 border-slate-900 animate-pulse"></div>
            </div>

            <h3 className="text-lg font-semibold text-slate-200 mb-2">
              Welcome to AI Log Analyst
            </h3>
            <p className="text-sm text-slate-400 mb-4 max-w-md mx-auto">
              I'll help you fetch and analyze logs with real-time streaming
              updates and intelligent insights. I can now provide **rich text**
              responses with:
            </p>
            <div className="text-xs text-slate-500 mb-4 max-w-md mx-auto text-left">
              • **Bold** and *italic* formatting
              <br />
              • `Inline code` and code blocks
              <br />
              • Structured data visualization
              <br />
              • Interactive log entries
              <br />• Collapsible sections
            </div>

            <div className="mt-6 p-4 bg-slate-800/40 backdrop-blur-sm rounded-2xl border border-slate-700/50 max-w-lg mx-auto">
              <p className="text-sm text-slate-300 font-medium mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-yellow-400" />
                Try these example queries:
              </p>
              <div className="text-sm text-slate-400 space-y-2 text-left">
                <div className="p-2 bg-slate-700/30 rounded-lg border border-slate-600/30">
                  <span className="text-blue-400">
                    "Show me **authentication errors** from `cloud_run_revision`
                    services in the last hour"
                  </span>
                </div>
                <div className="p-2 bg-slate-700/30 rounded-lg border border-slate-600/30">
                  <span className="text-green-400">
                    "Find *performance issues* in my `gce_instance` logs"
                  </span>
                </div>
                <div className="p-2 bg-slate-700/30 rounded-lg border border-slate-600/30">
                  <span className="text-purple-400">
                    "Check for **5xx errors** in my load balancer logs"
                  </span>
                </div>
              </div>
            </div>

            {currentSessionId && (
              <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl max-w-md mx-auto">
                <p className="text-sm text-blue-300 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Continuing conversation session
                </p>
              </div>
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
            <div className="flex items-start gap-3 max-w-[85%]">
              {message.sender === "ai" ? (
                <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 border border-blue-400/50 flex items-center justify-center shadow-lg">
                  <Brain className="w-4 h-4 text-white" />
                </div>
              ) : (
                <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-br from-slate-600 to-slate-700 border border-slate-500/50 flex items-center justify-center shadow-lg">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
              <div
                className={`rounded-2xl px-5 py-3 border backdrop-blur-sm shadow-lg ${
                  message.sender === "user"
                    ? "bg-gradient-to-br from-blue-600 to-blue-700 text-white border-blue-500/50"
                    : "bg-slate-800/80 text-slate-200 border-slate-700/50"
                }`}
              >
                {message.sender === "ai" ? (
                  <div className="text-sm leading-relaxed">
                    <RichTextRenderer content={message.text} />
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">
                    {message.text}
                  </p>
                )}

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

      <div className="border-t border-slate-700/50 p-6 bg-slate-900/50 backdrop-blur-sm">
        <div className="flex items-center gap-3 bg-slate-800/60 border border-slate-700/50 rounded-2xl px-4 py-3 focus-within:border-blue-500/50 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all duration-200 shadow-lg">
          <div className="flex-shrink-0">
            <Search className="w-5 h-5 text-slate-400" />
          </div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              sending
                ? "AI is analyzing your query..."
                : "Ask about your GCP logs, services, time ranges, or specific issues... (Enter to send)"
            }
            className="flex-1 bg-transparent text-slate-200 placeholder-slate-500 focus:outline-none text-sm"
            disabled={sending}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || sending}
            className={`inline-flex items-center justify-center px-4 py-2 rounded-xl transition-all duration-200 shadow-lg ${
              !input.trim() || sending
                ? "bg-slate-700/50 text-slate-500 cursor-not-allowed"
                : "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white hover:shadow-xl transform hover:scale-105"
            }`}
            title="Send message"
          >
            {sending ? (
              <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Quick Action Buttons */}
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() =>
              setInput(
                "Show me **ERROR** logs from `cloud_run_revision` services in the last hour"
              )
            }
            className="px-3 py-1.5 text-xs bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 rounded-lg border border-slate-600/50 transition-all duration-200"
          >
            <Filter className="w-3 h-3 inline mr-1" />
            Recent Errors
          </button>
          <button
            onClick={() =>
              setInput("Find *performance issues* in my `gce_instance` logs")
            }
            className="px-3 py-1.5 text-xs bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 rounded-lg border border-slate-600/50 transition-all duration-200"
          >
            <Zap className="w-3 h-3 inline mr-1" />
            Performance
          </button>
          <button
            onClick={() =>
              setInput(
                "Check for **authentication failures** across all services"
              )
            }
            className="px-3 py-1.5 text-xs bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 rounded-lg border border-slate-600/50 transition-all duration-200"
          >
            <Database className="w-3 h-3 inline mr-1" />
            Auth Issues
          </button>
        </div>
      </div>
    </div>
  );
};
