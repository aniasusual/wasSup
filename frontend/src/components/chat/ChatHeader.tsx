import { Maximize2, Minimize2, RotateCcw, Sparkles } from "lucide-react";

interface ChatHeaderProps {
  isStreaming: boolean;
  isExpanded: boolean;
  onReset: () => void;
  onToggleExpand?: () => void;
}

export const ChatHeader = ({ isStreaming, isExpanded, onReset, onToggleExpand }: ChatHeaderProps) => {
  return (
    <div className="flex items-center justify-between border-b border-gray-800/80 px-4 py-3">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-500/20 text-blue-300">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-100">Investigation Assistant</h3>
          <p className="text-xs text-gray-500">
            {isStreaming ? "Analyzing signals..." : "Ready to collaborate"}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onReset}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-gray-800 bg-gray-900/60 text-gray-400 hover:text-gray-200 hover:border-gray-700 transition-colors"
          title="Reset conversation"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
        {onToggleExpand && (
          <button
            type="button"
            onClick={onToggleExpand}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-gray-800 bg-gray-900/60 text-gray-400 hover:text-gray-200 hover:border-gray-700 transition-colors"
            title={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
        )}
      </div>
    </div>
  );
};

export default ChatHeader;
