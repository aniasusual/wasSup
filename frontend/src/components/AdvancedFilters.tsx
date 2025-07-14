import { useState } from "react";
import { ChevronDown, ChevronUp, Filter } from "lucide-react";
import type { FilterState, GCPService } from "../types/gcp";

interface AdvancedFiltersProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  service?: GCPService;
  className?: string;
}

const SEVERITY_OPTIONS = ["ERROR", "WARNING", "INFO", "DEBUG"];
const TIME_RANGE_OPTIONS = [
  { value: "1h", label: "Last 1 hour" },
  { value: "6h", label: "Last 6 hours" },
  { value: "24h", label: "Last 24 hours" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "custom", label: "Custom range" },
];

export const AdvancedFilters = ({
  filters,
  onFiltersChange,
  service,
  className = "",
}: AdvancedFiltersProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const updateFilter = (key: keyof FilterState, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value,
    });
  };

  const clearFilter = (key: keyof FilterState) => {
    const newFilters = { ...filters };
    if (Array.isArray(filters[key])) {
      newFilters[key] = [] as any;
    } else {
      newFilters[key] = "" as any;
    }
    onFiltersChange(newFilters);
  };

  const clearAllFilters = () => {
    onFiltersChange({
      severity: [],
      resourceType: "",
      logType: [],
      sourceLocation: "",
      userAccount: "",
      requestId: "",
      timeRange: "1h",
      customQuery: "",
    });
  };

  const hasActiveFilters = Object.values(filters).some((value) =>
    Array.isArray(value) ? value.length > 0 : value !== "" && value !== "1h"
  );

  return (
    <div
      className={`bg-gray-900 border border-gray-800 rounded-lg ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-blue-500" />
          <h3 className="text-lg font-medium text-white">Advanced Filters</h3>
          {hasActiveFilters && (
            <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
              Active
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button
              onClick={clearAllFilters}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              Clear All
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-gray-400 hover:text-white transition-colors"
          >
            {isExpanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* Filters Content */}
      {isExpanded && (
        <div className="p-4 space-y-4">
          {/* Severity Filter */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">
                Severity
              </label>
              {filters.severity.length > 0 && (
                <button
                  onClick={() => clearFilter("severity")}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {SEVERITY_OPTIONS.map((severity) => (
                <button
                  key={severity}
                  onClick={() => {
                    const newSeverity = filters.severity.includes(severity)
                      ? filters.severity.filter((s) => s !== severity)
                      : [...filters.severity, severity];
                    updateFilter("severity", newSeverity);
                  }}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    filters.severity.includes(severity)
                      ? "bg-blue-600 text-white"
                      : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                  }`}
                >
                  {severity}
                </button>
              ))}
            </div>
          </div>

          {/* Time Range Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">
              Time Range
            </label>
            <select
              value={filters.timeRange}
              onChange={(e) => updateFilter("timeRange", e.target.value)}
              className="w-full p-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
            >
              {TIME_RANGE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Resource Type Filter */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">
                Resource Type
              </label>
              {filters.resourceType && (
                <button
                  onClick={() => clearFilter("resourceType")}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>
            <input
              type="text"
              value={filters.resourceType}
              onChange={(e) => updateFilter("resourceType", e.target.value)}
              placeholder="e.g., gce_instance, k8s_container"
              className="w-full p-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Log Type Filter */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">
                Log Type
              </label>
              {filters.logType.length > 0 && (
                <button
                  onClick={() => clearFilter("logType")}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {service?.logTypes.map((logType) => (
                <button
                  key={logType}
                  onClick={() => {
                    const newLogType = filters.logType.includes(logType)
                      ? filters.logType.filter((t) => t !== logType)
                      : [...filters.logType, logType];
                    updateFilter("logType", newLogType);
                  }}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    filters.logType.includes(logType)
                      ? "bg-green-600 text-white"
                      : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                  }`}
                >
                  {logType}
                </button>
              ))}
            </div>
          </div>

          {/* Source Location Filter */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">
                Source Location
              </label>
              {filters.sourceLocation && (
                <button
                  onClick={() => clearFilter("sourceLocation")}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>
            <input
              type="text"
              value={filters.sourceLocation}
              onChange={(e) => updateFilter("sourceLocation", e.target.value)}
              placeholder="File path, function name, line number"
              className="w-full p-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* User Account Filter */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">
                User/Service Account
              </label>
              {filters.userAccount && (
                <button
                  onClick={() => clearFilter("userAccount")}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>
            <input
              type="text"
              value={filters.userAccount}
              onChange={(e) => updateFilter("userAccount", e.target.value)}
              placeholder="user@example.com or service-account@project.iam.gserviceaccount.com"
              className="w-full p-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Request ID Filter */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">
                Request ID/Trace ID
              </label>
              {filters.requestId && (
                <button
                  onClick={() => clearFilter("requestId")}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>
            <input
              type="text"
              value={filters.requestId}
              onChange={(e) => updateFilter("requestId", e.target.value)}
              placeholder="Request ID or Trace ID for distributed tracing"
              className="w-full p-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Custom Query Filter */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-300">
                Custom Query
              </label>
              {filters.customQuery && (
                <button
                  onClick={() => clearFilter("customQuery")}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>
            <textarea
              value={filters.customQuery}
              onChange={(e) => updateFilter("customQuery", e.target.value)}
              placeholder="Advanced GCP Cloud Logging query syntax..."
              rows={3}
              className="w-full p-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 font-mono text-sm"
            />
          </div>
        </div>
      )}
    </div>
  );
};
