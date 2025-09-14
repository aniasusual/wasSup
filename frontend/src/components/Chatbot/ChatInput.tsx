import React from "react";
import { Send, Search, Filter, Zap, Database } from "lucide-react";

interface ChatInputProps {
  input: string;
  setInput: (value: string) => void;
  onSendMessage: () => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  sending: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  input,
  setInput,
  onSendMessage,
  onKeyDown,
  sending
}) => {
  const quickActions = [
    {
      label: "Recent Errors",
      icon: Filter,
      query: "Show me **ERROR** logs from `cloud_run_revision` services in the last hour"
    },
    {
      label: "Performance",
      icon: Zap,
      query: "Find *performance issues* in my `gce_instance` logs"
    },
    {
      label: "Auth Issues",
      icon: Database,
      query: "Check for **authentication failures** across all services"
    }
  ];

  return (
    <div className="border-t border-slate-700/50 p-4 bg-transparent">
      <div className="flex items-center gap-3 glass-card rounded-xl px-4 py-3 focus-within:border-blue-500/50 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all duration-200">
        <div className="flex-shrink-0">
          <Search className="w-5 h-5 text-slate-400" />
        </div>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={
            sending
              ? "Chico is thinking..."
              : "Ask Chico about your logs, services, time ranges… (Enter)"
          }
          className="flex-1 bg-transparent text-slate-200 placeholder-slate-500 focus:outline-none text-sm"
          disabled={sending}
        />
        <button
          onClick={onSendMessage}
          disabled={!input.trim() || sending}
          className={`inline-flex items-center justify-center px-4 py-2 rounded-lg transition-all duration-200 ${
            !input.trim() || sending
              ? "bg-slate-700/40 text-slate-500 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 text-white"
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
        {quickActions.map((action, index) => (
          <button
            key={index}
            onClick={() => setInput(action.query)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800/40 hover:bg-slate-700/50 text-slate-300 rounded-md border border-slate-700/50 transition-colors"
          >
            <action.icon className="w-3.5 h-3.5" />
            {action.label}
          </button>
        ))}
      </div>
    </div>
  );
};
