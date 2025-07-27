import { useState } from "react";
import { MessageSquare, Send } from "lucide-react";
import toast from "react-hot-toast";

type Message = {
  id: number;
  text: string;
  sender: "user" | "ai";
  timestamp: string;
};

export const Chatbot = ({ selectedServices }: any) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [isTyping, setIsTyping] = useState<boolean>(false);

  const sendMessage = () => {
    if (!input.trim()) return;

    const newMessage: Message = {
      id: Date.now(),
      text: input,
      sender: "user",
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev: Message[]) => [...prev, newMessage]);
    setInput("");
    setIsTyping(true);

    // Simulate AI response with error handling
    setTimeout(() => {
      try {
        const aiResponse: Message = {
          id: Date.now() + 1,
          text: `I've analyzed the logs from ${
            selectedServices?.length > 0
              ? "the selected services"
              : "all services"
          }. Based on your query "${input}", here's what I found...`,
          sender: "ai",
          timestamp: new Date().toLocaleTimeString(),
        };
        setMessages((prev: Message[]) => [...prev, aiResponse]);
      } catch (error) {
        console.error("Error generating AI response:", error);
        toast.error(
          `Failed to generate AI response: ${
            error instanceof Error ? error.message : String(error)
          }`
        );
      } finally {
        setIsTyping(false);
      }
    }, 1500);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="bg-gray-900 border-b border-gray-800 px-4 py-3">
        <h3 className="text-white font-medium flex items-center gap-2">
          <MessageSquare className="w-5 h-5" />
          Log Analysis Assistant
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-700" />
            <p className="text-sm">Ask me about your logs!</p>
            <p className="text-xs mt-2">
              Try: "Show me all errors in the last hour"
            </p>
          </div>
        )}

        {messages.map((message: Message) => (
          <div
            key={message.id}
            className={`flex ${
              message.sender === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.sender === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-300"
              }`}
            >
              <p className="text-sm">{message.text}</p>
              <p className="text-xs mt-1 opacity-70">{message.timestamp}</p>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-lg px-4 py-2">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-gray-800 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Ask about your logs..."
            className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
          <button
            onClick={sendMessage}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};
