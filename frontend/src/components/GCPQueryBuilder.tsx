import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  GCP_RESOURCE_MAPPINGS,
  // QUERY_VALUE_MAPPINGS,
} from "../data/gcpResourceMappings";
import {
  ChevronDown,
  Plus,
  Trash2,
  Loader2,
  AlertCircle,
  Bug,
  CheckCircle,
  XCircle,
  Search,
  X,
  FileText,
  Copy,
} from "lucide-react";
import type { LogTab } from "../types/gcp";
import { useAuth } from "../contexts/Auth";
import axios from "axios";
import toast from "react-hot-toast";
import { parseGCPErrorMessage } from "../utils/errorUtils";

const SEVERITY_OPTIONS = ["ERROR", "WARNING", "INFO", "DEBUG"];
// const CACHE_TTL = 5 * 60 * 1000; // 5 minutes
// const apiCache = new Map<string, { data: any; timestamp: number }>();

interface GCPQueryBuilderProps {
  tab: LogTab;
  projectId: string;
  onUpdateTab: (tab: LogTab) => void;
  onQuerySubmit: (query: string) => void;
  isActive: boolean;
}

interface ApiStatus {
  [key: string]: {
    status: "loading" | "success" | "error" | "fallback";
    message?: string;
    endpoint?: string;
  };
}

// Query parsing interface
interface ParsedQuery {
  resourceType: string;
  resourceLabels: Record<string, string>;
  additionalQueries: Array<{
    type: string;
    value: string;
    operator?: string;
  }>;
}

// Function to parse GCP log query
const parseGCPQuery = (query: string): ParsedQuery | null => {
  try {
    // Handle both newline-separated and AND-separated queries
    let lines: string[];
    if (query.includes("\n")) {
      // Newline-separated format
      lines = query.split("\n").filter((line) => line.trim());
    } else {
      // AND-separated format (single line)
      lines = query
        .split(" AND ")
        .map((line) => line.trim())
        .filter((line) => line);
    }

    const result: ParsedQuery = {
      resourceType: "",
      resourceLabels: {},
      additionalQueries: [],
    };

    for (const line of lines) {
      const trimmedLine = line.trim();

      // Parse resource.type
      if (trimmedLine.startsWith("resource.type=")) {
        const match = trimmedLine.match(/resource\.type="([^"]+)"/);
        if (match) {
          result.resourceType = match[1];
        }
      }
      // Parse resource.labels
      else if (trimmedLine.startsWith("resource.labels.")) {
        const match = trimmedLine.match(/resource\.labels\.([^=]+)="([^"]+)"/);
        if (match) {
          result.resourceLabels[match[1]] = match[2];
        }
      }
      // Parse severity
      else if (trimmedLine.startsWith("severity")) {
        // Handle both quoted and unquoted values
        const quotedMatch = trimmedLine.match(/severity(>=?|<=?|=)"([^"]+)"/);
        const unquotedMatch = trimmedLine.match(/severity(>=?|<=?|=)([^\s]+)/);
        const match = quotedMatch || unquotedMatch;
        if (match) {
          result.additionalQueries.push({
            type: "severity",
            value: match[2],
            operator: match[1],
          });
        }
      }
      // Parse timestamp
      else if (trimmedLine.startsWith("timestamp")) {
        // Handle both quoted and unquoted values
        const quotedMatch = trimmedLine.match(/timestamp(>=?|<=?|=)"([^"]+)"/);
        const unquotedMatch = trimmedLine.match(/timestamp(>=?|<=?|=)([^\s]+)/);
        const match = quotedMatch || unquotedMatch;
        if (match) {
          result.additionalQueries.push({
            type: "timestamp",
            value: match[2],
            operator: match[1],
          });
        }
      }
      // Parse jsonPayload
      else if (trimmedLine.startsWith("jsonPayload.")) {
        const match = trimmedLine.match(/jsonPayload\.([^=]+)="([^"]+)"/);
        if (match) {
          result.additionalQueries.push({
            type: "jsonPayload",
            value: `${match[1]}="${match[2]}"`,
          });
        }
      }
      // Parse textPayload
      else if (trimmedLine.startsWith("textPayload:")) {
        const match = trimmedLine.match(/textPayload:"([^"]+)"/);
        if (match) {
          result.additionalQueries.push({
            type: "textPayload",
            value: match[1],
          });
        }
      }
      // Parse labels
      else if (trimmedLine.startsWith("labels.")) {
        const match = trimmedLine.match(/labels\.([^=]+)="([^"]+)"/);
        if (match) {
          result.additionalQueries.push({
            type: "labels",
            value: `${match[1]}="${match[2]}"`,
          });
        }
      }
      // Parse custom conditions (anything else)
      else if (
        trimmedLine.includes("=") ||
        trimmedLine.includes(">") ||
        trimmedLine.includes("<")
      ) {
        result.additionalQueries.push({
          type: "custom",
          value: trimmedLine,
        });
      }
    }

    console.log("Parsed query result:", {
      originalQuery: query,
      parsedResourceType: result.resourceType,
      parsedResourceLabels: result.resourceLabels,
      parsedAdditionalQueries: result.additionalQueries,
      lines: lines,
    });

    return result.resourceType ? result : null;
  } catch (error) {
    console.error("Error parsing query:", error);
    return null;
  }
};

