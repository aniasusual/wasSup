import React, { useMemo, useState } from "react";
import { MessageAnalysis } from "./MessageAnalysis";
import { Brain, FileText, Boxes, CheckCircle2, Loader2, ChevronDown, ChevronUp } from "lucide-react";

interface AIMessageProps {
  text: string;
  completeResult?: any;
  actions?: any[];
  needsClarification?: boolean;
  isStreaming?: boolean;
  isExpanded?: boolean;
  events?: Array<{
    node: string;
    title: string;
    status: string; // started | completed
    data: any;
    timestamp: string;
    startedAt?: string;
    completedAt?: string;
  }>;
}

export const AIMessage: React.FC<AIMessageProps> = ({
  text,
  completeResult,
  actions,
  needsClarification = false,
  isStreaming = false,
  isExpanded = false,
  events = []
}) => {
  // Order events for stable visual progress
  const orderedEvents = useMemo(() => {
    const arr = Array.isArray(events) ? [...events] : [];
    return arr.sort((a, b) => {
      const ta = a.startedAt || a.timestamp || "";
      const tb = b.startedAt || b.timestamp || "";
      return ta.localeCompare(tb);
    });
  }, [events]);
  const ExpandableValue: React.FC<{ value: any; maxChars?: number }> = ({ value, maxChars = 120 }) => {
    const [expanded, setExpanded] = useState(false);
    const isString = typeof value === "string";
    const compact = isString ? (value as string) : JSON.stringify(value);
    const full = isString ? (value as string) : JSON.stringify(value, null, 2);
    const tooLong = (compact || "").length > maxChars;

    if (isString && !tooLong) {
      return (
        <code className="inline-block max-w-full truncate px-1.5 py-0.5 rounded bg-slate-950/40 border border-slate-800/60 text-white/90 break-all">
          {compact}
        </code>
      );
    }

    return (
      <div className="space-y-1">
        {!expanded ? (
          <div className="relative">
            <div className="truncate pr-16 text-white">{compact.slice(0, maxChars)}…</div>
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
          <div className="rounded-md border border-slate-800/60 bg-slate-950/50">
            <div className="flex items-center justify-between px-2 py-1 border-b border-slate-800/60">
              <div className="text-[11px] text-slate-400">JSON</div>
              <div className="flex items-center gap-2">
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
            </div>
            <pre className={`font-mono text-[12px] leading-5 whitespace-pre-wrap break-words break-all w-full max-w-full max-h-80 overflow-auto p-3 text-white`}>
              {full}
            </pre>
          </div>
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

  const NodeProgress: React.FC<{ items: NonNullable<AIMessageProps["events"]> }>= ({ items }) => {
    if (!items || items.length === 0) return null;
    return (
      <div className="px-5 pt-5 pb-4 border-b border-slate-800/60">
        <div className="text-[11px] uppercase tracking-wide text-slate-400 mb-2">Progress</div>
        <div className="relative overflow-x-auto">
          <div className="pointer-events-none absolute left-0 top-0 h-full w-6 bg-gradient-to-r from-slate-900/70 to-transparent" />
          <div className="pointer-events-none absolute right-0 top-0 h-full w-6 bg-gradient-to-l from-slate-900/70 to-transparent" />
          <div className="flex items-stretch gap-4 min-w-max pr-2 snap-x snap-mandatory">
            {items.map((ev, idx) => {
              const done = (ev.status || "").toLowerCase() === "completed";
              const meta = getMeta(ev.node);
              return (
                <div key={`${ev.node}-${idx}`} className="flex items-center gap-4 snap-start">
                  <div className="flex flex-col items-center min-w-[140px]">
                    <div className={`w-full glass-card hover-card gradient-border rounded-xl px-3 py-2 ${done ? "border-emerald-500/40" : "border-blue-500/30"}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-slate-200 text-xs font-medium">
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-lg bg-slate-800/60 border border-slate-700/60">
                            {meta.icon}
                          </span>
                          <span className="truncate max-w-[9rem]" title={ev.title}>{ev.title}</span>
                        </div>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border inline-flex items-center gap-1 ${done ? "bg-emerald-500/10 text-emerald-300 border-emerald-600/40" : "bg-blue-500/10 text-blue-300 border-blue-600/40"}`}>
                          {done ? <CheckCircle2 className="w-3.5 h-3.5"/> : <Loader2 className="w-3.5 h-3.5 animate-spin"/>}
                          {ev.status}
                        </span>
                      </div>
                    </div>
                    {ev.startedAt && ev.completedAt && (
                      <div className="mt-1 text-[10px] text-slate-500">{((new Date(ev.completedAt).getTime()-new Date(ev.startedAt).getTime())/1000).toFixed(2)}s</div>
                    )}
                  </div>
                  {idx < items.length - 1 && (
                    <div className={`h-px w-10 self-center ${items[idx+1]?.status?.toLowerCase() === 'completed' ? 'bg-emerald-600/50' : 'bg-slate-700/60'}`}></div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="w-full max-w-full min-w-0 mb-6 animate-slide-up">
      {/* Main Analysis Content */}
      <div className="glass-card gradient-border hover-card rounded-2xl overflow-hidden max-w-full">
        {/* Horizontal progress */}
        {orderedEvents && orderedEvents.length > 0 && (
          <NodeProgress items={orderedEvents as NonNullable<AIMessageProps["events"]>} />
        )}
        {/* Collapsible node details */}
        {orderedEvents && orderedEvents.length > 0 && (
          <div className="px-5 pt-3 pb-3 space-y-2 border-b border-slate-800/60">
            {orderedEvents.map((ev, idx) => {
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
                  <div className="px-3 py-3 bg-slate-950/40 space-y-2">
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
                    <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-2">
                      <div className="text-slate-400 text-[10px] uppercase tracking-wide mb-1">State Snapshot</div>
                      <ExpandableValue value={(ev as any).state ?? ev} maxChars={180} />
                    </div>
                    {ev.data && (
                      <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-2">
                        <div className="text-slate-400 text-[10px] uppercase tracking-wide mb-1">Event Data</div>
                        <ExpandableValue value={ev.data} maxChars={180} />
                      </div>
                    )}
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

        {/* Relevant Logs (from Execute Logging API) */}
        {!!(completeResult?.relevant_logs?.length) && (
          <div className="px-5 pb-5">
            <div className="mb-2 text-[12px] text-slate-400">Logs returned: {completeResult.relevant_logs.length}</div>
            <div className="space-y-2">
              {completeResult.relevant_logs.slice(0, 20).map((log: any, idx: number) => {
                const severity = String(log?.severity || 'DEFAULT');
                const ts = log?.timestamp ? new Date(log.timestamp).toLocaleString() : '';
                const preview = (log?.message || '').toString();
                const resourceType = log?.resource_type || '';
                const chip = severity === 'ERROR' || severity === 'CRITICAL' || severity === 'ALERT' || severity === 'EMERGENCY'
                  ? 'bg-red-500/10 text-red-300 border-red-600/40'
                  : severity === 'WARNING'
                  ? 'bg-amber-500/10 text-amber-300 border-amber-600/40'
                  : 'bg-slate-500/10 text-slate-300 border-slate-600/40';
                return (
                  <details key={log.id || idx} className="group border border-slate-800/60 rounded-xl overflow-hidden">
                    <summary className="list-none px-3 py-2 bg-slate-900/50 hover:bg-slate-900/60 cursor-pointer select-none flex items-start gap-2">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border ${chip}`}>{severity}</span>
                      <div className="flex-1 min-w-0">
                        <div className="text-slate-300 text-[12px] flex items-center gap-2">
                          <span className="text-slate-400">{ts}</span>
                          {resourceType && <span className="text-slate-500">• {resourceType}</span>}
                        </div>
                        {/* Message preview with explicit expand available on open */}
                        <div className="text-slate-200 text-[13px] truncate" title={preview}>{preview}</div>
                      </div>
                    </summary>
                    <div className="px-3 py-3 bg-slate-950/40 space-y-2">
                      <div>
                        <div className="text-[11px] text-slate-400 mb-1">Message</div>
                        <ExpandableValue value={preview} maxChars={160} />
                      </div>
                      {(log?.payload?.jsonPayload || log?.payload?.textPayload || log?.payload?.protoPayload) && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {log?.payload?.jsonPayload && (
                            <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-2">
                              <div className="text-[11px] text-slate-400 mb-1">jsonPayload</div>
                              <ExpandableValue value={log.payload.jsonPayload} />
                            </div>
                          )}
                          {log?.payload?.textPayload && (
                            <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-2">
                              <div className="text-[11px] text-slate-400 mb-1">textPayload</div>
                              <ExpandableValue value={log.payload.textPayload} />
                            </div>
                          )}
                          {log?.payload?.protoPayload && (
                            <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-2">
                              <div className="text-[11px] text-slate-400 mb-1">protoPayload</div>
                              <ExpandableValue value={log.payload.protoPayload} />
                            </div>
                          )}
                        </div>
                      )}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {log?.http && (
                          <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-2">
                            <div className="text-[11px] text-slate-400 mb-1">http</div>
                            <ExpandableValue value={log.http} />
                          </div>
                        )}
                        {log?.resource_labels && (
                          <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-2">
                            <div className="text-[11px] text-slate-400 mb-1">resource.labels</div>
                            <ExpandableValue value={log.resource_labels} />
                          </div>
                        )}
                      </div>
                    </div>
                  </details>
                );
              })}
              {completeResult.relevant_logs.length > 20 && (
                <div className="text-[12px] text-slate-400">Showing first 20 entries…</div>
              )}
            </div>
          </div>
        )}

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
