import React from "react";
import { MessageAnalysis } from "./MessageAnalysis";

interface AIMessageProps {
  text: string;
  completeResult?: any;
  actions?: any[];
  needsClarification?: boolean;
  isStreaming?: boolean;
}

export const AIMessage: React.FC<AIMessageProps> = ({
  text,
  completeResult,
  actions,
  needsClarification = false,
  isStreaming = false
}) => {
  return (
    <div className="w-full mb-6 animate-slide-up">
      {/* Main Analysis Content */}
      <div className="glass-card rounded-2xl overflow-hidden">
        {/* Content */}
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

        {/* Actions - compact chips, no heading */}
        {actions && actions.length > 0 && (
          <div className="px-5 pb-5">
            <div className="flex flex-wrap gap-2">
              {actions.map((action, index) => (
                <button
                  key={index}
                  className="px-3 py-1.5 bg-slate-800/50 hover:bg-slate-700/60 text-slate-200 text-xs rounded-md border border-slate-700/60 transition-colors"
                  onClick={() => {
                    console.log("Action clicked:", action);
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
