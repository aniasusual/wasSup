import { useEffect, useRef } from "react";
import type { ChatLogReference, ChatMessage } from "../../types/chat";
import { ChatMessageBubble } from "./ChatMessageBubble";

interface ChatMessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  onLogReferenceSelect?: (reference: ChatLogReference) => void;
}

export const ChatMessageList = ({
  messages,
  isStreaming,
  onLogReferenceSelect,
}: ChatMessageListProps) => {
  const scrollAnchorRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  if (messages.length === 0) {
    return (
      <div className="flex min-h-[120px] items-center justify-center rounded-xl border border-gray-800/60 bg-gray-950/70 px-4 py-6 text-center text-sm text-gray-500">
        Start the conversation to kick off an investigation.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <ChatMessageBubble
          key={message.id}
          message={message}
          onLogReferenceSelect={onLogReferenceSelect}
        />
      ))}
      <div ref={scrollAnchorRef} />
    </div>
  );
};

export default ChatMessageList;
