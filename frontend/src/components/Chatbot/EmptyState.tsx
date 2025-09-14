import React from "react";
import { Brain } from "lucide-react";

interface EmptyStateProps {
  currentSessionId: string | null;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ currentSessionId }) => {
  const exampleQueries = [
    {
      query: "Show me **authentication errors** from `cloud_run_revision` services in the last hour",
      color: "text-blue-400"
    },
    {
      query: "Find *performance issues* in my `gce_instance` logs",
      color: "text-green-400"
    },
    {
      query: "Check for **5xx errors** in my load balancer logs",
      color: "text-purple-400"
    }
  ];

  return (
    <div className="text-center text-slate-400 mt-12">
      <div className="mb-4 mx-auto w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/30 to-purple-600/30 border border-slate-700/40 flex items-center justify-center">
        <Brain className="w-6 h-6 text-blue-400" />
      </div>
      <h3 className="text-lg font-semibold text-slate-200 mb-2">Meet Chico</h3>
      <p className="text-sm text-slate-400 mb-4 max-w-xl mx-auto">
        Your log assistant. Ask a question to begin.
      </p>

      <div className="mt-2 flex flex-col gap-2 max-w-2xl mx-auto text-left">
        {exampleQueries.map((example, index) => (
          <div key={index} className="p-3 bg-slate-800/30 rounded-lg border border-slate-700/40 hover:bg-slate-800/50 transition-colors cursor-pointer">
            <span className={example.color}>"{example.query}"</span>
          </div>
        ))}
      </div>
    </div>
  );
};
