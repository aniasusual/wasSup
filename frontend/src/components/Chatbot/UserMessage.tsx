import React from "react";
import { User } from "lucide-react";

interface UserMessageProps {
  text: string;
  timestamp: string;
}

export const UserMessage: React.FC<UserMessageProps> = ({ text, timestamp }) => {
  return (
    <div className="flex justify-end mb-5 animate-slide-up">
      <div className="flex items-start gap-2.5 max-w-[85%]">
        <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-gradient-to-br from-slate-600 to-slate-700 border border-slate-500/50 flex items-center justify-center shadow-md">
          <User className="w-4 h-4 text-white" />
        </div>
        <div className="rounded-xl px-5 py-3 border bg-blue-600 text-white border-blue-500/50">
          <p className="text-[13px] whitespace-pre-wrap leading-relaxed">
            {text}
          </p>
          <p className="text-[10px] mt-2 text-blue-100/80">
            {timestamp}
          </p>
        </div>
      </div>
    </div>
  );
};
