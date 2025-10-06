import { useMemo, useState } from "react";
import { ChevronDown, History, Maximize2, Minimize2, RotateCcw, Sparkles } from "lucide-react";

import type { ChatSessionSummary } from "../../types/chat";

interface ChatHeaderProps {
  isStreaming: boolean;
  isExpanded: boolean;
  onReset: () => void;
  sessions?: ChatSessionSummary[];
  activeSessionId?: string | null;
  isLoadingSessions?: boolean;
  onSessionSelect?: (sessionId: string) => void;
  onToggleExpand?: () => void;
}

const formatTimestamp = (iso?: string) => {
  if (!iso) {
    return "";
  }
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }
  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const ChatHeader = ({
  isStreaming,
  isExpanded,
  onReset,
  sessions = [],
  activeSessionId = null,
  isLoadingSessions = false,
  onSessionSelect,
  onToggleExpand,
}: ChatHeaderProps) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const activeSession = useMemo(
    () => sessions.find((item) => item.sessionId === activeSessionId) ?? null,
    [sessions, activeSessionId]
  );

  const sessionLabel = activeSession?.title ?? "New conversation";

  const handleToggleMenu = () => {
    setIsMenuOpen((prev) => !prev);
  };

  const handleSelect = (sessionId: string) => {
    if (onSessionSelect) {
      onSessionSelect(sessionId);
    }
    setIsMenuOpen(false);
  };

  const handleNewSession = () => {
    onReset();
    setIsMenuOpen(false);
  };

  return (
    <div className="flex items-center justify-between border-b border-gray-800/80 px-4 py-3">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-500/20 text-blue-300">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-100">Investigation Assistant</h3>
          <p className="text-xs text-gray-500">
            {isStreaming ? "Analyzing signals..." : "Ready to collaborate"}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <div className="relative">
          <button
            type="button"
            onClick={handleToggleMenu}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-800 bg-gray-900/60 px-3 py-1.5 text-sm text-gray-300 transition-colors hover:border-gray-700 hover:text-gray-100"
            title="Select conversation session"
          >
            <History className="h-4 w-4" />
            <span className="max-w-[140px] truncate text-left">{sessionLabel}</span>
            <ChevronDown className={`h-3.5 w-3.5 transition-transform ${isMenuOpen ? "rotate-180" : ""}`} />
          </button>
          {isMenuOpen && (
            <div className="absolute right-0 z-20 mt-2 w-64 rounded-xl border border-gray-800/80 bg-gray-950/90 p-2 shadow-xl backdrop-blur">
              <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-wide text-gray-500">
                <span>Sessions</span>
                <button
                  type="button"
                  onClick={handleNewSession}
                  className="rounded-md px-2 py-1 text-[11px] font-semibold text-blue-300 transition-colors hover:bg-blue-500/10"
                >
                  New
                </button>
              </div>
              <div className="max-h-64 space-y-1 overflow-y-auto pr-1">
                {isLoadingSessions ? (
                  <div className="px-2 py-3 text-xs text-gray-500">Loading sessions…</div>
                ) : sessions.length === 0 ? (
                  <div className="px-2 py-3 text-xs text-gray-500">
                    No previous sessions yet.
                  </div>
                ) : (
                  sessions.map((session) => {
                    const isActive = session.sessionId === activeSessionId;
                    return (
                      <button
                        key={session.sessionId}
                        type="button"
                        onClick={() => handleSelect(session.sessionId)}
                        className={`w-full rounded-lg px-3 py-2 text-left transition-colors ${
                          isActive
                            ? "bg-blue-500/10 text-blue-200"
                            : "bg-transparent text-gray-200 hover:bg-gray-900"
                        }`}
                      >
                        <p className="text-sm font-medium leading-tight">{session.title}</p>
                        <p className="text-[11px] text-gray-500">
                          {formatTimestamp(session.updatedAt ?? session.createdAt)}
                        </p>
                        {session.lastMessagePreview && (
                          <p className="mt-1 max-h-[2.75rem] overflow-hidden text-[11px] text-gray-400">
                            {session.lastMessagePreview}
                          </p>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={onReset}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-gray-800 bg-gray-900/60 text-gray-400 hover:text-gray-200 hover:border-gray-700 transition-colors"
          title="Reset conversation"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
        {onToggleExpand && (
          <button
            type="button"
            onClick={onToggleExpand}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-gray-800 bg-gray-900/60 text-gray-400 hover:text-gray-200 hover:border-gray-700 transition-colors"
            title={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
        )}
      </div>
    </div>
  );
};

export default ChatHeader;
