import React, { useEffect, useMemo, useState } from "react";
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
  resumeInfo?: {
    mode?: string;
    message?: string;
  };
  onOpenLogsTab?: (args: { entries: any[]; title?: string }) => void;
}

const resolveActionLabel = (action: any, index: number) => {
  if (!action) {
    return `Action ${index + 1}`;
  }

  return (
    action.label ||
    action.title ||
    action.name ||
    action.summary ||
    action.description ||
    `Action ${index + 1}`
  );
};

export const AIMessage: React.FC<AIMessageProps> = ({
  text,
  completeResult,
  actions,
  needsClarification = false,
  isStreaming = false,
  isExpanded = false,
  events = [],
  resumeInfo,
  onOpenLogsTab,
}) => {
  const clarifyingQuestions = completeResult?.clarifying_questions ?? completeResult?.clarifyingQuestions;
  const missingInfo = completeResult?.missing_info ?? completeResult?.missingInfo;
  const toolResults = completeResult?.tool_results ?? completeResult?.toolResults;

  const normalizedActions = Array.isArray(actions) ? actions.filter(Boolean) : [];

  const relevantLogs = Array.isArray(completeResult?.relevant_logs)
    ? completeResult?.relevant_logs ?? []
    : Array.isArray(completeResult?.relevantLogs)
    ? completeResult?.relevantLogs ?? []
    : [];

  const hasLogs = relevantLogs.length > 0;

  const formatResumeMode = (mode?: string) => {
    if (!mode) {
      return undefined;
    }
    return mode
      .split(/[_\s]+/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  };

  const effectiveResumeInfo = useMemo(() => {
    const mode = resumeInfo?.mode ?? completeResult?.resume_mode;
    const message = resumeInfo?.message ??
      (completeResult?.resumed_from_wait
        ? "Investigation resumed after pending clarification."
        : undefined);

    if (!mode && !message) {
      return undefined;
    }
    return {
      mode,
      message,
    };
  }, [resumeInfo, completeResult]);

  const formattedResumeMode = formatResumeMode(effectiveResumeInfo?.mode);

  // Order events for stable visual progress
  const orderedEvents = useMemo(() => {
    const arr = Array.isArray(events) ? [...events] : [];
    return arr.sort((a, b) => {
      const ta = a.startedAt || a.timestamp || "";
      const tb = b.startedAt || b.timestamp || "";
      return ta.localeCompare(tb);
    });
  }, [events]);

  type EventItem = NonNullable<AIMessageProps["events"]>[number];

  const buildEventKey = (ev: EventItem, index: number) => {
    const base = `${ev.node || "node"}-${ev.timestamp || ""}`;
    return `${base}-${index}`;
  };

  const [activeEventKey, setActiveEventKey] = useState<string | null>(null);

  useEffect(() => {
    if (!orderedEvents.length) {
      setActiveEventKey(null);
      return;
    }
    const firstKey = buildEventKey(orderedEvents[orderedEvents.length - 1], orderedEvents.length - 1);
    setActiveEventKey(firstKey);
  }, [orderedEvents]);
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
      case "direct_filter":
        return { icon: <FileText className="w-4 h-4" />, chip: "bg-cyan-500/10 text-cyan-300 border-cyan-600/40" };
      case "single_stage_filter":
        return { icon: <FileText className="w-4 h-4" />, chip: "bg-teal-500/10 text-teal-300 border-teal-600/40" };
      case "context_aware_filter":
        return { icon: <Boxes className="w-4 h-4" />, chip: "bg-indigo-500/10 text-indigo-300 border-indigo-600/40" };
      case "filter_optimization":
        return { icon: <FileText className="w-4 h-4" />, chip: "bg-amber-500/10 text-amber-300 border-amber-600/40" };
      case "primary_call_prep":
        return { icon: <FileText className="w-4 h-4" />, chip: "bg-sky-500/10 text-sky-300 border-sky-600/40" };
      case "execute_logging_api":
        return { icon: <FileText className="w-4 h-4" />, chip: "bg-rose-500/10 text-rose-300 border-rose-600/40" };
      case "response_analysis":
        return { icon: <Brain className="w-4 h-4" />, chip: "bg-emerald-500/10 text-emerald-300 border-emerald-600/40" };
      case "multi_dimensional_analysis":
        return { icon: <Brain className="w-4 h-4" />, chip: "bg-fuchsia-500/10 text-fuchsia-300 border-fuchsia-600/40" };
      case "auto_refine_filters":
        return { icon: <FileText className="w-4 h-4" />, chip: "bg-lime-500/10 text-lime-300 border-lime-600/40" };
      case "broaden_search":
        return { icon: <FileText className="w-4 h-4" />, chip: "bg-yellow-500/10 text-yellow-300 border-yellow-600/40" };
      case "arch_resource_discovery":
        return { icon: <Boxes className="w-4 h-4" />, chip: "bg-pink-500/10 text-pink-300 border-pink-600/40" };
      case "upstream_downstream_check":
        return { icon: <Boxes className="w-4 h-4" />, chip: "bg-orange-500/10 text-orange-300 border-orange-600/40" };
      case "present_results":
        return { icon: <FileText className="w-4 h-4" />, chip: "bg-green-500/10 text-green-300 border-green-600/40" };
      case "session_complete":
        return { icon: <CheckCircle2 className="w-4 h-4" />, chip: "bg-green-600/10 text-green-300 border-green-700/40" };
      default:
        return { icon: <FileText className="w-4 h-4" />, chip: "bg-slate-500/10 text-slate-300 border-slate-600/40" };
    }
  };

  const NodeProgress: React.FC<{
    items: NonNullable<AIMessageProps["events"]>;
    activeKey: string | null;
    onSelect: (key: string) => void;
  }> = ({ items, activeKey, onSelect }) => {
    if (!items || items.length === 0) return null;
    return (
      <div className="px-5 pt-5 pb-4 border-b border-slate-800/60">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-3">
          <div className="text-[11px] uppercase tracking-wide text-slate-400">Investigation Flow</div>
          {activeKey && <div className="text-[11px] text-slate-500">Tap a node to inspect captured state</div>}
        </div>
        <div className="relative overflow-x-auto pb-1">
          <div className="pointer-events-none absolute left-0 top-0 h-full w-6 bg-gradient-to-r from-slate-900/70 to-transparent" />
          <div className="pointer-events-none absolute right-0 top-0 h-full w-6 bg-gradient-to-l from-slate-900/70 to-transparent" />
          <div className="flex items-stretch gap-4 min-w-max pr-3 snap-x snap-mandatory">
            {items.map((ev, idx) => {
              const key = buildEventKey(ev, idx);
              const isActive = key === activeKey;
              const done = (ev.status || "").toLowerCase() === "completed";
              const meta = getMeta(ev.node);
              const startedAt = ev.startedAt ? new Date(ev.startedAt) : null;
              const completedAt = ev.completedAt ? new Date(ev.completedAt) : null;
              const durationMs = startedAt && completedAt ? completedAt.getTime() - startedAt.getTime() : null;
              const durationText = durationMs !== null ? `${(durationMs / 1000).toFixed(2)}s` : null;

              const summary = () => {
                const d: any = ev.data || {};
                switch (ev.node) {
                  case "response_analysis": {
                    const q = d.result_quality || d.quality;
                    const total = d.result_stats?.total ?? d.total;
                    return `Quality ${q ?? "—"}${typeof total === "number" ? ` · Total ${total}` : ""}`;
                  }
                  case "auto_refine_filters":
                    return `Refinements ${d.iterations ?? d.count ?? "—"}`;
                  case "broaden_search":
                    return `Broadenings ${d.iterations ?? d.count ?? "—"}`;
                  case "arch_resource_discovery":
                    return `Discovered ${d.discovered ?? "—"}`;
                  case "multi_dimensional_analysis":
                    if (d?.summary) {
                      const t = d.summary.total;
                      const er = d.summary.error_rate;
                      return `Analyzed ${t ?? "—"}${typeof er === "number" ? ` · Error ${er}%` : ""}`;
                    }
                    return "";
                  case "execute_logging_api":
                    return `${typeof d.returned === "number" ? `Returned ${d.returned}` : ""}${typeof d.page_count === "number" ? ` · Pages ${d.page_count}` : ""}`.trim();
                  default:
                    return "";
                }
              };

              return (
                <div
                  key={key}
                  onClick={() => onSelect(key)}
                  className={`relative snap-start shrink-0 transition-all duration-400 cursor-pointer ${
                    isActive ? "w-[320px] lg:w-[360px]" : "w-[220px] lg:w-[240px]"
                  }`}
                >
                  <div
                    className={`h-full rounded-2xl border bg-slate-900/55 backdrop-blur-md px-4 py-3 transition-all duration-500 hover:-translate-y-1 hover:shadow-[0_20px_45px_rgba(56,189,248,0.15)] overflow-hidden ${
                      isActive
                        ? "border-sky-500/40 ring-2 ring-sky-500/20"
                        : done
                        ? "border-emerald-500/30"
                        : "border-slate-800/60"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 gap-y-2 flex-wrap">
                      <div className="flex items-center gap-3">
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-200">
                          {meta.icon}
                        </span>
                        <div className="min-w-0">
                          <div className="text-xs font-semibold text-slate-200 leading-tight" title={ev.title}>
                            {ev.title}
                          </div>
                          <div className="text-[11px] text-slate-500 mt-1">
                            {summary() || ev.node || "Node"}
                          </div>
                        </div>
                      </div>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full border inline-flex items-center gap-1 flex-shrink-0 self-start ${
                          done
                            ? "bg-emerald-500/10 text-emerald-300 border-emerald-600/40"
                            : "bg-blue-500/10 text-blue-300 border-blue-600/40"
                        }`}
                      >
                        {done ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                        {ev.status}
                      </span>
                    </div>

                    {durationText && (
                      <div className="mt-2 text-[10px] text-slate-500 uppercase tracking-[0.2em]">
                        Duration {durationText}
                      </div>
                    )}

                    {isActive && (
                      <div className="mt-3 space-y-3 text-left animate-slide-up">
                        {ev.state && (
                          <div>
                            <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400 mb-1">State Snapshot</div>
                            <ExpandableValue value={(ev as any).state ?? ev} maxChars={200} />
                          </div>
                        )}
                        {ev.data && (
                          <div>
                            <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400 mb-1">Event Data</div>
                            <ExpandableValue value={ev.data} maxChars={200} />
                          </div>
                        )}
                        {(!ev.state && !ev.data) && (
                          <div className="text-[12px] text-slate-400/80">No structured payload captured for this node.</div>
                        )}
                      </div>
                    )}
                  </div>
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
          <NodeProgress
            items={orderedEvents as NonNullable<AIMessageProps["events"]>}
            activeKey={activeEventKey}
            onSelect={(key) => setActiveEventKey(key)}
          />
        )}
        {effectiveResumeInfo?.message && (
          <div className="px-5 pt-4">
            <div className="flex items-start gap-3 rounded-xl border border-sky-500/35 bg-sky-500/10 px-4 py-3 text-sky-100 shadow-inner">
              <span className="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full border border-sky-400/60 bg-sky-500/20">
                {isStreaming ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                )}
              </span>
              <div className="space-y-1">
                <div className="text-[11px] uppercase tracking-[0.25em] text-sky-200/80">
                  {formattedResumeMode || "Resumed"}
                </div>
                <div className="text-[13px] leading-5">
                  {effectiveResumeInfo.message}
                </div>
              </div>
            </div>
          </div>
        )}
        {/* Final analysis comes after stages */}
        <div className="p-5 text-[13px]">
          <MessageAnalysis
            analysis={text}
            metadata={completeResult?.metadata}
            needsClarification={needsClarification}
            clarifyingQuestions={clarifyingQuestions}
            missingInfo={missingInfo}
            toolResults={toolResults}
            isStreaming={isStreaming}
            completeResult={completeResult}
          />
          {hasLogs && (
            <div className="mt-3">
              <button
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-blue-700/60 bg-blue-900/30 text-blue-300 hover:bg-blue-900/50 transition-colors text-[12px]"
                onClick={() => onOpenLogsTab && onOpenLogsTab({
                  entries: relevantLogs,
                  title: `AI Results (${relevantLogs.length})`
                })}
                title="Open these entries in a logs tab"
              >
                Open in Logs Tab
              </button>
            </div>
          )}
        </div>

        {/* Relevant Logs (from Execute Logging API) */}
        {hasLogs && (
          <div className="px-5 pb-5">
            <div className="mb-2 flex items-center justify-between">
              <div className="text-[12px] text-slate-400">Logs returned: {relevantLogs.length}</div>
              <button
                className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md border border-blue-700/60 bg-blue-900/30 text-blue-300 hover:bg-blue-900/50 transition-colors text-[12px]"
                onClick={() => onOpenLogsTab && onOpenLogsTab({
                  entries: relevantLogs,
                  title: `AI Results (${relevantLogs.length})`
                })}
                title="Open these entries in a logs tab"
              >
                Open in Logs Tab
              </button>
            </div>
            <div className="space-y-2">
              {relevantLogs.slice(0, 20).map((log: any, idx: number) => {
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

        {/* When no logs returned, still show a clear, compact notice */}
        {completeResult && Array.isArray(completeResult.relevant_logs) && completeResult.relevant_logs.length === 0 && (
          <div className="px-5 pb-5">
            <div className="border border-slate-800/60 rounded-xl overflow-hidden bg-slate-900/40">
              <div className="px-3 py-2 text-slate-300 text-[13px]">No matching logs found for the current query.</div>
              <div className="px-3 pb-3 text-slate-400 text-[12px]">Try broadening the time range or lowering severity.</div>
            </div>
          </div>
        )}

        {/* Actions - compact chips, no heading */}
        {normalizedActions.length > 0 && (
          <div className="px-5 pb-5">
            <div className="flex flex-wrap gap-2">
              {normalizedActions.map((action, index) => (
                <button
                  key={index}
                  className="px-3 py-1.5 bg-slate-800/50 hover:bg-slate-700/60 text-slate-200 text-xs rounded-md border border-slate-700/60 transition-colors"
                  onClick={() => {
                  }}
                >
                  {resolveActionLabel(action, index)}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
