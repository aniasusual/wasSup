import { useState } from "react";
import { ChevronDown, ChevronRight, Copy } from "lucide-react";
import { JsonViewer } from "./JsonViewer";

export const LogEntry = ({ log }: any) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copiedField, setCopiedField] = useState(null);

  const getSeverityColor = (severity: any) => {
    switch (severity?.toLowerCase()) {
      case "error":
        return "text-red-400 bg-red-900/20";
      case "warning":
        return "text-yellow-400 bg-yellow-900/20";
      case "info":
        return "text-blue-400 bg-blue-900/20";
      case "debug":
        return "text-green-400 bg-green-900/20";
      default:
        return "text-gray-400 bg-gray-900/20";
    }
  };

  const copyToClipboard = (text: any, fieldName: any) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const formatTimestamp = (timestamp: any) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  // Extract main message from various payload types
  const getMainMessage = () => {
    if (log.textPayload) return log.textPayload;
    if (log.jsonPayload?.message) return log.jsonPayload.message;
    if (log.jsonPayload && typeof log.jsonPayload === "string")
      return log.jsonPayload;
    return "No message content";
  };

  const renderField = (label: any, value: any, fieldKey: any) => {
    if (!value) return null;

    return (
      <div className="mb-3">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
            {label}
          </span>
          <button
            onClick={() =>
              copyToClipboard(JSON.stringify(value, null, 2), fieldKey)
            }
            className="text-gray-500 hover:text-gray-300 transition-colors"
            title="Copy to clipboard"
          >
            <Copy size={12} />
          </button>
          {copiedField === fieldKey && (
            <span className="text-xs text-green-400">Copied!</span>
          )}
        </div>
        <div className="bg-gray-800 rounded-md p-3 border border-gray-700">
          {typeof value === "object" ? (
            <JsonViewer data={value} />
          ) : (
            <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
              {value}
            </pre>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-700 transition-all">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <span
              className={`text-xs font-bold px-2 py-1 rounded ${getSeverityColor(
                log.severity
              )}`}
            >
              {log.severity || "INFO"}
            </span>
            <span className="text-xs text-gray-500">
              {formatTimestamp(log.timestamp)}
            </span>
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-gray-200 transition-colors"
            title={isExpanded ? "Collapse" : "Expand details"}
          >
            {isExpanded ? (
              <ChevronDown size={16} />
            ) : (
              <ChevronRight size={16} />
            )}
          </button>
        </div>

        {/* Main message */}
        <div className="text-gray-300 text-sm font-mono mb-2">
          {getMainMessage()}
        </div>

        {/* Resource info */}
        {log.resource && (
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>Resource: {log.resource.type}</span>
            {log.labels?.service && <span>Service: {log.labels.service}</span>}
            {log.labels?.version && <span>Version: {log.labels.version}</span>}
          </div>
        )}
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="p-4 space-y-4">
          {renderField("Resource", log.resource, "resource")}
          {renderField("JSON Payload", log.jsonPayload, "jsonPayload")}
          {renderField("Text Payload", log.textPayload, "textPayload")}
          {renderField("HTTP Request", log.httpRequest, "httpRequest")}
          {renderField("Labels", log.labels, "labels")}
          {renderField("Source Location", log.sourceLocation, "sourceLocation")}
          {renderField("Operation", log.operation, "operation")}

          {/* Any additional fields */}
          {Object.entries(log).map(([key, value]) => {
            if (
              [
                "id",
                "timestamp",
                "severity",
                "resource",
                "jsonPayload",
                "textPayload",
                "httpRequest",
                "labels",
                "sourceLocation",
                "operation",
              ].includes(key)
            ) {
              return null;
            }
            return renderField(key, value, key);
          })}
        </div>
      )}
    </div>
  );
};