// Custom SearchableSelect Component
const SearchableSelect: React.FC<{
  options: string[];
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  isLoading?: boolean;
  error?: string;
}> = ({ options, value, onChange, placeholder, isLoading = false, error }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredOptions = options.filter((option) =>
    option.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSearchTerm("");
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSelect = (option: string) => {
    onChange(option);
    setIsOpen(false);
    setSearchTerm("");
  };

  return (
    <div ref={dropdownRef} className="relative">
      <button
        type="button"
        onClick={() => !isLoading && setIsOpen(!isOpen)}
        disabled={isLoading}
        className={`
          w-full flex items-center justify-between px-4 py-3 
          bg-slate-800/50 border border-slate-700/50 rounded-xl
          text-slate-200 text-sm backdrop-blur-sm
          hover:border-slate-600 hover:bg-slate-800/70
          focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500
          transition-all duration-200 ease-in-out
          ${isLoading ? "cursor-not-allowed opacity-60" : "cursor-pointer"}
          ${isOpen ? "border-blue-500 ring-2 ring-blue-500/20" : ""}
        `}
      >
        <span className={value ? "text-slate-200" : "text-slate-400"}>
          {value || placeholder}
        </span>
        <div className="flex items-center gap-2">
          {isLoading && (
            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
          )}
          <ChevronDown
            className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </div>
      </button>

      {isOpen && !isLoading && (
        <div className="absolute z-50 w-full mt-2 bg-slate-800/95 backdrop-blur-lg border border-slate-700/50 rounded-xl shadow-2xl overflow-hidden">
          <div className="p-3 border-b border-slate-700/50">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                ref={inputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search options..."
                className="w-full pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-600 rounded-lg text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
              />
              {searchTerm && (
                <button
                  type="button"
                  onClick={() => setSearchTerm("")}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-200"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          <div className="max-h-48 overflow-y-auto">
            {filteredOptions.length > 0 ? (
              filteredOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => handleSelect(option)}
                  className={`
                    w-full text-left px-4 py-3 text-sm transition-colors duration-150
                    hover:bg-slate-700/50 focus:bg-slate-700/50 focus:outline-none
                    ${
                      value === option
                        ? "bg-blue-600/20 text-blue-300"
                        : "text-slate-200"
                    }
                  `}
                >
                  {option}
                </button>
              ))
            ) : (
              <div className="px-4 py-8 text-center text-slate-400 text-sm">
                No options found
              </div>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="mt-2 text-xs text-red-400 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          {error}
        </div>
      )}
    </div>
  );
};

export const GCPQueryBuilder: React.FC<GCPQueryBuilderProps> = ({
  tab,
  projectId,
  onUpdateTab,
  onQuerySubmit,
  isActive,
}) => {
  const { token, forceLogout } = useAuth();
  const [resourceType, setResourceType] = useState<string>(
    tab.filters.resourceType || "cloud_run_revision"
  );
  const [resourceLabels, setResourceLabels] = useState<Record<string, string>>(
    {}
  );
  const [labelOptions, setLabelOptions] = useState<Record<string, string[]>>(
    {}
  );
  const [labelLoading, setLabelLoading] = useState<Record<string, boolean>>({});
  const [labelError, setLabelError] = useState<Record<string, string>>({});
  const [additionalQueries, setAdditionalQueries] = useState<any[]>([]);
  const [showAddQuery, setShowAddQuery] = useState(false);
  const [queryPreview, setQueryPreview] = useState("");
  const [error, setError] = useState<string>("");
  const [dependencyValues, setDependencyValues] = useState<
    Record<string, string>
  >({});
  const [debugInfo, setDebugInfo] = useState<string[]>([]);
  const [showDebug, setShowDebug] = useState(false);
  const [apiStatus, setApiStatus] = useState<ApiStatus>({});
  const [showManualQuery, setShowManualQuery] = useState(false);
  const [manualQuery, setManualQuery] = useState("");
  const [parseError, setParseError] = useState<string>("");

  // Check if this is a project logs tab
  const isProjectLogs = tab.serviceId === "project_logs";

  // Use refs to track the latest values to prevent stale closures
  const resourceTypeRef = useRef(resourceType);
  const projectIdRef = useRef(projectId);

  // Initialize state from existing tab query when component mounts
  useEffect(() => {
    if (tab.query && tab.query.trim()) {
      addDebugMessage(
        `Initializing query builder with existing query: ${tab.query}`
      );
      const parsed = parseGCPQuery(tab.query);
      if (parsed) {
        // Update resource type if parsed from query
        if (parsed.resourceType && parsed.resourceType !== resourceType) {
          setResourceType(parsed.resourceType);
          addDebugMessage(
            `Set resource type from query: ${parsed.resourceType}`
          );
        }

        // Update resource labels
        if (Object.keys(parsed.resourceLabels).length > 0) {
          setResourceLabels(parsed.resourceLabels);
          setDependencyValues(parsed.resourceLabels);
          addDebugMessage(
            `Set resource labels from query: ${JSON.stringify(
              parsed.resourceLabels
            )}`
          );
        }

        // Update additional queries
        if (parsed.additionalQueries.length > 0) {
          setAdditionalQueries(parsed.additionalQueries);
          addDebugMessage(
            `Set additional queries from query: ${parsed.additionalQueries.length} conditions`
          );
        }
      } else {
        addDebugMessage(`Failed to parse existing query: ${tab.query}`);
      }
    } else {
      addDebugMessage("No existing query found, using default state");
    }
  }, []); // Only run once when component mounts

  // Update refs when values change
  useEffect(() => {
    resourceTypeRef.current = resourceType;
  }, [resourceType]);

  useEffect(() => {
    projectIdRef.current = projectId;
  }, [projectId]);

  // Add debug message with useCallback to prevent recreation
  const addDebugMessage = useCallback((message: string) => {
    console.log(`[QueryBuilder] ${message}`);
    setDebugInfo((prev) => [
      ...prev.slice(-20),
      `${new Date().toLocaleTimeString()}: ${message}`,
    ]);
  }, []);

  // Helper function to determine dependencies based on GCP resource patterns
  const getDependenciesForLabel = useCallback(
    (resourceType: string, label: string) => {
      const dependencyMap: Record<string, Record<string, string | string[]>> = {
        cloud_run_revision: {
          revision_name: "service_name",
        },
        gae_app: {
          version: "service",
          instance_id: ["service", "version"],
        },
        bigtable_instance: {
          cluster: "instance_id",
        },
        spanner_instance: {
          database: "instance_id",
        },
        cloud_scheduler_job: {
          job_id: "location",
        },
        cloud_tasks_queue: {
          queue_id: "location",
        },
        // Add more dependencies as needed
      };

      return dependencyMap[resourceType]?.[label] || null;
    },
    []
  );

  // Updated fetchOptionsFromBackend function with better error handling
  const fetchOptionsFromBackend = useCallback(
    async (
      resourceType: string,
      label: string,
      projectId: string,
      dependencies: Record<string, string>,
      token: string
    ) => {
      try {
        console.log(`Fetching options for ${resourceType}.${label}`, {
          resourceType,
          label,
          projectId,
          dependencies,
        });

        const response = await axios.post(
          "/api/v1/logs/gcp-resource-options",
          {
            resourceType,
            label,
            projectId,
            dependencies,
          },
          {
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            timeout: 30000, // 30 second timeout
          }
        );

        console.log(
          `API Response for ${resourceType}.${label}:`,
          response.data
        );

        // Check if response has the expected structure
        if (!response.data) {
          throw new Error("No data in response");
        }

        // Handle different response formats
        let options = [];

        if (response.data.options && Array.isArray(response.data.options)) {
          options = response.data.options;
        } else if (response.data.options) {
          // If options is not an array, try to convert it
          console.warn(
            `Options not an array for ${resourceType}.${label}:`,
            response.data.options
          );
          options = [];
        } else {
          // Fallback: check if the response data itself is an array
          if (Array.isArray(response.data)) {
            options = response.data;
          } else {
            console.error(
              `Unexpected response format for ${resourceType}.${label}:`,
              response.data
            );
            options = [];
          }
        }

        // Validate and clean the options
        const validOptions = options
          .filter(
            (option: any) =>
              option !== null && option !== undefined && option !== ""
          )
          .map((option: any) => String(option).trim())
          .filter((option: any) => option.length > 0);

        console.log(
          `Processed ${validOptions.length} valid options for ${resourceType}.${label}`
        );

        if (validOptions.length === 0 && response.data.message) {
          console.warn(
            `No options returned for ${resourceType}.${label}: ${response.data.message}`
          );
        }

        return validOptions;
      } catch (err: any) {
        console.error(
          `Error fetching options for ${resourceType}.${label}:`,
          err
        );

        let errorMessage = "Unknown error occurred";

        if (err.response) {
          // Check for authentication errors
          if (err.response.status === 401 || err.response.status === 403) {
            forceLogout("Authentication token expired or invalid");
            throw new Error("Authentication failed");
          }

          // Server responded with error status
          if (err.response.data && err.response.data.message) {
            errorMessage = err.response.data.message;
          } else {
            errorMessage = `Server error: ${err.response.status} - ${err.response.statusText}`;
          }
        } else if (err.request) {
          // Request was made but no response received
          errorMessage =
            "No response from server - check your network connection";
        } else if (err.code === "ECONNABORTED") {
          // Timeout
          errorMessage =
            "Request timed out - the API is taking too long to respond";
        } else {
          // Something else happened
          errorMessage = err.message || "Request failed";
        }

        // Show toast notification for the error
        const userFriendlyMessage = parseGCPErrorMessage(errorMessage);
        toast.error(`Failed to fetch ${label} options: ${userFriendlyMessage}`);

        throw new Error(errorMessage);
      }
    },
    []
  );

  // Fetch dropdown options for a label
  const fetchDropdownOptions = useCallback(
    async (
      label: string,
      currentProjectId: string,
      labelDeps: Record<string, string>
    ) => {
      const currentResourceType = resourceTypeRef.current;
      addDebugMessage(
        `Fetching options for ${currentResourceType}.${label} from backend`
      );

      setLabelLoading((prev) => ({ ...prev, [label]: true }));
      setLabelError((prev) => ({ ...prev, [label]: "" }));
      setApiStatus((prev) => ({
        ...prev,
        [label]: {
          status: "loading",
          message: "Fetching from backend...",
        },
      }));

      try {
        if (!token) {
          forceLogout("No access token available");
          throw new Error("Authentication failed");
        }

        const options = await fetchOptionsFromBackend(
          currentResourceType,
          label,
          currentProjectId,
          labelDeps,
          token
        );

        console.log(
          `Successfully fetched ${options.length} options for ${label}:`,
          options.slice(0, 5)
        );

        setLabelOptions((prev) => ({ ...prev, [label]: options }));
        setLabelLoading((prev) => ({ ...prev, [label]: false }));
        setApiStatus((prev) => ({
          ...prev,
          [label]: {
            status: "success",
            message: `Loaded ${options.length} items from backend`,
          },
        }));

        addDebugMessage(
          `Successfully loaded ${options.length} options for ${label}`
        );
        return options;
      } catch (err: any) {
        const errorMessage = err.message || "Unknown error occurred";

        addDebugMessage(`Error fetching options for ${label}: ${errorMessage}`);
        console.error(`fetchDropdownOptions error for ${label}:`, err);

        setLabelOptions((prev) => ({ ...prev, [label]: [] }));
        setLabelLoading((prev) => ({ ...prev, [label]: false }));
        setLabelError((prev) => ({ ...prev, [label]: errorMessage }));
        setApiStatus((prev) => ({
          ...prev,
          [label]: {
            status: "error",
            message: `Backend failed: ${errorMessage}`,
          },
        }));

        return [];
      }
    },
    [token, addDebugMessage, fetchOptionsFromBackend]
  );

  // Handle resource type change - memoized to prevent infinite loops
  const handleResourceTypeChange = useCallback(
    (newResourceType: string) => {
      addDebugMessage(`Resource type changed to: ${newResourceType}`);
      setResourceType(newResourceType);
      setResourceLabels({});
      setAdditionalQueries([]);
      setLabelLoading({});
      setLabelError({});
      setDependencyValues({});
      setApiStatus({});

      // Update tab without causing re-renders
      const updatedTab = {
        ...tab,
        title:
          GCP_RESOURCE_MAPPINGS[
            newResourceType as keyof typeof GCP_RESOURCE_MAPPINGS
          ]?.id ||
          newResourceType
            .replace(/_/g, " ")
            .replace(/\b\w/g, (l) => l.toUpperCase()),
        filters: { ...tab.filters, resourceType: newResourceType },
      };

      // Use setTimeout to break the potential loop
      setTimeout(() => {
        onUpdateTab(updatedTab);
      }, 0);
    },
    [tab, onUpdateTab, addDebugMessage]
  );

  // Fetch options for all labels when component mounts or resourceType changes
  useEffect(() => {
    // Skip fetching for project logs since we don't need resource-specific labels
    if (isProjectLogs) {
      addDebugMessage(
        "Skipping label fetch for project logs - no resource type needed"
      );
      return;
    }

    const mapping =
      GCP_RESOURCE_MAPPINGS[resourceType as keyof typeof GCP_RESOURCE_MAPPINGS];
    if (!mapping || !projectId) {
      addDebugMessage(
        `Skipping label fetch - mapping: ${!!mapping}, projectId: ${!!projectId}`
      );
      return;
    }

    addDebugMessage(
      `Fetching options for ${resourceType} labels: ${mapping.labels.join(
        ", "
      )}`
    );

    // Fetch options for labels that don't have dependencies first
    mapping.labels.forEach((label: any) => {
      const dependencies = getDependenciesForLabel(resourceType, label);
      if (!dependencies) {
        addDebugMessage(`Fetching independent label: ${label}`);
        fetchDropdownOptions(label, projectId, {});
      } else {
        addDebugMessage(
          `Skipping dependent label: ${label} (depends on: ${
            Array.isArray(dependencies) ? dependencies.join(", ") : dependencies
          })`
        );
      }
    });
  }, [
    resourceType,
    projectId,
    fetchDropdownOptions,
    addDebugMessage,
    getDependenciesForLabel,
    isProjectLogs,
  ]);

  // Handle dependencies: refetch dependent dropdowns when a dependency changes
  useEffect(() => {
    // Skip dependency handling for project logs
    if (isProjectLogs || Object.keys(dependencyValues).length === 0) return;

    const mapping =
      GCP_RESOURCE_MAPPINGS[resourceType as keyof typeof GCP_RESOURCE_MAPPINGS];
    if (!mapping || !projectId) return;

    addDebugMessage(
      `Dependencies changed: ${JSON.stringify(dependencyValues)}`
    );

    mapping.labels.forEach((label: any) => {
      const dependencies = getDependenciesForLabel(resourceType, label);
      if (dependencies) {
        if (typeof dependencies === "string") {
          if (dependencyValues[dependencies]) {
            addDebugMessage(`Fetching dependent label: ${label}`);
            fetchDropdownOptions(label, projectId, dependencyValues);
          }
        } else if (Array.isArray(dependencies)) {
          const allDepsSet = dependencies.every(
            (dep: string) => dependencyValues[dep]
          );
          if (allDepsSet) {
            addDebugMessage(`Fetching dependent label: ${label}`);
            fetchDropdownOptions(label, projectId, dependencyValues);
          }
        }
      }
    });
  }, [
    dependencyValues,
    resourceType,
    projectId,
    fetchDropdownOptions,
    addDebugMessage,
    getDependenciesForLabel,
    isProjectLogs,
  ]);

  // Generate query preview
  useEffect(() => {
    if (isProjectLogs) {
      // For project logs, we don't include resource type filters
      const conditions: string[] = [];

      // Add additional queries
      additionalQueries.forEach((q) => {
        if (q.value) {
          conditions.push(`${q.type}="${q.value}"`);
        }
      });

      // Add resource labels if any are set
      Object.entries(resourceLabels).forEach(([key, value]) => {
        if (value) {
          conditions.push(`resource.labels.${key}="${value}"`);
        }
      });

      const query = conditions.length > 0 ? conditions.join(" AND ") : "";
      setQueryPreview(query);
      addDebugMessage(
        `Generated project logs query: ${query || "No filters (all logs)"}`
      );
    } else {
      // For specific services, include resource type
      const conditions: string[] = [`resource.type="${resourceType}"`];

      // Add additional queries
      additionalQueries.forEach((q) => {
        if (q.value) {
          conditions.push(`${q.type}="${q.value}"`);
        }
      });

      // Add resource labels
      Object.entries(resourceLabels).forEach(([key, value]) => {
        if (value) {
          conditions.push(`resource.labels.${key}="${value}"`);
        }
      });

      const query = conditions.join(" AND ");
      setQueryPreview(query);
      addDebugMessage(`Generated query for ${resourceType}: ${query}`);
    }
  }, [
    resourceType,
    resourceLabels,
    additionalQueries,
    isProjectLogs,
    addDebugMessage,
  ]);

  // Handle label change
  const handleLabelChange = useCallback(
    (label: string, value: string) => {
      setResourceLabels((prev) => ({ ...prev, [label]: value }));
      // If this label is a dependency for others, update dependencyValues
      setDependencyValues((prev) => ({ ...prev, [label]: value }));
      addDebugMessage(`Label ${label} changed to: ${value}`);
    },
    [addDebugMessage]
  );

  // Handle add query
  const handleAddQuery = useCallback(
    (type: string, value: string, operator?: string) => {
      setAdditionalQueries((prev) => [...prev, { type, value, operator }]);
      setShowAddQuery(false);
    },
    []
  );

  // Remove query condition
  const handleRemoveQuery = useCallback((idx: number) => {
    setAdditionalQueries((prev) => prev.filter((_, i) => i !== idx));
  }, []);

  // Validate before submit
  const handleSubmit = useCallback(() => {
    if (!resourceType) {
      setError("Resource type is required.");
      return;
    }
    setError("");
    onQuerySubmit(queryPreview);
  }, [resourceType, queryPreview, onQuerySubmit]);

  // Clear all selections
  const handleClearAll = useCallback(() => {
    setResourceLabels({});
    setAdditionalQueries([]);
    setError("");
    setDependencyValues({});
  }, []);

  // Handle manual query parsing
  const handleParseManualQuery = useCallback(() => {
    if (!manualQuery.trim()) {
      setParseError("Please enter a query to parse");
      toast.error("Please enter a query to parse");
      return;
    }

    setParseError("");
    const parsed = parseGCPQuery(manualQuery);

    if (!parsed) {
      setParseError("Failed to parse query. Please check the format.");
      toast.error("Failed to parse query. Please check the format.");
      return;
    }

    // Check if resource type is supported
    if (
      !GCP_RESOURCE_MAPPINGS[
        parsed.resourceType as keyof typeof GCP_RESOURCE_MAPPINGS
      ]
    ) {
      setParseError(`Unsupported resource type: ${parsed.resourceType}`);
      toast.error(`Unsupported resource type: ${parsed.resourceType}`);
      return;
    }

    // Apply parsed query to the interface
    setResourceType(parsed.resourceType);
    setResourceLabels(parsed.resourceLabels);
    setAdditionalQueries(parsed.additionalQueries);
    setDependencyValues(parsed.resourceLabels);

    // Update tab
    const updatedTab = {
      ...tab,
      title:
        GCP_RESOURCE_MAPPINGS[
          parsed.resourceType as keyof typeof GCP_RESOURCE_MAPPINGS
        ]?.id ||
        parsed.resourceType
          .replace(/_/g, " ")
          .replace(/\b\w/g, (l) => l.toUpperCase()),
      filters: { ...tab.filters, resourceType: parsed.resourceType },
    };
    onUpdateTab(updatedTab);

    // Close modal and clear input
    setShowManualQuery(false);
    setManualQuery("");
    addDebugMessage(`Successfully parsed query for ${parsed.resourceType}`);
    toast.success(`Successfully parsed query for ${parsed.resourceType}`);
  }, [manualQuery, tab, onUpdateTab, addDebugMessage]);

  // Copy query to clipboard
  const handleCopyQuery = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(queryPreview);
      addDebugMessage("Query copied to clipboard");
      toast.success("Query copied to clipboard");
    } catch (error) {
      console.error("Failed to copy query:", error);
      addDebugMessage("Failed to copy query to clipboard");
      toast.error("Failed to copy query to clipboard");
    }
  }, [queryPreview, addDebugMessage]);

  // Get status icon for API calls
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "loading":
        return <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />;
      case "success":
        return <CheckCircle className="w-3 h-3 text-emerald-400" />;
      case "error":
        return <XCircle className="w-3 h-3 text-red-400" />;
      case "fallback":
        return <AlertCircle className="w-3 h-3 text-amber-400" />;
      default:
        return null;
    }
  };

  // Debug functions
  const testApiConnectivity = async () => {
    if (!token || !projectId) {
      console.error("Missing token or projectId for testing");
      return;
    }

    const testCases = [
      {
        name: "Cloud Run Services",
        resourceType: "cloud_run_revision",
        label: "service_name",
      },
      {
        name: "GCS Buckets",
        resourceType: "gcs_bucket",
        label: "bucket_name",
      },
      {
        name: "BigQuery Datasets",
        resourceType: "bigquery_dataset",
        label: "dataset_id",
      },
    ];

    for (const testCase of testCases) {
      try {
        console.log(`Testing ${testCase.name}...`);
        const options = await fetchOptionsFromBackend(
          testCase.resourceType,
          testCase.label,
          projectId,
          {},
          token
        );
        console.log(
          `✅ ${testCase.name}: ${options.length} options found`,
          options.slice(0, 3)
        );
      } catch (error: any) {
        console.error(`❌ ${testCase.name} failed:`, error.message);
      }
    }
  };

  // UI for API status display
  const renderApiStatus = () => {
    const statusEntries = Object.entries(apiStatus);
    if (statusEntries.length === 0) return null;

    return (
      <div className="mb-6 p-4 bg-slate-800/30 border border-slate-700/50 rounded-xl backdrop-blur-sm">
        <div className="text-xs font-medium text-slate-300 mb-3">
          API Status:
        </div>
        <div className="space-y-2">
          {statusEntries.map(([label, status]) => (
            <div key={label} className="flex items-center gap-3 text-xs">
              {getStatusIcon(status.status)}
              <span className="text-slate-400 min-w-[120px] font-mono">
                {label}:
              </span>
              <span
                className={`
                ${
                  status.status === "success"
                    ? "text-emerald-400"
                    : status.status === "error"
                    ? "text-red-400"
                    : status.status === "loading"
                    ? "text-blue-400"
                    : "text-amber-400"
                }
              `}
              >
                {status.message}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Debug controls UI
  const renderDebugControls = () => (
    <div className="mb-6 p-4 bg-slate-800/30 border border-slate-700/50 rounded-xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs font-medium text-slate-300">
          Debug Controls:
        </div>
        <button
          onClick={testApiConnectivity}
          className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded"
        >
          Test APIs
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs">
        <div>
          <div className="text-slate-400">Resource Type:</div>
          <div className="text-slate-200 font-mono">{resourceType}</div>
        </div>
        <div>
          <div className="text-slate-400">Project ID:</div>
          <div className="text-slate-200 font-mono">{projectId}</div>
        </div>
        <div>
          <div className="text-slate-400">Available Labels:</div>
          <div className="text-slate-200 font-mono">
            {GCP_RESOURCE_MAPPINGS[
              resourceType as keyof typeof GCP_RESOURCE_MAPPINGS
            ]?.labels?.join(", ") || "None"}
          </div>
        </div>
        <div>
          <div className="text-slate-400">Token Available:</div>
          <div className="text-slate-200 font-mono">{token ? "Yes" : "No"}</div>
        </div>
      </div>

      <div className="mt-3">
        <div className="text-slate-400 text-xs mb-2">
          Current Label Options Count:
        </div>
        <div className="grid grid-cols-3 gap-2 text-xs">
          {GCP_RESOURCE_MAPPINGS[
            resourceType as keyof typeof GCP_RESOURCE_MAPPINGS
          ]?.labels?.map((label: string) => (
            <div key={label} className="bg-slate-700/30 p-2 rounded">
              <div className="text-slate-300 font-medium">{label}</div>
              <div className="text-slate-400">
                {labelOptions[label]?.length || 0} options
              </div>
              <div className="text-xs">
                {labelLoading[label]
                  ? "Loading..."
                  : labelError[label]
                  ? "Error"
                  : labelOptions[label]?.length > 0
                  ? "Ready"
                  : "Empty"}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // UI for Manual Query Input Modal
  const renderManualQueryModal = () => {
    if (!showManualQuery) return null;

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
        <div className="bg-slate-900/95 backdrop-blur-lg border border-slate-700/50 rounded-2xl shadow-2xl p-6 w-[600px] max-w-[90vw] mx-4 max-h-[80vh] overflow-y-auto">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-slate-200 mb-2">
              Paste GCP Log Query
            </h3>
            <p className="text-sm text-slate-400">
              Paste your GCP log query here to automatically populate the query
              builder
            </p>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-3">
              Query Input
            </label>
            <textarea
              className="w-full h-48 px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-200 text-sm font-mono resize-none backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-200 ease-in-out"
              value={manualQuery}
              onChange={(e) => setManualQuery(e.target.value)}
              placeholder={`Paste your GCP log query here, for example:

resource.type="k8s_container"
resource.labels.project_id="emergent-default"
resource.labels.location="us-central1"
resource.labels.cluster_name="env-worker-cluster"
resource.labels.namespace_name="emergent-agents-env"
resource.labels.pod_name="agent-env-9f2d59a6-1dc6-45c7-94c5-bb7bd8e5829c"
severity>=DEFAULT`}
            />
          </div>

          {parseError && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl backdrop-blur-sm">
              <div className="flex items-center gap-2">
                <XCircle className="w-4 h-4 text-red-400" />
                <span className="text-red-300 text-sm font-medium">
                  {parseError}
                </span>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <button
              className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-all duration-200 ease-in-out font-medium"
              onClick={handleParseManualQuery}
            >
              Parse & Apply Query
            </button>
            <button
              className="flex-1 py-3 bg-slate-700/50 hover:bg-slate-700 text-slate-200 rounded-xl transition-all duration-200 ease-in-out font-medium"
              onClick={() => {
                setShowManualQuery(false);
                setManualQuery("");
                setParseError("");
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  };

  // UI for Add Query Modal/Dropdown
  const renderAddQueryModal = () => {
    const mapping =
      GCP_RESOURCE_MAPPINGS[resourceType as keyof typeof GCP_RESOURCE_MAPPINGS];
    if (!mapping) return null;

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
        <div className="bg-slate-900/95 backdrop-blur-lg border border-slate-700/50 rounded-2xl shadow-2xl p-6 w-96 max-w-md mx-4">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-slate-200 mb-2">
              Add Query Condition
            </h3>
            <p className="text-sm text-slate-400">
              Select a condition type to add to your query
            </p>
          </div>

          <div className="space-y-2 mb-6">
            {mapping.additionalQueries.map((queryType: string) => (
              <button
                key={queryType}
                className="w-full text-left px-4 py-3 rounded-xl hover:bg-slate-700/50 text-slate-200 text-sm transition-all duration-200 ease-in-out border border-transparent hover:border-slate-600/50"
                onClick={() => {
                  if (queryType === "severity") {
                    handleAddQuery("severity", SEVERITY_OPTIONS[0]);
                  } else if (queryType === "timestamp") {
                    handleAddQuery("timestamp", new Date().toISOString(), ">=");
                  } else if (queryType === "jsonPayload") {
                    handleAddQuery("jsonPayload", "");
                  } else if (queryType === "textPayload") {
                    handleAddQuery("textPayload", "");
                  } else if (queryType === "labels") {
                    handleAddQuery("labels", "");
                  } else {
                    handleAddQuery(queryType, "");
                  }
                }}
              >
                <span className="font-medium capitalize">
                  {queryType.replace(/([A-Z])/g, " $1")}
                </span>
                {queryType === "jsonPayload" && (
                  <span className="block text-xs text-slate-400 mt-1">
                    Filter by JSON payload fields
                  </span>
                )}
                {queryType === "textPayload" && (
                  <span className="block text-xs text-slate-400 mt-1">
                    Filter by text payload content
                  </span>
                )}
                {queryType === "labels" && (
                  <span className="block text-xs text-slate-400 mt-1">
                    Filter by resource labels
                  </span>
                )}
              </button>
            ))}
            <button
              className="w-full text-left px-4 py-3 rounded-xl hover:bg-slate-700/50 text-slate-200 text-sm transition-all duration-200 ease-in-out border border-transparent hover:border-slate-600/50"
              onClick={() => handleAddQuery("custom", "")}
            >
              <span className="font-medium">Custom Filter</span>
              <span className="block text-xs text-slate-400 mt-1">
                Write your own condition
              </span>
            </button>
          </div>

          <div className="flex gap-3">
            <button
              className="flex-1 py-3 bg-slate-700/50 hover:bg-slate-700 text-slate-200 rounded-xl transition-all duration-200 ease-in-out font-medium"
              onClick={() => setShowAddQuery(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  };

  // UI for resource label dropdowns
  const renderLabelDropdowns = () => {
    const mapping =
      GCP_RESOURCE_MAPPINGS[resourceType as keyof typeof GCP_RESOURCE_MAPPINGS];
    if (!mapping) return null;

    return mapping.labels.map((label: string) => {
      const isLoading = labelLoading[label];
      const error = labelError[label];
      const options = labelOptions[label] || [];
      const hasOptions = options.length > 0;
      const status = apiStatus[label];

      return (
        <div key={label} className="grid grid-cols-12 gap-4 items-start mb-6">
          <div className="col-span-4">
            <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
              <span className="font-mono text-xs bg-slate-800/50 px-2 py-1 rounded">
                resource.labels.{label}
              </span>
              {status && getStatusIcon(status.status)}
            </label>
            {status && status.status !== "success" && (
              <p className="text-xs text-slate-400 mt-1">{status.message}</p>
            )}
          </div>

          <div className="col-span-8">
            {hasOptions ? (
              <SearchableSelect
                options={options}
                value={resourceLabels[label] || ""}
                onChange={(value) => handleLabelChange(label, value)}
                placeholder={`Select ${label}`}
                isLoading={isLoading}
                error={error}
              />
            ) : (
              <input
                type="text"
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-200 text-sm backdrop-blur-sm hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-200 ease-in-out"
                value={resourceLabels[label] || ""}
                onChange={(e) => handleLabelChange(label, e.target.value)}
                placeholder={`Enter ${label}`}
              />
            )}
          </div>
        </div>
      );
    });
  };

  // Early return for safety
  if (!isActive || !tab) {
    return (
      <div className="w-full max-w-6xl mx-auto mt-8 mb-8 p-8 bg-gradient-to-br from-slate-900/90 to-slate-800/90 border border-slate-700/50 rounded-3xl shadow-2xl backdrop-blur-lg">
        <div className="text-center text-slate-400">
          Query Builder not available
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto mt-8 mb-8 p-8 bg-gradient-to-br from-slate-900/90 to-slate-800/90 border border-slate-700/50 rounded-3xl shadow-2xl backdrop-blur-lg">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-100 mb-2">
              {isProjectLogs
                ? "Project Logs Query Builder"
                : "GCP Query Builder"}
            </h2>
            <p className="text-slate-400">
              {isProjectLogs
                ? "Build queries to filter logs across all services in your project"
                : "Build queries to filter logs from specific GCP services"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 rounded-lg transition-all duration-200"
              onClick={() => setShowDebug(!showDebug)}
              title="Toggle debug info"
            >
              <Bug className="w-4 h-4" />
            </button>
            <button
              className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 rounded-lg transition-all duration-200"
              onClick={() => setShowManualQuery(!showManualQuery)}
              title="Toggle manual query input"
            >
              <FileText className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Resource Type Selection */}
      <div className="mb-8">
        <div className="grid grid-cols-12 gap-4 items-center">
          <div className="col-span-4">
            <label className="text-sm font-medium text-slate-300">
              <span className="font-mono text-xs bg-slate-800/50 px-2 py-1 rounded">
                resource.type
              </span>
            </label>
          </div>
          <div className="col-span-8">
            {isProjectLogs ? (
              <div className="flex items-center gap-2 px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-200 text-sm backdrop-blur-sm">
                <AlertCircle className="w-4 h-4 text-amber-400" />
                <span>
                  All services are being queried. Resource type selection is
                  disabled.
                </span>
              </div>
            ) : (
              <SearchableSelect
                options={Object.keys(GCP_RESOURCE_MAPPINGS)}
                value={resourceType}
                onChange={handleResourceTypeChange}
                placeholder="Select resource type"
              />
            )}
          </div>
        </div>
      </div>

      {/* Resource Labels */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-slate-200 mb-6">
          Resource Labels
        </h3>
        {isProjectLogs ? (
          <div className="flex items-center gap-2 px-4 py-3 bg-slate-800/30 border border-slate-700/50 rounded-xl text-slate-300 text-sm">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <span>
              No resource labels needed for project-wide logs. All services will
              be included.
            </span>
          </div>
        ) : (
          renderLabelDropdowns()
        )}
      </div>

      {/* Additional Query Conditions */}
      {isProjectLogs ? (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-slate-200 mb-6">
            Additional Conditions
          </h3>
          <div className="flex items-center gap-2 px-4 py-3 bg-slate-800/30 border border-slate-700/50 rounded-xl text-slate-300 text-sm mb-4">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <span>
              You can still add conditions like severity, timestamp, or custom
              queries to filter logs across all services.
            </span>
          </div>
          {additionalQueries.length > 0 && (
            <div className="space-y-4">
              {additionalQueries.map((q, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-4 p-4 bg-slate-800/30 border border-slate-700/50 rounded-xl backdrop-blur-sm"
                >
                  <span className="text-sm font-medium text-slate-300 min-w-[120px]">
                    {q.type} =
                  </span>
                  {q.type === "severity" ? (
                    <SearchableSelect
                      options={SEVERITY_OPTIONS}
                      value={q.value}
                      onChange={(val) => {
                        setAdditionalQueries((prev) =>
                          prev.map((item, i) =>
                            i === idx ? { ...item, value: val } : item
                          )
                        );
                      }}
                      placeholder="Select severity"
                    />
                  ) : (
                    <input
                      type="text"
                      className="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-200 text-sm backdrop-blur-sm hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-200 ease-in-out"
                      value={q.value}
                      onChange={(e) => {
                        const val = e.target.value;
                        setAdditionalQueries((prev) =>
                          prev.map((item, i) =>
                            i === idx ? { ...item, value: val } : item
                          )
                        );
                      }}
                      placeholder={`Enter ${q.type}`}
                    />
                  )}
                  <button
                    className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all duration-200 ease-in-out"
                    onClick={() => handleRemoveQuery(idx)}
                    title="Remove condition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        additionalQueries.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-slate-200 mb-6">
              Additional Conditions
            </h3>
            <div className="space-y-4">
              {additionalQueries.map((q, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-4 p-4 bg-slate-800/30 border border-slate-700/50 rounded-xl backdrop-blur-sm"
                >
                  <span className="text-sm font-medium text-slate-300 min-w-[120px]">
                    {q.type} =
                  </span>
                  {q.type === "severity" ? (
                    <SearchableSelect
                      options={SEVERITY_OPTIONS}
                      value={q.value}
                      onChange={(val) => {
                        setAdditionalQueries((prev) =>
                          prev.map((item, i) =>
                            i === idx ? { ...item, value: val } : item
                          )
                        );
                      }}
                      placeholder="Select severity"
                    />
                  ) : (
                    <input
                      type="text"
                      className="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-200 text-sm backdrop-blur-sm hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-200 ease-in-out"
                      value={q.value}
                      onChange={(e) => {
                        const val = e.target.value;
                        setAdditionalQueries((prev) =>
                          prev.map((item, i) =>
                            i === idx ? { ...item, value: val } : item
                          )
                        );
                      }}
                      placeholder={`Enter ${q.type}`}
                    />
                  )}
                  <button
                    className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all duration-200 ease-in-out"
                    onClick={() => handleRemoveQuery(idx)}
                    title="Remove condition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-4 mb-8">
        {isProjectLogs ? (
          <div className="flex items-center gap-2 px-4 py-3 bg-slate-800/30 border border-slate-700/50 rounded-xl text-slate-300 text-sm">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <span>
              Add conditions to filter logs across all services in the project.
            </span>
          </div>
        ) : (
          <button
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 ease-in-out font-medium"
            onClick={() => setShowAddQuery(true)}
            type="button"
          >
            <Plus className="w-4 h-4" /> Add Condition
          </button>
        )}

        <button
          className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 ease-in-out font-medium"
          onClick={() => onQuerySubmit(queryPreview)}
          type="button"
        >
          <CheckCircle className="w-4 h-4" /> Apply Query
        </button>
      </div>

      {/* Query Preview */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-slate-200 mb-4">
          Query Preview
        </h3>
        {isProjectLogs && (
          <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-300 text-sm">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>
                <strong>Project Logs Mode:</strong> This query will fetch logs
                from all services in your project. No resource type filter is
                applied.
              </span>
            </div>
          </div>
        )}
        <div className="p-4 bg-slate-800/30 border border-slate-700/50 rounded-xl backdrop-blur-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-300">
              Generated Query:
            </span>
            <button
              className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 rounded-lg transition-all duration-200"
              onClick={() => {
                navigator.clipboard.writeText(queryPreview);
                toast.success("Query copied to clipboard!");
              }}
              title="Copy query to clipboard"
            >
              <Copy className="w-4 h-4" />
            </button>
          </div>
          <div className="font-mono text-sm text-slate-200 bg-slate-900/50 p-3 rounded-lg border border-slate-700/50">
            {queryPreview || "No query generated yet"}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-red-400" />
            <span className="text-red-300 text-sm font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 ease-in-out"
          onClick={handleSubmit}
          type="button"
          disabled={!queryPreview.trim()}
        >
          Submit Query
        </button>
      </div>

      {/* Add Query Modal */}
      {showAddQuery && renderAddQueryModal()}

      {/* Manual Query Input */}
      {showManualQuery && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-slate-200 mb-4">
            Manual Query Input
          </h3>
          {isProjectLogs && (
            <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-300 text-sm">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                <span>
                  <strong>Project Logs Mode:</strong> You can enter any valid
                  GCP Logging query. No resource type filter will be
                  automatically added.
                </span>
              </div>
            </div>
          )}
          <div className="space-y-4">
            <textarea
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-slate-200 text-sm font-mono resize-none backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-200 ease-in-out"
              value={manualQuery}
              onChange={(e) => setManualQuery(e.target.value)}
              placeholder="Enter your GCP Logging query here..."
              rows={6}
            />
            <div className="flex items-center gap-4">
              <button
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all duration-200 ease-in-out font-medium"
                onClick={handleParseManualQuery}
                type="button"
              >
                <CheckCircle className="w-4 h-4" /> Parse Query
              </button>
              <button
                className="inline-flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-all duration-200 ease-in-out font-medium"
                onClick={() => setManualQuery("")}
                type="button"
              >
                <X className="w-4 h-4" /> Clear
              </button>
            </div>
            {parseError && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-300 text-sm">
                <div className="flex items-center gap-2">
                  <XCircle className="w-4 h-4" />
                  <span>Parse Error: {parseError}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Manual Query Modal */}
      {renderManualQueryModal()}

      {/* Authentication Token Warning */}
      {!token && (
        <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0" />
            <div>
              <p className="text-blue-300 font-medium text-sm">
                No Authentication Token
              </p>
              <p className="text-blue-200/80 text-xs mt-1">
                All dropdowns will use test data for demonstration.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Debug Information */}
      {showDebug && (
        <>
          {renderApiStatus()}
          {renderDebugControls()}
          <div className="mb-6 p-4 bg-slate-800/30 border border-slate-700/50 rounded-xl backdrop-blur-sm">
            <div className="text-xs font-medium text-slate-300 mb-3">
              Debug Information:
            </div>
            <div className="max-h-32 overflow-y-auto text-xs text-slate-400 space-y-1 font-mono">
              {debugInfo.map((info, i) => (
                <div key={i} className="opacity-80">
                  {info}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
