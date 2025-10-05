import type { ComponentPropsWithoutRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { ChatLogReference, ChatMessage } from "../../types/chat";

interface ChatMessageBubbleProps {
  message: ChatMessage;
  onLogReferenceSelect?: (reference: ChatLogReference) => void;
}

const formatTimestamp = (iso: string) => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

export const ChatMessageBubble = ({ message, onLogReferenceSelect }: ChatMessageBubbleProps) => {
  const isUser = message.role === "user";
  const isPending = message.status === "pending";
  const metadata = (message.metadata ?? {}) as {
    markdown?: unknown;
    jsonPayload?: unknown;
  };

  const markdownContent =
    !isUser && typeof metadata.markdown === "string"
      ? metadata.markdown
      : message.content;
  const jsonRaw = !isUser && typeof metadata.jsonPayload === "string" ? metadata.jsonPayload : null;

  const markdownComponents = {
    h1: (props: ComponentPropsWithoutRef<"h1">) => (
      <h1 className="text-lg font-semibold text-blue-200" {...props} />
    ),
    h2: (props: ComponentPropsWithoutRef<"h2">) => (
      <h2 className="text-base font-semibold text-blue-100 mt-4" {...props} />
    ),
    h3: (props: ComponentPropsWithoutRef<"h3">) => (
      <h3 className="text-sm font-semibold text-blue-100 mt-3" {...props} />
    ),
    p: (props: ComponentPropsWithoutRef<"p">) => (
      <p className="leading-relaxed text-[14px] text-slate-100/90" {...props} />
    ),
    ul: (props: ComponentPropsWithoutRef<"ul">) => (
      <ul className="list-disc list-inside space-y-1 text-sm text-slate-100/90" {...props} />
    ),
    ol: (props: ComponentPropsWithoutRef<"ol">) => (
      <ol className="list-decimal list-inside space-y-1 text-sm text-slate-100/90" {...props} />
    ),
    li: (props: ComponentPropsWithoutRef<"li">) => (
      <li className="text-[14px] text-slate-100/90" {...props} />
    ),
    strong: (props: ComponentPropsWithoutRef<"strong">) => (
      <strong className="text-blue-200 font-semibold" {...props} />
    ),
    em: (props: ComponentPropsWithoutRef<"em">) => (
      <em className="text-blue-100/80" {...props} />
    ),
    blockquote: (props: ComponentPropsWithoutRef<"blockquote">) => (
      <blockquote className="border-l-2 border-blue-500/50 pl-3 text-blue-100 italic" {...props} />
    ),
    code: (props: ComponentPropsWithoutRef<"code">) => (
      <code className="rounded bg-slate-900/80 px-1.5 py-0.5 text-xs text-blue-200" {...props} />
    ),
    pre: (props: ComponentPropsWithoutRef<"pre">) => (
      <pre className="overflow-x-auto rounded-lg bg-slate-900/90 p-3 text-xs text-blue-100" {...props} />
    ),
    a: (props: ComponentPropsWithoutRef<"a">) => (
      <a className="text-sky-300 underline underline-offset-2 hover:text-sky-200" target="_blank" rel="noreferrer" {...props} />
    ),
    hr: () => <hr className="my-4 border-t border-slate-700/60" />,
  };

  let logReferences: ChatLogReference[] = [];
  if (jsonRaw && jsonRaw.trim().length > 0) {
    try {
      const parsedJson = JSON.parse(jsonRaw);
      if (
        parsedJson &&
        typeof parsedJson === "object" &&
        "log_references" in (parsedJson as Record<string, unknown>)
      ) {
        const candidate = (parsedJson as Record<string, unknown>)["log_references"];
        if (Array.isArray(candidate)) {
          logReferences = candidate
            .map((item): ChatLogReference | null => {
              if (typeof item !== "object" || item === null) {
                return null;
              }

              const record = item as Record<string, unknown>;
              const timeRangeValue = record.time_range;
              const normalizedTimeRange =
                typeof timeRangeValue === "object" && timeRangeValue !== null
                  ? (() => {
                      const range = timeRangeValue as { start?: unknown; end?: unknown };
                      return {
                        start: typeof range.start === "string" ? range.start : undefined,
                        end: typeof range.end === "string" ? range.end : undefined,
                      };
                    })()
                  : undefined;

              return {
                id: typeof record.id === "string" ? record.id : undefined,
                service_type:
                  typeof record.service_type === "string"
                    ? record.service_type
                    : undefined,
                service_name:
                  typeof record.service_name === "string"
                    ? record.service_name
                    : undefined,
                description:
                  typeof record.description === "string"
                    ? record.description
                    : undefined,
                severity:
                  typeof record.severity === "string"
                    ? record.severity
                    : undefined,
                count: typeof record.count === "number" ? record.count : undefined,
                pages_analyzed:
                  typeof record.pages_analyzed === "number"
                    ? record.pages_analyzed
                    : undefined,
                filter: typeof record.filter === "string" ? record.filter : undefined,
                summary:
                  typeof record.summary === "string"
                    ? record.summary
                    : undefined,
                time_range: normalizedTimeRange,
              };
            })
            .filter((item): item is ChatLogReference => Boolean(item));
        }
      }
    } catch {
    }
  }

  const wrapperClass = `flex w-full ${isUser ? "justify-end" : "justify-start"}`;
  const containerWidthClass = isUser
    ? "max-w-[88%] sm:max-w-[75%]"
    : "w-full";
  const bubbleBase = "relative rounded-2xl px-4 py-4 text-sm transition-colors";
  const assistantTone = "bg-gray-900/85 text-slate-100 border border-gray-800";
  const userTone = "bg-blue-600 text-white";
  const bubbleTone = isUser ? userTone : assistantTone;
  const pendingClass = isPending && !isUser ? " animate-pulse" : "";
  const bubbleWidthClass = isUser ? "" : " w-full";
  const metaClass = `mt-2 text-[10px] uppercase tracking-wide ${
    isUser ? "text-blue-200/80 text-right" : "text-slate-500"
  }`;

  return (
    <div className={wrapperClass}>
      <div className={containerWidthClass}>
        <div className={`${bubbleBase} ${bubbleTone}${pendingClass}${bubbleWidthClass}`}>
          {isPending ? (
            <span className="inline-flex gap-1">
              <span className="w-2 h-2 rounded-full bg-gray-300/80 animate-bounce" />
              <span className="w-2 h-2 rounded-full bg-gray-300/80 animate-bounce [animation-delay:120ms]" />
              <span className="w-2 h-2 rounded-full bg-gray-300/80 animate-bounce [animation-delay:240ms]" />
            </span>
          ) : isUser ? (
            <p className="whitespace-pre-line leading-relaxed">{message.content}</p>
          ) : (
            <div className="space-y-5">
              {markdownContent && (
                <div className="space-y-3">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={markdownComponents}
                  >
                    {markdownContent}
                  </ReactMarkdown>
                </div>
              )}
              {logReferences.length > 0 && (
                <div className="border-t border-gray-800 pt-4">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-blue-200/80">
                    Relevant logs
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {logReferences.map((ref, index) => {
                      const key = ref.id ?? `log-ref-${index}`;
                      const title = ref.service_name ?? ref.description ?? key;
                      const badge = ref.severity ?? ref.service_type ?? "Insight";
                      const count = typeof ref.count === "number" ? ref.count : undefined;
                      const summary = ref.summary ?? ref.description ?? "View details";
                      return (
                        <button
                          type="button"
                          key={key}
                          onClick={() => onLogReferenceSelect?.(ref)}
                          className="flex w-full flex-col gap-1 rounded-xl border border-blue-500/25 bg-blue-500/10 px-4 py-3 text-left text-sm text-blue-100 transition-colors hover:border-blue-400/50 hover:bg-blue-500/15"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-[15px] text-blue-50">
                              {title}
                            </span>
                            <span className="rounded-full border border-blue-300/40 bg-blue-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-blue-50">
                              {badge}
                            </span>
                          </div>
                          <div className="text-[12px] text-blue-100/80 line-clamp-2">
                            {summary}
                          </div>
                          <div className="mt-2 flex items-center gap-3 text-[11px] text-blue-100/70">
                            {count !== undefined && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-blue-500/25 px-2.5 py-0.5">
                                <span className="h-1.5 w-1.5 rounded-full bg-blue-200" />
                                {count} logs
                              </span>
                            )}
                            {ref.time_range && typeof ref.time_range === "object" && (
                              <span className="truncate">
                                {ref.time_range.start?.slice(11, 19)} → {ref.time_range.end?.slice(11, 19)}
                              </span>
                            )}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        <div className={metaClass}>
          {isPending ? "Thinking" : formatTimestamp(message.timestamp)}
        </div>
      </div>
    </div>
  );
};

export default ChatMessageBubble;
