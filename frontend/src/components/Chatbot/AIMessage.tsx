import React, { useState } from "react";
import { MessageAnalysis } from "./MessageAnalysis";
import { Brain, FileText, Boxes, CheckCircle2, Loader2, ChevronDown, ChevronUp } from "lucide-react";

interface AIMessageProps {
  text: string;
  completeResult?: any;
  actions?: any[];
  needsClarification?: boolean;
  isStreaming?: boolean;
  events?: Array<{
    node: string;
    title: string;
    status: string; // started | completed
    data: any;
    timestamp: string;
  }>;
}

export const AIMessage: React.FC<AIMessageProps> = ({
  text,
  completeResult,
  actions,
  needsClarification = false,
  isStreaming = false,
  events = []
}) => {
  const ExpandableValue: React.FC<{ value: any; maxChars?: number }> = ({ value, maxChars = 120 }) => {
    const [expanded, setExpanded] = useState(false);
    const isString = typeof value === "string";
    const compact = isString ? (value as string) : JSON.stringify(value);
    const full = isString ? (value as string) : JSON.stringify(value, null, 2);
    const tooLong = (compact || "").length > maxChars;

    if (!tooLong) {
      return <div className="truncate">{compact}</div>;
    }

    return (
      <div className="space-y-1">
        {!expanded ? (
          <div className="relative">
            <div className="truncate pr-16">{compact.slice(0, maxChars)}…</div>
            <span
              role="button"
              onClick={() => setExpanded(true)}
              className="absolute right-0 top-0 text-[11px] inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800/60 border border-slate-700/60 text-slate-300 hover:bg-slate-800 cursor-pointer select-none"
              title="Show more"
            >
              Show more
              <ChevronDown className="w-3 h-3" />
            </span>
          </div>
        ) : (
          <>
            <pre className="font-mono text-[12px] whitespace-pre-wrap max-h-40 overflow-auto bg-slate-950/50 border border-slate-800/60 rounded-md p-2">
              {full}
            </pre>
            <div className="flex justify-end">
              <span
                role="button"
                onClick={() => setExpanded(false)}
                className="text-[11px] inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800/60 border border-slate-700/60 text-slate-300 hover:bg-slate-800 cursor-pointer select-none"
                title="Show less"
              >
                Show less
                <ChevronUp className="w-3 h-3" />
              </span>
            </div>
          </>
        )}
      </div>
    );
  };

  const getMeta = (node: string) => {
    switch (node) {
      case "user_query_input":
        return { icon: <FileText className="w-4 h-4" />, chip: "bg-blue-500/10 text-blue-300 border-blue-600/40" };
      case "architecture_loader":
        return { icon: <Boxes className="w-4 h-4" />, chip: "bg-purple-500/10 text-purple-300 border-purple-600/40" };
      case "intent_and_query_analysis":
        return { icon: <Brain className="w-4 h-4" />, chip: "bg-emerald-500/10 text-emerald-300 border-emerald-600/40" };
      default:
        return { icon: <FileText className="w-4 h-4" />, chip: "bg-slate-500/10 text-slate-300 border-slate-600/40" };
    }
  };

  return (
    <div className="w-full mb-6 animate-slide-up">
      {/* Main Analysis Content */}
      <div className="glass-card rounded-2xl overflow-hidden">
        {/* Subtle collapsible node results (stages first) */}
        {events && events.length > 0 && (
          <div className="px-5 pt-5 pb-3 space-y-2 border-b border-slate-800/60">
            {events.map((ev, idx) => {
              const meta = getMeta(ev.node);
              const StatusIcon = (ev.status === "completed" ? CheckCircle2 : Loader2) as any;
              const startedAt = ev.startedAt ? new Date(ev.startedAt) : null;
              const completedAt = ev.completedAt ? new Date(ev.completedAt) : null;
              const durationMs = startedAt && completedAt ? (completedAt.getTime() - startedAt.getTime()) : null;
              const humanDuration = durationMs !== null ? `${(durationMs / 1000).toFixed(2)}s` : null;
              return (
                <details key={`${ev.node}-${idx}`} className="group border border-slate-800/60 rounded-xl overflow-hidden">
                  <summary className="list-none flex items-center justify-between px-3 py-2 bg-slate-900/50 hover:bg-slate-900/60 cursor-pointer select-none">
                    <div className="flex items-center gap-2 text-slate-200 text-sm font-medium">
                      <span className="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-slate-800/60 border border-slate-700/60">
                        {meta.icon}
                      </span>
                      <span>{ev.title}</span>
                    </div>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full border inline-flex items-center gap-1 ${meta.chip}`}>
                      <StatusIcon className={`w-3.5 h-3.5 ${ev.status === 'completed' ? '' : 'animate-pulse'}`} />
                      {ev.status}
                    </span>
                  </summary>
                  <div className="px-3 py-3 bg-slate-950/40">
                    {(startedAt || completedAt) && (
                      <div className="mb-2 text-[11px] text-slate-400 flex flex-wrap gap-x-4 gap-y-1">
                        {startedAt && (
                          <span>Started: {startedAt.toLocaleTimeString()}</span>
                        )}
                        {completedAt && (
                          <span>Completed: {completedAt.toLocaleTimeString()}</span>
                        )}
                        {humanDuration && (
                          <span>Duration: {humanDuration}</span>
                        )}
                      </div>
                    )}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[12px] text-slate-300/90">
                      {Object.entries(ev.data || {}).slice(0, 8).map(([k, v]) => (
                        <div key={k} className="bg-slate-950/40 border border-slate-800/60 rounded-lg px-2 py-1" title={k}>
                          <div className="text-slate-400 text-[10px] uppercase tracking-wide">{k}</div>
                          <ExpandableValue value={v} />
                        </div>
                      ))}
                    </div>
                  </div>
                </details>
              );
            })}
          </div>
        )}

        {/* Final analysis comes after stages */}
        <div className="p-5 text-[13px]">
          <MessageAnalysis
            analysis={text}
            metadata={completeResult?.metadata}
            needsClarification={needsClarification}
            clarifyingQuestions={completeResult?.clarifying_questions}
            missingInfo={completeResult?.missing_info}
            toolResults={completeResult?.tool_results}
            isStreaming={isStreaming}
            completeResult={completeResult}
          />
        </div>

        {/* Actions - compact chips, no heading */}
        {actions && actions.length > 0 && (
          <div className="px-5 pb-5">
            <div className="flex flex-wrap gap-2">
              {actions.map((action, index) => (
                <button
                  key={index}
                  className="px-3 py-1.5 bg-slate-800/50 hover:bg-slate-700/60 text-slate-200 text-xs rounded-md border border-slate-700/60 transition-colors"
                  onClick={() => {
                  }}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
