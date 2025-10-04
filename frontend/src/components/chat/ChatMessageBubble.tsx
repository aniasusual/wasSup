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
      <h1 className="text-xl font-semibold tracking-tight text-blue-100" {...props} />
    ),
    h2: (props: ComponentPropsWithoutRef<"h2">) => (
      <h2 className="text-lg font-semibold text-blue-100 border-l-2 border-blue-500/50 pl-3" {...props} />
    ),
    h3: (props: ComponentPropsWithoutRef<"h3">) => (
      <h3 className="text-base font-semibold text-blue-50 mt-4" {...props} />
    ),
    p: (props: ComponentPropsWithoutRef<"p">) => (
      <p
        className="leading-relaxed text-[15px] text-slate-100/90"
        {...props}
      />
    ),
    ul: (props: ComponentPropsWithoutRef<"ul">) => (
      <ul
        className="space-y-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-100/90"
        {...props}
      />
    ),
    ol: (props: ComponentPropsWithoutRef<"ol">) => (
      <ol
        className="space-y-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-100/90 list-decimal list-inside"
        {...props}
      />
    ),
    li: (props: ComponentPropsWithoutRef<"li">) => (
      <li
        className="relative pl-4 text-[15px] text-slate-100/90 before:absolute before:left-0 before:top-2.5 before:h-1.5 before:w-1.5 before:rounded-full before:bg-blue-300/70"
        {...props}
      />
    ),
    strong: (props: ComponentPropsWithoutRef<"strong">) => (
      <strong className="text-blue-200 font-semibold" {...props} />
    ),
    em: (props: ComponentPropsWithoutRef<"em">) => (
      <em className="text-blue-100/80" {...props} />
    ),
    blockquote: (props: ComponentPropsWithoutRef<"blockquote">) => (
      <blockquote
        className="border-l-4 border-blue-500/60 bg-blue-500/10 text-blue-100/90 italic px-4 py-3 rounded-r-xl"
        {...props}
      />
    ),
    code: (props: ComponentPropsWithoutRef<"code">) => (
      <code
        className="rounded-md bg-slate-900/90 px-2 py-[3px] text-[12px] text-blue-200"
        {...props}
      />
    ),
    pre: (props: ComponentPropsWithoutRef<"pre">) => (
      <pre
        className="overflow-x-auto rounded-xl border border-white/10 bg-[#05060f]/95 p-4 text-[13px] leading-relaxed text-blue-100"
        {...props}
      />
    ),
    a: (props: ComponentPropsWithoutRef<"a">) => (
      <a
        className="text-sky-300 underline decoration-dotted underline-offset-4 transition-colors hover:text-sky-200"
        target="_blank"
        rel="noreferrer"
        {...props}
      />
    ),
    hr: () => <hr className="my-6 border-t border-blue-500/20" />,
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
                  ? {
                      start:
                        typeof (timeRangeValue as Record<string, unknown>).start === "string"
                          ? (timeRangeValue as Record<string, unknown>).start
                          : undefined,
                      end:
                        typeof (timeRangeValue as Record<string, unknown>).end === "string"
                          ? (timeRangeValue as Record<string, unknown>).end
                          : undefined,
                    }
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
  const bubbleBase = "relative rounded-3xl px-5 py-4 text-sm transition-all duration-200";
  const assistantTone =
    "bg-slate-950/85 text-slate-100 border border-white/10 shadow-[0_16px_36px_rgba(8,18,36,0.45)] backdrop-blur-sm";
  const userTone =
    "bg-gradient-to-br from-blue-600 via-blue-500 to-indigo-500 text-white shadow-[0_12px_24px_rgba(37,99,235,0.45)]";
  const bubbleTone = isUser ? userTone : assistantTone;
  const interactiveTone = isUser
    ? "hover:-translate-y-0.5"
    : "hover:-translate-y-0.5 hover:border-blue-400/40";
  const pendingClass = isPending && !isUser ? " animate-pulse" : "";
  const bubbleWidthClass = isUser ? "" : " w-full";
  const metaClass = `mt-2 text-[10px] uppercase tracking-wide ${
    isUser ? "text-blue-200/80 text-right" : "text-slate-500"
  }`;

  return (
    <div className={wrapperClass}>
      <div className={containerWidthClass}>
        <div className={`${bubbleBase} ${bubbleTone} ${interactiveTone}${pendingClass}${bubbleWidthClass}`}>
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
                <div className="border-t border-white/10 pt-4">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-blue-300/80">
                    Relevant logs
                  </p>
                  <div className="mt-3 flex flex-wrap gap-3">
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
                          className="group relative flex w-full flex-col gap-1 overflow-hidden rounded-xl border border-blue-500/25 bg-blue-500/15 px-4 py-3 text-left text-sm text-blue-100 transition-transform duration-200 hover:-translate-y-1 hover:border-blue-400/50 hover:bg-blue-500/20"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-[15px] text-blue-50">
                              {title}
                            </span>
                            <span className="rounded-full border border-blue-300/40 bg-blue-500/20 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-blue-50">
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
