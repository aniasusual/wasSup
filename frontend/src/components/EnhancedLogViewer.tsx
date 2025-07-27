import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  Info,
  Bug,
  MessageSquare,
} from "lucide-react";
import type { LogEntry } from "../types/gcp";

interface EnhancedLogViewerProps {
  logs: LogEntry[];
  className?: string;
}

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case "ERROR":
      return <AlertTriangle className="w-4 h-4 text-red-500" />;
    case "WARNING":
      return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    case "INFO":
      return <Info className="w-4 h-4 text-blue-500" />;
    case "DEBUG":
      return <Bug className="w-4 h-4 text-gray-500" />;
    default:
      return <MessageSquare className="w-4 h-4 text-gray-500" />;
  }
};

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case "ERROR":
      return "border-l-red-500 bg-red-500/10";
    case "WARNING":
      return "border-l-yellow-500 bg-yellow-500/10";
    case "INFO":
      return "border-l-blue-500 bg-blue-500/10";
    case "DEBUG":
      return "border-l-gray-500 bg-gray-500/10";
    default:
      return "border-l-gray-500 bg-gray-500/10";
  }
};

const formatTimestamp = (timestamp: string | Date | null) => {
  if (!timestamp) {
    return {
      exact: "No timestamp",
      relative: "No timestamp",
      full: "No timestamp",
    };
  }

  const now = new Date();
  const timestampDate =
    typeof timestamp === "string" ? new Date(timestamp) : timestamp;

  // Check if the date is valid
  if (isNaN(timestampDate.getTime())) {
    return {
      exact: "Invalid date",
      relative: "Invalid date",
      full: "Invalid date",
    };
  }

  // Format exact timestamp with timezone
  const exactTime =
    timestampDate.toLocaleString("en-US", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }) + ` ${timestampDate.getMilliseconds().toString().padStart(3, "0")}ms`;

  // Calculate relative time
  const diff = now.getTime() - timestampDate.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  let relativeTime = "Just now";
  if (days > 0) relativeTime = `${days}d ago`;
  else if (hours > 0) relativeTime = `${hours}h ago`;
  else if (minutes > 0) relativeTime = `${minutes}m ago`;

  return {
    exact: exactTime,
    relative: relativeTime,
    full: `${exactTime} (${relativeTime})`,
  };
};

