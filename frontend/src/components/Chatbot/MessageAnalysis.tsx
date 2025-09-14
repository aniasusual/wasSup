import React from "react";
import { ProperMarkdownRenderer } from "./ProperMarkdownRenderer";

interface MessageAnalysisProps {
  analysis: string;
  isStreaming?: boolean;
  // Keeping optional props for compatibility, but unused to reduce noise
  metadata?: any;
  needsClarification?: boolean;
  clarifyingQuestions?: Array<{ question: string; context: string }>;
  missingInfo?: string[];
  toolResults?: any;
  completeResult?: any;
}

export const MessageAnalysis: React.FC<MessageAnalysisProps> = ({ analysis, isStreaming = false }) => {
  return (
    <div className="space-y-4">
      {analysis ? (
        <div className="relative">
          <ProperMarkdownRenderer content={analysis} />
          {isStreaming && (
            <div className="absolute bottom-0 right-0 w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          )}
        </div>
      ) : isStreaming ? (
        <div className="flex items-center justify-center gap-3 text-slate-300 py-6">
          <div className="flex space-x-1.5">
            <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce"></div>
            <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
          <span className="text-sm font-medium">Thinking…</span>
        </div>
      ) : null}
    </div>
  );
};

