import React from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import {
  AlertTriangle,
  CheckCircle,
  Info,
  XCircle,
  Code,
  Database,
  Clock,
  Server,
  ExternalLink,
  Copy,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

interface RichTextRendererProps {
  content: string;
  className?: string;
}

interface LogEntry {
  id: string;
  timestamp: string;
  severity: string;
  message: string;
  serviceId?: string;
  traceId?: string;
}

interface StructuredData {
  type: "logs" | "metrics" | "insights" | "actions" | "code" | "table";
  data: any;
  title?: string;
  collapsible?: boolean;
}

export const RichTextRenderer: React.FC<RichTextRendererProps> = ({
  content,
  className = "",
}) => {
  const [copiedStates, setCopiedStates] = React.useState<
    Record<string, boolean>
  >({});
  const [collapsedSections, setCollapsedSections] = React.useState<
    Record<string, boolean>
  >({});

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedStates((prev) => ({ ...prev, [id]: true }));
      setTimeout(() => {
        setCopiedStates((prev) => ({ ...prev, [id]: false }));
      }, 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  const toggleCollapse = (id: string) => {
    setCollapsedSections((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case "ERROR":
        return <XCircle className="w-4 h-4 text-red-400" />;
      case "WARNING":
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      case "INFO":
        return <Info className="w-4 h-4 text-blue-400" />;
      case "DEBUG":
        return <Code className="w-4 h-4 text-gray-400" />;
      default:
        return <Info className="w-4 h-4 text-gray-400" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case "ERROR":
        return "border-red-500/50 bg-red-950/20";
      case "WARNING":
        return "border-yellow-500/50 bg-yellow-950/20";
      case "INFO":
        return "border-blue-500/50 bg-blue-950/20";
      case "DEBUG":
        return "border-gray-500/50 bg-gray-950/20";
      default:
        return "border-gray-500/50 bg-gray-950/20";
    }
  };

  const renderCodeBlock = (
    match: string,
    language: string,
    code: string,
    index: number
  ) => {
    const blockId = `code-${index}`;
    const isCollapsed = collapsedSections[blockId];

    return (
      <div
        key={index}
        className="my-4 rounded-lg border border-slate-700/50 overflow-hidden"
      >
        <div className="flex items-center justify-between bg-slate-800/50 px-4 py-2 border-b border-slate-700/50">
          <div className="flex items-center gap-2">
            <Code className="w-4 h-4 text-slate-400" />
            <span className="text-sm font-medium text-slate-300">
              {language || "Code"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => copyToClipboard(code, blockId)}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded transition-colors"
              title="Copy code"
            >
              {copiedStates[blockId] ? (
                <CheckCircle className="w-4 h-4 text-green-400" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
            <button
              onClick={() => toggleCollapse(blockId)}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 rounded transition-colors"
              title={isCollapsed ? "Expand" : "Collapse"}
            >
              {isCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
        {!isCollapsed && (
          <div className="max-h-96 overflow-auto">
            <SyntaxHighlighter
              language={language || "text"}
              style={vscDarkPlus}
              customStyle={{
                margin: 0,
                background: "transparent",
                fontSize: "0.875rem",
                lineHeight: "1.5",
              }}
              showLineNumbers={code.split("\n").length > 5}
              wrapLines={true}
              wrapLongLines={true}
            >
              {code}
            </SyntaxHighlighter>
          </div>
        )}
      </div>
    );
  };

  const renderLogEntry = (log: LogEntry, index: number) => {
    const severityColor = getSeverityColor(log.severity);
    const severityIcon = getSeverityIcon(log.severity);

    return (
      <div
        key={log.id || index}
        className={`p-3 rounded-lg border ${severityColor} hover:bg-opacity-30 transition-colors`}
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">{severityIcon}</div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono text-slate-400">
                {new Date(log.timestamp).toLocaleString()}
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700/50 text-slate-300">
                {log.severity}
              </span>
              {log.serviceId && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-900/30 text-blue-300 flex items-center gap-1">
                  <Server className="w-3 h-3" />
                  {log.serviceId}
                </span>
              )}
              {log.traceId && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-purple-900/30 text-purple-300 font-mono">
                  {log.traceId.slice(0, 8)}...
                </span>
              )}
            </div>
            <div className="text-sm text-slate-200 whitespace-pre-wrap break-words">
              {log.message}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderStructuredData = (data: StructuredData, index: number) => {
    const sectionId = `section-${index}`;
    const isCollapsed = collapsedSections[sectionId];

    const renderContent = () => {
      switch (data.type) {
        case "logs":
          return (
            <div className="space-y-2">
              {data.data.map((log: LogEntry, logIndex: number) =>
                renderLogEntry(log, logIndex)
              )}
            </div>
          );

        case "metrics":
          return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(data.data).map(([key, value]: [string, any]) => (
                <div
                  key={key}
                  className="p-3 bg-slate-800/30 rounded-lg border border-slate-700/50"
                >
                  <div className="text-xs text-slate-400 mb-1">{key}</div>
                  <div className="text-lg font-semibold text-slate-200">
                    {value}
                  </div>
                </div>
              ))}
            </div>
          );

        case "insights":
          return (
            <div className="space-y-3">
              {data.data.map((insight: any, insightIndex: number) => (
                <div
                  key={insightIndex}
                  className="p-3 bg-blue-950/20 border border-blue-800/50 rounded-lg"
                >
                  <div className="flex items-start gap-2">
                    <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="text-sm font-medium text-blue-300 mb-1">
                        {insight.title || "Insight"}
                      </div>
                      <div className="text-sm text-blue-200">
                        {insight.description}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          );

        case "actions":
          return (
            <div className="space-y-2">
              {data.data.map((action: any, actionIndex: number) => (
                <button
                  key={actionIndex}
                  className="w-full p-3 text-left bg-slate-800/30 hover:bg-slate-700/30 border border-slate-700/50 rounded-lg transition-colors"
                  onClick={() => {
                    console.log("Action clicked:", action);
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-slate-200">
                        {action.label}
                      </div>
                      {action.description && (
                        <div className="text-xs text-slate-400 mt-1">
                          {action.description}
                        </div>
                      )}
                    </div>
                    <ExternalLink className="w-4 h-4 text-slate-400" />
                  </div>
                </button>
              ))}
            </div>
          );

        case "table":
          const headers = Object.keys(data.data[0] || {});
          return (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    {headers.map((header) => (
                      <th
                        key={header}
                        className="text-left py-2 px-3 text-slate-300 font-medium"
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.data.map((row: any, rowIndex: number) => (
                    <tr
                      key={rowIndex}
                      className="border-b border-slate-800/50 hover:bg-slate-800/20"
                    >
                      {headers.map((header) => (
                        <td key={header} className="py-2 px-3 text-slate-200">
                          {row[header]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );

        default:
          return (
            <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-700/50">
              <pre className="text-sm text-slate-200 whitespace-pre-wrap">
                {JSON.stringify(data.data, null, 2)}
              </pre>
            </div>
          );
      }
    };

    return (
      <div
        key={index}
        className="my-4 rounded-lg border border-slate-700/50 overflow-hidden"
      >
        <div
          className="flex items-center justify-between bg-slate-800/50 px-4 py-3 border-b border-slate-700/50 cursor-pointer hover:bg-slate-700/50 transition-colors"
          onClick={() => data.collapsible && toggleCollapse(sectionId)}
        >
          <div className="flex items-center gap-2">
            {data.type === "logs" && (
              <Database className="w-4 h-4 text-slate-400" />
            )}
            {data.type === "metrics" && (
              <Server className="w-4 h-4 text-slate-400" />
            )}
            {data.type === "insights" && (
              <Info className="w-4 h-4 text-slate-400" />
            )}
            {data.type === "actions" && (
              <ExternalLink className="w-4 h-4 text-slate-400" />
            )}
            {data.type === "table" && (
              <Database className="w-4 h-4 text-slate-400" />
            )}
            <span className="text-sm font-medium text-slate-300">
              {data.title ||
                `${data.type.charAt(0).toUpperCase() + data.type.slice(1)}`}
            </span>
            <span className="text-xs text-slate-500">
              (
              {Array.isArray(data.data)
                ? data.data.length
                : Object.keys(data.data).length}{" "}
              items)
            </span>
          </div>
          {data.collapsible && (
            <button className="p-1 text-slate-400 hover:text-slate-200 transition-colors">
              {isCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
        {(!data.collapsible || !isCollapsed) && (
          <div className="p-4">{renderContent()}</div>
        )}
      </div>
    );
  };

  const parseContent = (content: string) => {
    const elements: React.ReactNode[] = [];
    let currentIndex = 0;

    // Parse structured data blocks (JSON-like objects)
    const structuredDataRegex =
      /```(?:json|data|logs|metrics|insights|actions|table)\n([\s\S]*?)\n```/g;
    let match;
    let lastIndex = 0;

    while ((match = structuredDataRegex.exec(content)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        const textContent = content.slice(lastIndex, match.index);
        elements.push(parseMarkdown(textContent, currentIndex));
        currentIndex++;
      }

      // Parse structured data
      try {
        const data = JSON.parse(match[1]);
        const type = match[0].includes("logs")
          ? "logs"
          : match[0].includes("metrics")
          ? "metrics"
          : match[0].includes("insights")
          ? "insights"
          : match[0].includes("actions")
          ? "actions"
          : match[0].includes("table")
          ? "table"
          : "json";

        elements.push(
          renderStructuredData({ type, data, collapsible: true }, currentIndex)
        );
        currentIndex++;
      } catch (e) {
        // If JSON parsing fails, treat as regular code block
        elements.push(
          renderCodeBlock(match[0], "json", match[1], currentIndex)
        );
        currentIndex++;
      }

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < content.length) {
      const textContent = content.slice(lastIndex);
      elements.push(parseMarkdown(textContent, currentIndex));
    }

    return elements;
  };

  const parseMarkdown = (text: string, startIndex: number): React.ReactNode => {
    const elements: React.ReactNode[] = [];
    let currentIndex = startIndex;

    // Parse code blocks
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)\n```/g;
    let match;
    let lastIndex = 0;

    while ((match = codeBlockRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        const textContent = text.slice(lastIndex, match.index);
        elements.push(parseInlineMarkdown(textContent, currentIndex));
        currentIndex++;
      }

      // Add code block
      elements.push(
        renderCodeBlock(match[0], match[1] || "text", match[2], currentIndex)
      );
      currentIndex++;

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const textContent = text.slice(lastIndex);
      elements.push(parseInlineMarkdown(textContent, currentIndex));
    }

    return elements.length === 1 ? (
      elements[0]
    ) : (
      <div key={startIndex}>{elements}</div>
    );
  };

  const parseInlineMarkdown = (
    text: string,
    startIndex: number
  ): React.ReactNode => {
    const elements: React.ReactNode[] = [];
    let currentIndex = startIndex;

    // Parse inline code
    const inlineCodeRegex = /`([^`]+)`/g;
    let match;
    let lastIndex = 0;

    while ((match = inlineCodeRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        const textContent = text.slice(lastIndex, match.index);
        elements.push(parseBasicFormatting(textContent, currentIndex));
        currentIndex++;
      }

      // Add inline code
      elements.push(
        <code
          key={currentIndex}
          className="px-1.5 py-0.5 bg-slate-800/50 text-slate-200 rounded text-sm font-mono border border-slate-700/50"
        >
          {match[1]}
        </code>
      );
      currentIndex++;

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const textContent = text.slice(lastIndex);
      elements.push(parseBasicFormatting(textContent, currentIndex));
    }

    return elements.length === 1 ? (
      elements[0]
    ) : (
      <span key={startIndex}>{elements}</span>
    );
  };

  const parseBasicFormatting = (
    text: string,
    startIndex: number
  ): React.ReactNode => {
    const elements: React.ReactNode[] = [];
    let currentIndex = startIndex;

    // Parse bold text
    const boldRegex = /\*\*(.*?)\*\*/g;
    let match;
    let lastIndex = 0;

    while ((match = boldRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        const textContent = text.slice(lastIndex, match.index);
        elements.push(parseItalic(textContent, currentIndex));
        currentIndex++;
      }

      // Add bold text
      elements.push(
        <strong key={currentIndex} className="font-semibold text-slate-100">
          {match[1]}
        </strong>
      );
      currentIndex++;

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const textContent = text.slice(lastIndex);
      elements.push(parseItalic(textContent, currentIndex));
    }

    return elements.length === 1 ? (
      elements[0]
    ) : (
      <span key={startIndex}>{elements}</span>
    );
  };

  const parseItalic = (text: string, startIndex: number): React.ReactNode => {
    const elements: React.ReactNode[] = [];
    let currentIndex = startIndex;

    // Parse italic text
    const italicRegex = /\*(.*?)\*/g;
    let match;
    let lastIndex = 0;

    while ((match = italicRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        const textContent = text.slice(lastIndex, match.index);
        elements.push(parseLinks(textContent, currentIndex));
        currentIndex++;
      }

      // Add italic text
      elements.push(
        <em key={currentIndex} className="italic text-slate-200">
          {match[1]}
        </em>
      );
      currentIndex++;

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const textContent = text.slice(lastIndex);
      elements.push(parseLinks(textContent, currentIndex));
    }

    return elements.length === 1 ? (
      elements[0]
    ) : (
      <span key={startIndex}>{elements}</span>
    );
  };

  const parseLinks = (text: string, startIndex: number): React.ReactNode => {
    const elements: React.ReactNode[] = [];
    let currentIndex = startIndex;

    // Parse links
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    let match;
    let lastIndex = 0;

    while ((match = linkRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        const textContent = text.slice(lastIndex, match.index);
        elements.push(parseLineBreaks(textContent, currentIndex));
        currentIndex++;
      }

      // Add link
      elements.push(
        <a
          key={currentIndex}
          href={match[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-400 hover:text-blue-300 underline transition-colors"
        >
          {match[1]}
        </a>
      );
      currentIndex++;

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const textContent = text.slice(lastIndex);
      elements.push(parseLineBreaks(textContent, currentIndex));
    }

    return elements.length === 1 ? (
      elements[0]
    ) : (
      <span key={startIndex}>{elements}</span>
    );
  };

  const parseLineBreaks = (
    text: string,
    startIndex: number
  ): React.ReactNode => {
    if (!text) return null;

    const lines = text.split("\n");
    if (lines.length === 1) {
      return <span key={startIndex}>{text}</span>;
    }

    return (
      <span key={startIndex}>
        {lines.map((line, index) => (
          <React.Fragment key={index}>
            {line}
            {index < lines.length - 1 && <br />}
          </React.Fragment>
        ))}
      </span>
    );
  };

  return (
    <div className={`rich-text-content ${className}`}>
      {parseContent(content)}
    </div>
  );
};

export default RichTextRenderer;
