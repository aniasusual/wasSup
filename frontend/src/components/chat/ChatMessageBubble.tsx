import type { ChatMessage } from "../../types/chat";

interface ChatMessageBubbleProps {
  message: ChatMessage;
}

const formatTimestamp = (iso: string) => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

export const ChatMessageBubble = ({ message }: ChatMessageBubbleProps) => {
  const isUser = message.role === "user";
  const isPending = message.status === "pending";

  const wrapperClass = `flex w-full ${isUser ? "justify-end" : "justify-start"}`;
  const containerWidthClass = isUser
    ? "max-w-[88%] sm:max-w-[75%]"
    : "w-full";
  const bubbleBase = "rounded-2xl px-4 py-3 text-sm shadow-sm transition-colors";
  const bubbleTone = isUser
    ? "bg-blue-600 text-white"
    : "bg-gray-800/80 text-gray-100";
  const pendingClass = isPending && !isUser ? " animate-pulse" : "";
  const bubbleWidthClass = isUser ? "" : " w-full";
  const metaClass = `mt-1 text-[10px] uppercase tracking-wide ${
    isUser ? "text-blue-200/70 text-right" : "text-gray-500"
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
          ) : (
            <p className="whitespace-pre-line leading-relaxed">{message.content}</p>
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
