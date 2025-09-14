import React from "react";

export const TypingIndicator: React.FC = () => {
  return (
    <div className="w-full mb-8">
      <div className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur-xl border border-slate-700/50 rounded-3xl shadow-2xl overflow-hidden">
        <div className="p-8">
          <div className="flex items-center justify-center gap-4 text-slate-300">
            <div className="flex space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"></div>
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            <span className="text-lg font-medium">AI is analyzing your query...</span>
          </div>
        </div>
      </div>
    </div>
  );
};
