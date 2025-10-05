import type { ChatSuggestion } from "../../types/chat";

interface ChatSuggestionBarProps {
  suggestions: ChatSuggestion[];
  disabled?: boolean;
  onSelect: (prompt: string) => void;
}

export const ChatSuggestionBar = ({ suggestions, disabled, onSelect }: ChatSuggestionBarProps) => {
  if (!suggestions.length) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion.id}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(suggestion.prompt)}
          className="px-3 py-1.5 rounded-full border border-blue-500/40 text-xs font-medium text-blue-100/90 bg-blue-500/10 hover:bg-blue-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {suggestion.label}
        </button>
      ))}
    </div>
  );
};

export default ChatSuggestionBar;
