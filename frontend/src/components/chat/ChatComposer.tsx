import { useCallback } from "react";
import { ArrowUp } from "lucide-react";

interface ChatComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
  isBusy?: boolean;
  placeholder?: string;
}

export const ChatComposer = ({
  value,
  onChange,
  onSend,
  disabled,
  isBusy,
  placeholder = "Ask about incidents, timelines, or patterns...",
}: ChatComposerProps) => {
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        onSend();
      }
    },
    [onSend]
  );

  return (
    <div className="rounded-xl bg-gray-900/60 border border-gray-800 focus-within:border-blue-500/60 transition-colors">
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        rows={1}
        className="w-full resize-none bg-transparent px-4 pt-3 text-sm text-gray-100 placeholder-gray-500 focus:outline-none"
        placeholder={placeholder}
        disabled={disabled}
      />
      <div className="flex items-center justify-between px-3 pb-3">
        <span className="text-[11px] text-gray-500">Press Shift + Enter for a new line</span>
        <button
          type="button"
          onClick={onSend}
          disabled={disabled || isBusy || !value.trim()}
          className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-white hover:bg-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ArrowUp className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default ChatComposer;
