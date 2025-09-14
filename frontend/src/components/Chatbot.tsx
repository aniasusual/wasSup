import React, { useState, useRef, useEffect } from "react";
import toast from "react-hot-toast";
import { useAuth } from "../contexts/Auth";
import axios from "axios";

// Import our new components
import { ChatHeader } from "./Chatbot/ChatHeader";
import { ChatInput } from "./Chatbot/ChatInput";
import { EmptyState } from "./Chatbot/EmptyState";
import { UserMessage } from "./Chatbot/UserMessage";
import { AIMessage } from "./Chatbot/AIMessage";
// import { TypingIndicator } from "./Chatbot/TypingIndicator";

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
  completeResult?: any;
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
  onOpenInsight = () => {},
  isExpanded = false,
  onToggleExpand,
}: any) => {
  // Suppress unused parameter warning for future use
  void onOpenInsight;
  void projectArchitecture;

  // State management
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [sending, setSending] = useState<boolean>(false);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showSessions, setShowSessions] = useState<boolean>(false);
  
  // Refs
  const listRef = useRef<HTMLDivElement | null>(null);
  const { token } = useAuth();

  // Load user sessions on component mount
  useEffect(() => {
    if (token) {
      loadUserSessions();
    }
  }, [token]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    const el = listRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, isTyping]);

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
    setSending(true);
    setIsTyping(true);

    // Create a streaming AI response message
    const streamingMessageId = Date.now() + 1;
    const streamingMessage: Message = {
      id: streamingMessageId,
      text: "",
      sender: "ai",
      timestamp: new Date().toLocaleTimeString(),
      toolResults: null,
      actions: [],
      needsClarification: false,
      isStreaming: true,
    };

    setMessages((prev: Message[]) => [...prev, streamingMessage]);

    try {
      // Use the streaming endpoint
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/agent/query/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: input,
          project_id: projectId,
          session_id: currentSessionId,
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
      let accumulatedText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case "status":
                  // Skip status updates - no loading indicators needed
                  break;

                case "chunk":
                  // Handle streaming text chunks
                  if (data.message) {
                    const seamFixed = (prev: string, chunk: string) => {
                      let incoming = String(chunk);
                      // If chunk begins with heading/list/code fence and previous doesn't end with newline, add one
                      const needsBreak =
                        /^(\s*#{1,6}\s)/.test(incoming) || // heading
                        /^(\s*[-*+]\s)/.test(incoming) || // unordered list
                        /^(\s*\d+\.\s)/.test(incoming) || // ordered list
                        /^(\s*```)/.test(incoming); // code fence

                      if (needsBreak && prev && !prev.endsWith("\n")) {
                        incoming = "\n" + incoming;
                      }

                      // Also fix mid-line headings like "... last_hour ## Heading"
                      incoming = incoming.replace(/(\S)\s+(#{1,6}\s)/g, "$1\n$2");

                      return prev + incoming;
                    };

                    accumulatedText = seamFixed(accumulatedText, data.message);
                    setMessages((prev: Message[]) =>
                      prev.map((msg) =>
                        msg.id === streamingMessageId
                          ? {
                              ...msg,
                              text: accumulatedText,
                            }
                          : msg
                      )
                    );
                  }
                  break;

                case "result":
                  finalResult = data.data;
                  setMessages((prev: Message[]) =>
                    prev.map((msg) =>
                      msg.id === streamingMessageId
                        ? {
                            ...msg,
                            text: finalResult?.analysis || accumulatedText,
                            toolResults: finalResult?.toolResults || null,
                            actions: finalResult?.actions || [],
                            needsClarification: finalResult?.needsClarification || false,
                            isStreaming: false,
                            completeResult: finalResult,
                          }
                        : msg
                    )
                  );
                  break;

                case "error":
                  setMessages((prev: Message[]) =>
                    prev.map((msg) =>
                      msg.id === streamingMessageId
                        ? {
                            ...msg,
                            text: `❌ Error: ${data.message}`,
                            isStreaming: false,
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
      if (finalResult?.session_id && !currentSessionId) {
        setCurrentSessionId(finalResult.session_id);
      }

      // Reload sessions to get updated context
      await loadUserSessions();
    } catch (error: any) {
      console.error("Error generating AI response:", error);
      let errorMessage = "Failed to generate AI response";
      if (error.message) {
        errorMessage = `Network error: ${error.message}`;
      }

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
      setSending(false);
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full min-h-0 text-[13px]">
      {/* Header */}
      <ChatHeader
        showSessions={showSessions}
        onToggleSessions={() => setShowSessions(!showSessions)}
        onStartNewSession={startNewSession}
        onToggleExpand={onToggleExpand}
        isExpanded={isExpanded}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onLoadSessionHistory={loadSessionHistory}
        onDeleteSession={deleteSession}
      />

      {/* Messages Area */}
      <div
        ref={listRef}
        className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 && (
          <EmptyState currentSessionId={currentSessionId} />
        )}

        {messages.map((message: Message) => (
          <div key={message.id} className="w-full animate-fade-in">
            {message.sender === "user" ? (
              <UserMessage
                text={message.text}
                timestamp={message.timestamp}
              />
            ) : (
              <AIMessage
                text={message.text}
                completeResult={message.completeResult}
                actions={message.actions}
                needsClarification={message.needsClarification}
                isStreaming={message.isStreaming}
              />
            )}
          </div>
        ))}


      </div>

      {/* Input Area */}
      <ChatInput
        input={input}
        setInput={setInput}
        onSendMessage={sendMessage}
        onKeyDown={handleKeyDown}
        sending={sending}
      />
    </div>
  );
};
