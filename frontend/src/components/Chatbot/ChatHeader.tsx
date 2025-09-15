import React from "react";
import { Brain, History, Maximize2, Minimize2, MessageSquare, Trash2 } from "lucide-react";

interface Session {
  session_id: string;
  project_id: string;
  created_at: string;
  last_updated: string;
  message_count: number;
  context_summary: string;
}

interface ChatHeaderProps {
  showSessions: boolean;
  onToggleSessions: () => void;
  onStartNewSession: () => void;
  onToggleExpand?: () => void;
  isExpanded?: boolean;
  sessions: Session[];
  currentSessionId: string | null;
  onLoadSessionHistory: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  showSessions,
  onToggleSessions,
  onStartNewSession,
  onToggleExpand,
  isExpanded,
  sessions,
  currentSessionId,
  onLoadSessionHistory,
  onDeleteSession
}) => {
  return (
    <div className="border-b border-slate-700/50 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-md">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <h2 className="text-base font-semibold text-white">Chico</h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onToggleSessions}
            className="p-2 rounded-lg hover:bg-slate-800/60 border border-transparent hover:border-slate-700/50 transition-colors"
            title="Session History"
          >
            <History className="w-4 h-4 text-slate-400" />
          </button>

          {onToggleExpand && (
            <button
              onClick={onToggleExpand}
              className="p-2 rounded-lg hover:bg-slate-800/60 border border-transparent hover:border-slate-700/50 transition-colors"
              title={isExpanded ? "Minimize" : "Expand"}
            >
              {isExpanded ? (
                <Minimize2 className="w-4 h-4 text-slate-400" />
              ) : (
                <Maximize2 className="w-4 h-4 text-slate-400" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Session Management Panel */}
      {showSessions && (
        <div className="mt-4 p-4 bg-slate-800/40 rounded-xl border border-slate-700/50">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-semibold text-slate-200 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-blue-400" />
              Sessions
            </h3>
            <button
              onClick={onStartNewSession}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-md transition-colors"
            >
              New
            </button>
          </div>

          {sessions.length === 0 ? (
            <div className="text-center py-6">
              <MessageSquare className="w-10 h-10 mx-auto mb-2 text-slate-600" />
              <p className="text-slate-500 text-sm">No active sessions</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-56 overflow-y-auto">
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                    currentSessionId === session.session_id
                      ? "bg-blue-500/15 border-blue-500/40"
                      : "bg-slate-700/30 border-slate-600/40 hover:bg-slate-700/50"
                  }`}
                >
                  <div
                    className="flex-1 min-w-0"
                    onClick={() => onLoadSessionHistory(session.session_id)}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-slate-400 font-medium">
                        {new Date(session.last_updated).toLocaleDateString()}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        • {session.message_count} msgs
                      </span>
                    </div>
                    <p className="text-sm text-slate-200 truncate">
                      {session.context_summary || "No context available"}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(session.session_id);
                    }}
                    className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-md"
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
  );
};