const LogEntryComponent = ({ log }: { log: LogEntry }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Always allow expand/collapse, not just for structured data
  const logMessage = log.message || log.textPayload || "No message";
  const previewMessage =
    logMessage.length > 200
      ? logMessage.slice(0, 200) + "..."
      : logMessage.split("\n")[0];
  const hasStructuredData =
    log.jsonPayload || log.httpRequest || log.traceId || log.spanId;

  // Helper function to get formatted timestamp
  const getFormattedTimestamp = () => {
    const formatted = formatTimestamp(log.timestamp);
    return {
      display: formatted.full,
      tooltip: formatted.exact,
    };
  };

  return (
    <div
      className={`border-l-4 ${getSeverityColor(
        log.severity
      )} bg-gray-900 hover:bg-gray-800 transition-colors`}
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {getSeverityIcon(log.severity)}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 text-sm">
                <span
                  className="text-gray-400 font-mono"
                  title={getFormattedTimestamp().tooltip}
                >
                  {getFormattedTimestamp().display}
                </span>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    log.severity === "ERROR"
                      ? "bg-red-600 text-white"
                      : log.severity === "WARNING"
                      ? "bg-yellow-600 text-white"
                      : log.severity === "INFO"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-600 text-white"
                  }`}
                >
                  {log.severity}
                </span>
                {log.traceId && (
                  <span className="text-xs text-gray-500 font-mono">
                    Trace: {log.traceId.slice(0, 8)}...
                  </span>
                )}
              </div>
              <div className="mt-1 text-white font-medium break-words whitespace-pre-line">
                {isExpanded ? logMessage : previewMessage}
              </div>
            </div>
          </div>

          {/* Always show expand/collapse button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex-shrink-0 p-1 text-gray-400 hover:text-white transition-colors"
            title={isExpanded ? "Collapse log" : "Expand log"}
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Resource Info */}
        {log.resource && (
          <div className="mt-2 text-sm text-gray-400">
            <span className="font-medium">Resource:</span> {log.resource.type}
            {log.resource.labels &&
              Object.entries(log.resource.labels).map(([key, value]) => (
                <span key={key} className="ml-2">
                  {key}={value}
                </span>
              ))}
          </div>
        )}

        {/* Labels */}
        {log.labels && Object.keys(log.labels).length > 0 && (
          <div className="mt-2 text-sm text-gray-400">
            <span className="font-medium">Labels:</span>
            {Object.entries(log.labels).map(([key, value]) => (
              <span key={key} className="ml-2">
                {key}={value}
              </span>
            ))}
          </div>
        )}

        {/* Detailed Timestamp Info */}
        {isExpanded && (
          <div className="mt-4 p-3 bg-gray-800 rounded-lg">
            <h4 className="text-sm font-medium text-gray-300 mb-2">
              Timestamp Details
            </h4>
            <div className="text-xs text-gray-400 space-y-1">
              <div>Exact Time: {formatTimestamp(log.timestamp).exact}</div>
              <div>
                Relative Time: {formatTimestamp(log.timestamp).relative}
              </div>
              <div>ISO Format: {String(log.timestamp)}</div>
              <div>
                Unix Timestamp: {new Date(log.timestamp).getTime().toString()}
              </div>
            </div>
          </div>
        )}

        {/* Expanded Structured Data */}
        {isExpanded && hasStructuredData && (
          <div className="mt-4 p-3 bg-gray-800 rounded-lg">
            <h4 className="text-sm font-medium text-gray-300 mb-2">
              Structured Data
            </h4>

            {/* HTTP Request */}
            {log.httpRequest && (
              <div className="mb-3">
                <h5 className="text-xs font-medium text-gray-400 mb-1">
                  HTTP Request
                </h5>
                <div className="text-xs text-gray-300 space-y-1">
                  <div>Method: {log.httpRequest.requestMethod}</div>
                  <div>URL: {log.httpRequest.requestUrl}</div>
                  <div>Status: {log.httpRequest.status}</div>
                  <div>Response Size: {log.httpRequest.responseSize}</div>
                  <div>User Agent: {log.httpRequest.userAgent}</div>
                </div>
              </div>
            )}

            {/* JSON Payload */}
            {log.jsonPayload && (
              <div className="mb-3">
                <h5 className="text-xs font-medium text-gray-400 mb-1">
                  JSON Payload
                </h5>
                <pre className="text-xs text-gray-300 bg-gray-900 p-2 rounded overflow-x-auto">
                  {JSON.stringify(log.jsonPayload, null, 2)}
                </pre>
              </div>
            )}

            {/* Trace Information */}
            {(log.traceId || log.spanId) && (
              <div>
                <h5 className="text-xs font-medium text-gray-400 mb-1">
                  Trace Information
                </h5>
                <div className="text-xs text-gray-300 space-y-1">
                  {log.traceId && <div>Trace ID: {log.traceId}</div>}
                  {log.spanId && <div>Span ID: {log.spanId}</div>}
                </div>
              </div>
            )}
          </div>
        )}
        {/* Show full log object as JSON when expanded */}
        {isExpanded && (
          <div className="mt-4 p-3 bg-gray-900 rounded-lg">
            <h4 className="text-sm font-medium text-gray-300 mb-2">
              Full Log Object
            </h4>
            <pre className="text-xs text-gray-200 bg-gray-950 p-2 rounded overflow-x-auto">
              {JSON.stringify(log, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export const EnhancedLogViewer = ({
  logs,
  className = "",
}: EnhancedLogViewerProps) => {
  if (logs.length === 0) {
    return (
      <div
        className={`flex items-center justify-center p-8 text-gray-400 ${className}`}
      >
        <div className="text-center">
          <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-600" />
          <p className="text-lg font-medium">No logs found</p>
          <p className="text-sm">Try adjusting your filters or time range</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-1 ${className}`}>
      {logs.map((log) => (
        <LogEntryComponent key={log.id} log={log} />
      ))}
    </div>
  );
};
