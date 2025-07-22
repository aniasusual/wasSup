// import React, { useState, useEffect, useCallback, useRef } from "react";
// import { GCP_RESOURCE_MAPPINGS as RAW_MAPPINGS } from "../data/gcpResourceMappings";
// import { GCP_API_ENDPOINTS as RAW_API_ENDPOINTS } from "../data/gcpApiEndpoints";
// import { FALLBACK_DATA as RAW_FALLBACK_DATA } from "../data/fallbackData";
// import {
//   ChevronDown,
//   Plus,
//   Trash2,
//   Loader2,
//   AlertCircle,
//   Bug,
//   CheckCircle,
//   XCircle,
// } from "lucide-react";
// import type { LogTab } from "../types/gcp";
// import { useAuth } from "../contexts/Auth";

// const GCP_RESOURCE_MAPPINGS: Record<
//   string,
//   { labels: string[]; additionalQueries: string[] }
// > = RAW_MAPPINGS;

// const GCP_API_ENDPOINTS: Record<string, any> = RAW_API_ENDPOINTS;
// const FALLBACK_DATA: Record<
//   string,
//   Record<string, string[]>
// > = RAW_FALLBACK_DATA;

// const SEVERITY_OPTIONS = ["ERROR", "WARNING", "INFO", "DEBUG"];
// const CACHE_TTL = 5 * 60 * 1000; // 5 minutes
// const apiCache = new Map<string, { data: any; timestamp: number }>();

// interface GCPQueryBuilderProps {
//   tab: LogTab;
//   projectId: string;
//   onUpdateTab: (tab: LogTab) => void;
//   onQuerySubmit: (query: string) => void;
//   isActive: boolean;
// }

// interface ApiStatus {
//   [key: string]: {
//     status: "loading" | "success" | "error" | "fallback";
//     message?: string;
//     endpoint?: string;
//   };
// }

// export const GCPQueryBuilder: React.FC<GCPQueryBuilderProps> = ({
//   tab,
//   projectId,
//   onUpdateTab,
//   onQuerySubmit,
//   isActive,
// }) => {
//   const { accesstoken } = useAuth();
//   const [resourceType, setResourceType] = useState<string>(
//     tab.filters.resourceType || "cloud_run_revision"
//   );
//   const [resourceLabels, setResourceLabels] = useState<Record<string, string>>(
//     {}
//   );
//   const [labelOptions, setLabelOptions] = useState<Record<string, string[]>>(
//     {}
//   );
//   const [labelLoading, setLabelLoading] = useState<Record<string, boolean>>({});
//   const [labelError, setLabelError] = useState<Record<string, string>>({});
//   const [additionalQueries, setAdditionalQueries] = useState<any[]>([]);
//   const [showAddQuery, setShowAddQuery] = useState(false);
//   const [queryPreview, setQueryPreview] = useState("");
//   const [error, setError] = useState<string>("");
//   const [dependencyValues, setDependencyValues] = useState<
//     Record<string, string>
//   >({});
//   const [debugInfo, setDebugInfo] = useState<string[]>([]);
//   const [showDebug, setShowDebug] = useState(false);
//   const [apiStatus, setApiStatus] = useState<ApiStatus>({});

//   // Use refs to track the latest values to prevent stale closures
//   const resourceTypeRef = useRef(resourceType);
//   const projectIdRef = useRef(projectId);

//   // Update refs when values change
//   useEffect(() => {
//     resourceTypeRef.current = resourceType;
//   }, [resourceType]);

//   useEffect(() => {
//     projectIdRef.current = projectId;
//   }, [projectId]);

//   // Add debug message with useCallback to prevent recreation
//   const addDebugMessage = useCallback((message: string) => {
//     console.log(`[QueryBuilder] ${message}`);
//     setDebugInfo((prev) => [
//       ...prev.slice(-20),
//       `${new Date().toLocaleTimeString()}: ${message}`,
//     ]);
//   }, []);

//   // Initialize with fallback data for immediate dropdown display
//   useEffect(() => {
//     const fallbackForResourceType = FALLBACK_DATA[resourceType];
//     if (fallbackForResourceType) {
//       addDebugMessage(`Initializing with fallback data for ${resourceType}`);
//       setLabelOptions(fallbackForResourceType);

//       // Set initial API status for all labels
//       const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
//       if (mapping) {
//         const initialStatus: ApiStatus = {};
//         mapping.labels.forEach((label) => {
//           const hasApiConfig = (GCP_API_ENDPOINTS as any)[resourceType]?.[
//             label
//           ];
//           initialStatus[label] = hasApiConfig
//             ? { status: "fallback", message: "Using fallback data initially" }
//             : { status: "fallback", message: "No API endpoint available" };
//         });
//         setApiStatus(initialStatus);
//       }
//     }
//   }, [resourceType, addDebugMessage]);

//   // Helper: fetch with auth and cache
//   const fetchWithAuth = useCallback(
//     async (key: string, endpoint: string) => {
//       addDebugMessage(`Attempting API call: ${endpoint}`);

//       if (!accesstoken) {
//         addDebugMessage("No access token - using fallback data");
//         throw new Error("No access token available");
//       }

//       const now = Date.now();
//       const cached = apiCache.get(key);
//       if (cached && now - cached.timestamp < CACHE_TTL) {
//         addDebugMessage(`Using cached response for: ${key}`);
//         return cached.data;
//       }

//       try {
//         const response = await fetch(endpoint, {
//           headers: {
//             Authorization: `Bearer ${accesstoken}`,
//             "Content-Type": "application/json",
//           },
//         });

//         addDebugMessage(`API response status: ${response.status}`);

//         if (!response.ok) {
//           const errorText = await response.text();
//           addDebugMessage(`API error: ${response.status} - ${errorText}`);
//           throw new Error(`API call failed: ${response.status} - ${errorText}`);
//         }

//         const data = await response.json();
//         addDebugMessage(`API call successful for: ${key}`);
//         apiCache.set(key, { data, timestamp: now });
//         return data;
//       } catch (error: any) {
//         addDebugMessage(`API call failed: ${error.message}`);
//         throw error;
//       }
//     },
//     [accesstoken, addDebugMessage]
//   );

//   // Helper function to transform API data with logging
//   const transformApiData = useCallback(
//     (resourceType: string, label: string, data: any) => {
//       const apiConfig = (GCP_API_ENDPOINTS as any)[resourceType]?.[label];
//       if (!apiConfig || !apiConfig.transform) {
//         console.log(`No transform function for ${resourceType}.${label}`);
//         return [];
//       }

//       console.log(`API response for ${resourceType}.${label}:`, data);
//       const result = apiConfig.transform(data);
//       console.log(`Transformed result for ${resourceType}.${label}:`, result);
//       return result;
//     },
//     []
//   );

//   // Fetch dropdown options for a label
//   const fetchDropdownOptions = useCallback(
//     async (
//       label: string,
//       currentProjectId: string,
//       labelDeps: Record<string, string>
//     ) => {
//       const currentResourceType = resourceTypeRef.current;
//       addDebugMessage(`Fetching options for ${currentResourceType}.${label}`);

//       const apiConfig = (GCP_API_ENDPOINTS as any)[currentResourceType]?.[
//         label
//       ];
//       if (!apiConfig) {
//         addDebugMessage(
//           `No API config found for ${currentResourceType}.${label} - using fallback`
//         );
//         const fallbackOptions =
//           FALLBACK_DATA[currentResourceType]?.[label] || [];
//         setLabelOptions((prev) => ({ ...prev, [label]: fallbackOptions }));
//         setApiStatus((prev) => ({
//           ...prev,
//           [label]: { status: "fallback", message: "No API endpoint available" },
//         }));
//         return fallbackOptions;
//       }

//       // Check if endpoint is marked as unavailable
//       const endpoint = apiConfig.endpoint(currentProjectId);
//       if (endpoint.startsWith("#")) {
//         addDebugMessage(`API endpoint unavailable for ${label}: ${endpoint}`);
//         const fallbackOptions =
//           FALLBACK_DATA[currentResourceType]?.[label] || [];
//         setLabelOptions((prev) => ({ ...prev, [label]: fallbackOptions }));
//         setApiStatus((prev) => ({
//           ...prev,
//           [label]: {
//             status: "fallback",
//             message: `API not available: ${endpoint.replace("#", "")}`,
//             endpoint,
//           },
//         }));
//         return fallbackOptions;
//       }

//       setLabelLoading((prev) => ({ ...prev, [label]: true }));
//       setLabelError((prev) => ({ ...prev, [label]: "" }));
//       setApiStatus((prev) => ({
//         ...prev,
//         [label]: {
//           status: "loading",
//           message: "Fetching from API...",
//           endpoint,
//         },
//       }));

//       try {
//         let finalEndpoint: string;

//         // Build endpoint with dependencies
//         if (apiConfig.dependsOn) {
//           if (typeof apiConfig.dependsOn === "string") {
//             const depValue = labelDeps[apiConfig.dependsOn];
//             if (!depValue) {
//               addDebugMessage(
//                 `Dependency ${apiConfig.dependsOn} not satisfied for ${label}`
//               );
//               setLabelLoading((prev) => ({ ...prev, [label]: false }));
//               setApiStatus((prev) => ({
//                 ...prev,
//                 [label]: {
//                   status: "fallback",
//                   message: `Waiting for ${apiConfig.dependsOn} selection`,
//                   endpoint,
//                 },
//               }));
//               return [];
//             }
//             finalEndpoint = apiConfig.endpoint(currentProjectId, depValue);
//           } else if (Array.isArray(apiConfig.dependsOn)) {
//             const depValues = apiConfig.dependsOn.map(
//               (dep: string) => labelDeps[dep]
//             );
//             if (depValues.some((val: any) => !val)) {
//               addDebugMessage(`Some dependencies not satisfied for ${label}`);
//               setLabelLoading((prev) => ({ ...prev, [label]: false }));
//               setApiStatus((prev) => ({
//                 ...prev,
//                 [label]: {
//                   status: "fallback",
//                   message: `Waiting for dependencies: ${apiConfig.dependsOn.join(
//                     ", "
//                   )}`,
//                   endpoint,
//                 },
//               }));
//               return [];
//             }
//             finalEndpoint = apiConfig.endpoint(currentProjectId, ...depValues);
//           } else {
//             finalEndpoint = apiConfig.endpoint(currentProjectId);
//           }
//         } else {
//           finalEndpoint = apiConfig.endpoint(currentProjectId);
//         }

//         const cacheKey = `${currentResourceType}:${label}:${finalEndpoint}`;
//         const data = await fetchWithAuth(cacheKey, finalEndpoint);
//         const options = transformApiData(currentResourceType, label, data);

//         addDebugMessage(
//           `Successfully fetched ${options.length} options for ${label}`
//         );

//         setLabelOptions((prev) => ({ ...prev, [label]: options }));
//         setLabelLoading((prev) => ({ ...prev, [label]: false }));
//         setApiStatus((prev) => ({
//           ...prev,
//           [label]: {
//             status: "success",
//             message: `Loaded ${options.length} items from API`,
//             endpoint: finalEndpoint,
//           },
//         }));
//         return options;
//       } catch (err: any) {
//         addDebugMessage(`Error fetching options for ${label}: ${err.message}`);

//         // Fall back to static data on API failure
//         const fallbackOptions =
//           FALLBACK_DATA[currentResourceType]?.[label] || [];
//         addDebugMessage(
//           `Using fallback data for ${label}: ${fallbackOptions.length} options`
//         );

//         setLabelOptions((prev) => ({ ...prev, [label]: fallbackOptions }));
//         setLabelLoading((prev) => ({ ...prev, [label]: false }));
//         setLabelError((prev) => ({
//           ...prev,
//           [label]: `API failed: ${err.message}`,
//         }));
//         setApiStatus((prev) => ({
//           ...prev,
//           [label]: {
//             status: "error",
//             message: `API failed: ${err.message}. Using fallback data.`,
//             endpoint,
//           },
//         }));

//         return fallbackOptions;
//       }
//     },
//     [fetchWithAuth, transformApiData, addDebugMessage]
//   );

//   // Handle resource type change - memoized to prevent infinite loops
//   const handleResourceTypeChange = useCallback(
//     (newResourceType: string) => {
//       addDebugMessage(`Resource type changed to: ${newResourceType}`);
//       setResourceType(newResourceType);
//       setResourceLabels({});
//       setAdditionalQueries([]);
//       setLabelLoading({});
//       setLabelError({});
//       setDependencyValues({});
//       setApiStatus({});

//       // Update tab without causing re-renders
//       const updatedTab = {
//         ...tab,
//         title: newResourceType
//           .replace(/_/g, " ")
//           .replace(/\b\w/g, (l) => l.toUpperCase()),
//         filters: { ...tab.filters, resourceType: newResourceType },
//       };

//       // Use setTimeout to break the potential loop
//       setTimeout(() => {
//         onUpdateTab(updatedTab);
//       }, 0);
//     },
//     [tab, onUpdateTab, addDebugMessage]
//   );

//   // Fetch options for all labels when component mounts or resourceType changes
//   useEffect(() => {
//     const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
//     if (!mapping || !projectId) {
//       addDebugMessage(
//         `Skipping label fetch - mapping: ${!!mapping}, projectId: ${!!projectId}`
//       );
//       return;
//     }

//     addDebugMessage(
//       `Fetching options for ${resourceType} labels: ${mapping.labels.join(
//         ", "
//       )}`
//     );

//     // Fetch options for labels that don't have dependencies first
//     mapping.labels.forEach((label) => {
//       const apiConfig = (GCP_API_ENDPOINTS as any)[resourceType]?.[label];
//       if (!apiConfig || !apiConfig.dependsOn) {
//         addDebugMessage(`Fetching independent label: ${label}`);
//         fetchDropdownOptions(label, projectId, {});
//       } else {
//         addDebugMessage(
//           `Skipping dependent label: ${label} (depends on: ${apiConfig.dependsOn})`
//         );
//       }
//     });
//   }, [resourceType, projectId, fetchDropdownOptions, addDebugMessage]);

//   // Handle dependencies: refetch dependent dropdowns when a dependency changes
//   useEffect(() => {
//     if (Object.keys(dependencyValues).length === 0) return;

//     const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
//     if (!mapping || !projectId) return;

//     addDebugMessage(
//       `Dependencies changed: ${JSON.stringify(dependencyValues)}`
//     );

//     mapping.labels.forEach((label) => {
//       const apiConfig = (GCP_API_ENDPOINTS as any)[resourceType]?.[label];
//       if (apiConfig && apiConfig.dependsOn) {
//         if (typeof apiConfig.dependsOn === "string") {
//           if (dependencyValues[apiConfig.dependsOn]) {
//             addDebugMessage(`Fetching dependent label: ${label}`);
//             fetchDropdownOptions(label, projectId, dependencyValues);
//           }
//         } else if (Array.isArray(apiConfig.dependsOn)) {
//           const allDepsSet = apiConfig.dependsOn.every(
//             (dep: string) => dependencyValues[dep]
//           );
//           if (allDepsSet) {
//             addDebugMessage(`Fetching dependent label: ${label}`);
//             fetchDropdownOptions(label, projectId, dependencyValues);
//           }
//         }
//       }
//     });
//   }, [
//     dependencyValues,
//     resourceType,
//     projectId,
//     fetchDropdownOptions,
//     addDebugMessage,
//   ]);

//   // Build query preview
//   useEffect(() => {
//     let query = `resource.type="${resourceType}"`;
//     const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
//     if (mapping) {
//       mapping.labels.forEach((label: string) => {
//         if (resourceLabels[label]) {
//           query += ` AND resource.labels.${label}="${resourceLabels[label]}"`;
//         }
//       });
//     }
//     additionalQueries.forEach((q: any) => {
//       if (q.type === "severity" && q.value) {
//         query += ` AND severity="${q.value}"`;
//       } else if (q.type === "timestamp" && q.value) {
//         query += ` AND timestamp${q.operator || ">="}"${q.value}"`;
//       } else if (q.type === "custom" && q.value) {
//         query += ` AND (${q.value})`;
//       } else if (q.type && q.value) {
//         query += ` AND ${q.type}="${q.value}"`;
//       }
//     });
//     setQueryPreview(query);
//   }, [resourceType, resourceLabels, additionalQueries]);

//   // Handle label change
//   const handleLabelChange = useCallback(
//     (label: string, value: string) => {
//       setResourceLabels((prev) => ({ ...prev, [label]: value }));
//       // If this label is a dependency for others, update dependencyValues
//       setDependencyValues((prev) => ({ ...prev, [label]: value }));
//       addDebugMessage(`Label ${label} changed to: ${value}`);
//     },
//     [addDebugMessage]
//   );

//   // Handle add query
//   const handleAddQuery = useCallback(
//     (type: string, value: string, operator?: string) => {
//       setAdditionalQueries((prev) => [...prev, { type, value, operator }]);
//       setShowAddQuery(false);
//     },
//     []
//   );

//   // Remove query condition
//   const handleRemoveQuery = useCallback((idx: number) => {
//     setAdditionalQueries((prev) => prev.filter((_, i) => i !== idx));
//   }, []);

//   // Validate before submit
//   const handleSubmit = useCallback(() => {
//     if (!resourceType) {
//       setError("Resource type is required.");
//       return;
//     }
//     setError("");
//     onQuerySubmit(queryPreview);
//   }, [resourceType, queryPreview, onQuerySubmit]);

//   // Clear all selections
//   const handleClearAll = useCallback(() => {
//     setResourceLabels({});
//     setAdditionalQueries([]);
//     setError("");
//     setDependencyValues({});
//   }, []);

//   // Get status icon for API calls
//   const getStatusIcon = (status: string) => {
//     switch (status) {
//       case "loading":
//         return <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />;
//       case "success":
//         return <CheckCircle className="w-3 h-3 text-green-400" />;
//       case "error":
//         return <XCircle className="w-3 h-3 text-red-400" />;
//       case "fallback":
//         return <AlertCircle className="w-3 h-3 text-yellow-400" />;
//       default:
//         return null;
//     }
//   };

//   // UI for API status display
//   const renderApiStatus = () => {
//     const statusEntries = Object.entries(apiStatus);
//     if (statusEntries.length === 0) return null;

//     return (
//       <div className="mb-4 p-3 bg-gray-800 border border-gray-700 rounded">
//         <div className="text-xs text-gray-300 mb-2">API Status:</div>
//         <div className="space-y-1">
//           {statusEntries.map(([label, status]) => (
//             <div key={label} className="flex items-center gap-2 text-xs">
//               {getStatusIcon(status.status)}
//               <span className="text-gray-400 min-w-[120px]">{label}:</span>
//               <span
//                 className={`
//                 ${
//                   status.status === "success"
//                     ? "text-green-400"
//                     : status.status === "error"
//                     ? "text-red-400"
//                     : status.status === "loading"
//                     ? "text-blue-400"
//                     : "text-yellow-400"
//                 }
//               `}
//               >
//                 {status.message}
//               </span>
//             </div>
//           ))}
//         </div>
//       </div>
//     );
//   };

//   // UI for Add Query Modal/Dropdown
//   const renderAddQueryModal = () => {
//     const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
//     if (!mapping) return null;

//     return (
//       <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
//         <div className="bg-gray-900 border border-gray-700 rounded-lg shadow-xl p-6 w-80 max-w-md mx-4">
//           <div className="mb-4 text-sm font-medium text-gray-200">
//             Add Query Condition
//           </div>
//           <div className="space-y-2 mb-4">
//             {mapping.additionalQueries.map((q: string) => (
//               <button
//                 key={q}
//                 className="w-full text-left px-3 py-2 rounded hover:bg-gray-800 text-gray-100 text-sm transition-colors"
//                 onClick={() => {
//                   if (q === "severity") {
//                     handleAddQuery("severity", SEVERITY_OPTIONS[0]);
//                   } else if (q === "timestamp") {
//                     handleAddQuery("timestamp", new Date().toISOString(), ">=");
//                   } else {
//                     handleAddQuery(q, "");
//                   }
//                 }}
//               >
//                 {q}
//               </button>
//             ))}
//             <button
//               className="w-full text-left px-3 py-2 rounded hover:bg-gray-800 text-gray-100 text-sm transition-colors"
//               onClick={() => handleAddQuery("custom", "")}
//             >
//               Custom Filter
//             </button>
//           </div>
//           <div className="flex gap-2">
//             <button
//               className="flex-1 py-2 bg-gray-700 text-gray-200 rounded hover:bg-gray-600 transition-colors"
//               onClick={() => setShowAddQuery(false)}
//             >
//               Cancel
//             </button>
//           </div>
//         </div>
//       </div>
//     );
//   };

//   // UI for resource label dropdowns
//   const renderLabelDropdowns = () => {
//     const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
//     if (!mapping) return null;

//     return mapping.labels.map((label: string) => {
//       const isLoading = labelLoading[label];
//       const error = labelError[label];
//       const options = labelOptions[label] || [];
//       const hasOptions = options.length > 0;
//       const status = apiStatus[label];

//       return (
//         <div key={label} className="flex items-center gap-2 mb-3">
//           <span className="text-gray-300 text-sm min-w-[140px] flex items-center gap-1">
//             resource.labels.{label} ={status && getStatusIcon(status.status)}
//           </span>

//           {isLoading ? (
//             <div className="flex items-center gap-2">
//               <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
//               <span className="text-gray-400 text-sm">Loading...</span>
//             </div>
//           ) : hasOptions ? (
//             <div className="flex-1">
//               <select
//                 className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-gray-100 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
//                 value={resourceLabels[label] || ""}
//                 onChange={(e) => handleLabelChange(label, e.target.value)}
//               >
//                 <option value="">Select {label}</option>
//                 {options.map((option: string) => (
//                   <option key={option} value={option}>
//                     {option}
//                   </option>
//                 ))}
//               </select>
//               {status && status.status !== "success" && (
//                 <div className="flex items-center gap-1 mt-1 text-xs">
//                   {getStatusIcon(status.status)}
//                   <span
//                     className={`
//                     ${
//                       status.status === "error"
//                         ? "text-red-400"
//                         : "text-yellow-400"
//                     }
//                   `}
//                   >
//                     {status.message}
//                   </span>
//                 </div>
//               )}
//             </div>
//           ) : (
//             <div className="flex-1">
//               <input
//                 type="text"
//                 className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-gray-100 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
//                 value={resourceLabels[label] || ""}
//                 onChange={(e) => handleLabelChange(label, e.target.value)}
//                 placeholder={`Enter ${label}`}
//               />
//               {status && (
//                 <div className="flex items-center gap-1 mt-1 text-xs">
//                   {getStatusIcon(status.status)}
//                   <span
//                     className={`
//                     ${
//                       status.status === "error"
//                         ? "text-red-400"
//                         : "text-yellow-400"
//                     }
//                   `}
//                   >
//                     {status.message}
//                   </span>
//                 </div>
//               )}
//             </div>
//           )}
//         </div>
//       );
//     });
//   };

//   // Early return for safety
//   if (!isActive || !tab) {
//     return (
//       <div className="w-full max-w-4xl mx-auto mt-6 mb-8 p-6 bg-gray-900/90 border border-gray-800 rounded-2xl shadow-xl">
//         <div className="text-center text-gray-400">
//           Query Builder not available
//         </div>
//       </div>
//     );
//   }

//   return (
//     <div className="w-full max-w-4xl mx-auto mt-6 mb-8 p-6 bg-gray-900/90 border border-gray-800 rounded-2xl shadow-xl">
//       <div className="mb-6">
//         <div className="flex items-center justify-between mb-4">
//           <h2 className="text-lg font-semibold text-blue-300 flex items-center gap-2">
//             <span>Query Builder</span>
//             {Object.values(apiStatus).some(
//               (s) => s.status === "fallback" || s.status === "error"
//             ) && (
//               <span className="text-xs bg-yellow-500/20 text-yellow-300 px-2 py-1 rounded">
//                 Using Test Data
//               </span>
//             )}
//           </h2>
//           <button
//             onClick={() => setShowDebug(!showDebug)}
//             className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
//           >
//             <Bug className="w-3 h-3" />
//             Debug
//           </button>
//         </div>

//         {!accesstoken && (
//           <div className="mb-4 p-3 bg-blue-900/30 border border-blue-700 rounded text-blue-300 text-sm">
//             <div className="flex items-center gap-2">
//               <AlertCircle className="w-4 h-4" />
//               <span>
//                 No authentication token. All dropdowns will use test data.
//               </span>
//             </div>
//           </div>
//         )}

//         {showDebug && (
//           <>
//             {renderApiStatus()}
//             <div className="mb-4 p-3 bg-gray-800 border border-gray-700 rounded">
//               <div className="text-xs text-gray-300 mb-2">
//                 Debug Information:
//               </div>
//               <div className="max-h-32 overflow-y-auto text-xs text-gray-400 space-y-1">
//                 {debugInfo.map((info, i) => (
//                   <div key={i}>{info}</div>
//                 ))}
//               </div>
//             </div>
//           </>
//         )}

//         {/* Resource Type Dropdown */}
//         <div className="flex items-center gap-2 mb-4">
//           <span className="text-gray-300 text-sm min-w-[140px]">
//             resource.type =
//           </span>
//           <select
//             className="flex-1 bg-gray-800 border border-blue-600 rounded px-3 py-2 text-blue-300 text-sm font-semibold focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
//             value={resourceType}
//             onChange={(e) => handleResourceTypeChange(e.target.value)}
//           >
//             {Object.keys(GCP_RESOURCE_MAPPINGS).map((type: string) => (
//               <option key={type} value={type}>
//                 {type}
//               </option>
//             ))}
//           </select>
//         </div>

//         {renderLabelDropdowns()}

//         {additionalQueries.map((q, idx) => (
//           <div key={idx} className="flex items-center gap-2 mb-2">
//             <span className="text-gray-300 text-sm min-w-[140px]">
//               {q.type} =
//             </span>
//             {q.type === "severity" ? (
//               <select
//                 className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-gray-100 text-sm"
//                 value={q.value}
//                 onChange={(e) => {
//                   const val = e.target.value;
//                   setAdditionalQueries((prev) =>
//                     prev.map((item, i) =>
//                       i === idx ? { ...item, value: val } : item
//                     )
//                   );
//                 }}
//               >
//                 {SEVERITY_OPTIONS.map((s) => (
//                   <option key={s} value={s}>
//                     {s}
//                   </option>
//                 ))}
//               </select>
//             ) : (
//               <input
//                 type="text"
//                 className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-gray-100 text-sm"
//                 value={q.value}
//                 onChange={(e) => {
//                   const val = e.target.value;
//                   setAdditionalQueries((prev) =>
//                     prev.map((item, i) =>
//                       i === idx ? { ...item, value: val } : item
//                     )
//                   );
//                 }}
//                 placeholder={`Enter ${q.type}`}
//               />
//             )}
//             <button
//               className="p-1 text-gray-400 hover:text-red-400 transition-colors"
//               onClick={() => handleRemoveQuery(idx)}
//               title="Remove"
//             >
//               <Trash2 className="w-4 h-4" />
//             </button>
//           </div>
//         ))}

//         <div className="flex items-center gap-3 mt-6">
//           <button
//             className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded shadow transition-all"
//             onClick={() => setShowAddQuery(true)}
//             type="button"
//           >
//             <Plus className="w-4 h-4" /> Add Condition
//           </button>

//           <button
//             className="inline-flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded shadow transition-all"
//             onClick={handleClearAll}
//             type="button"
//           >
//             <Trash2 className="w-4 h-4" /> Clear All
//           </button>
//         </div>
//       </div>

//       <div className="mb-4">
//         <label className="block text-xs font-medium text-gray-400 mb-2">
//           Generated Query
//         </label>
//         <textarea
//           className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-200 text-xs font-mono resize-none"
//           value={queryPreview}
//           readOnly
//           rows={3}
//         />
//       </div>

//       {error && (
//         <div className="mb-4 text-red-400 text-sm font-medium">{error}</div>
//       )}

//       <div className="flex gap-3">
//         <button
//           className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold shadow disabled:opacity-50 disabled:cursor-not-allowed transition-all"
//           onClick={handleSubmit}
//           type="button"
//           disabled={!queryPreview.trim()}
//         >
//           Submit Query
//         </button>
//       </div>

//       {/* Add Query Modal */}
//       {showAddQuery && renderAddQueryModal()}
//     </div>
//   );
// };

import React, { useState, useEffect, useCallback, useRef } from "react";
import { GCP_RESOURCE_MAPPINGS as RAW_MAPPINGS } from "../data/gcpResourceMappings";
import { GCP_API_ENDPOINTS as RAW_API_ENDPOINTS } from "../data/gcpApiEndpoints";
import { FALLBACK_DATA as RAW_FALLBACK_DATA } from "../data/fallbackData";
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
} from "lucide-react";
import type { LogTab } from "../types/gcp";
import { useAuth } from "../contexts/Auth";

const GCP_RESOURCE_MAPPINGS: Record<
  string,
  { labels: string[]; additionalQueries: string[] }
> = RAW_MAPPINGS;

const GCP_API_ENDPOINTS: Record<string, any> = RAW_API_ENDPOINTS;
const FALLBACK_DATA: Record<
  string,
  Record<string, string[]>
> = RAW_FALLBACK_DATA;

const SEVERITY_OPTIONS = ["ERROR", "WARNING", "INFO", "DEBUG"];
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes
const apiCache = new Map<string, { data: any; timestamp: number }>();

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
  const { accesstoken } = useAuth();
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

  // Use refs to track the latest values to prevent stale closures
  const resourceTypeRef = useRef(resourceType);
  const projectIdRef = useRef(projectId);

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

  // Initialize with fallback data for immediate dropdown display
  useEffect(() => {
    const fallbackForResourceType = FALLBACK_DATA[resourceType];
    if (fallbackForResourceType) {
      addDebugMessage(`Initializing with fallback data for ${resourceType}`);
      setLabelOptions(fallbackForResourceType);

      // Set initial API status for all labels
      const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
      if (mapping) {
        const initialStatus: ApiStatus = {};
        mapping.labels.forEach((label) => {
          const hasApiConfig = (GCP_API_ENDPOINTS as any)[resourceType]?.[
            label
          ];
          initialStatus[label] = hasApiConfig
            ? { status: "fallback", message: "Using fallback data initially" }
            : { status: "fallback", message: "No API endpoint available" };
        });
        setApiStatus(initialStatus);
      }
    }
  }, [resourceType, addDebugMessage]);

  // Helper: fetch with auth and cache
  const fetchWithAuth = useCallback(
    async (key: string, endpoint: string) => {
      addDebugMessage(`Attempting API call: ${endpoint}`);

      if (!accesstoken) {
        addDebugMessage("No access token - using fallback data");
        throw new Error("No access token available");
      }

      const now = Date.now();
      const cached = apiCache.get(key);
      if (cached && now - cached.timestamp < CACHE_TTL) {
        addDebugMessage(`Using cached response for: ${key}`);
        return cached.data;
      }

      try {
        const response = await fetch(endpoint, {
          headers: {
            Authorization: `Bearer ${accesstoken}`,
            "Content-Type": "application/json",
          },
        });

        addDebugMessage(`API response status: ${response.status}`);

        if (!response.ok) {
          const errorText = await response.text();
          addDebugMessage(`API error: ${response.status} - ${errorText}`);
          throw new Error(`API call failed: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        addDebugMessage(`API call successful for: ${key}`);
        apiCache.set(key, { data, timestamp: now });
        return data;
      } catch (error: any) {
        addDebugMessage(`API call failed: ${error.message}`);
        throw error;
      }
    },
    [accesstoken, addDebugMessage]
  );

  // Helper function to transform API data with logging
  const transformApiData = useCallback(
    (resourceType: string, label: string, data: any) => {
      const apiConfig = (GCP_API_ENDPOINTS as any)[resourceType]?.[label];
      if (!apiConfig || !apiConfig.transform) {
        console.log(`No transform function for ${resourceType}.${label}`);
        return [];
      }

      console.log(`API response for ${resourceType}.${label}:`, data);
      const result = apiConfig.transform(data);
      console.log(`Transformed result for ${resourceType}.${label}:`, result);
      return result;
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
      addDebugMessage(`Fetching options for ${currentResourceType}.${label}`);

      const apiConfig = (GCP_API_ENDPOINTS as any)[currentResourceType]?.[
        label
      ];
      if (!apiConfig) {
        addDebugMessage(
          `No API config found for ${currentResourceType}.${label} - using fallback`
        );
        const fallbackOptions =
          FALLBACK_DATA[currentResourceType]?.[label] || [];
        setLabelOptions((prev) => ({ ...prev, [label]: fallbackOptions }));
        setApiStatus((prev) => ({
          ...prev,
          [label]: { status: "fallback", message: "No API endpoint available" },
        }));
        return fallbackOptions;
      }

      // Check if endpoint is marked as unavailable
      const endpoint = apiConfig.endpoint(currentProjectId);
      if (endpoint.startsWith("#")) {
        addDebugMessage(`API endpoint unavailable for ${label}: ${endpoint}`);
        const fallbackOptions =
          FALLBACK_DATA[currentResourceType]?.[label] || [];
        setLabelOptions((prev) => ({ ...prev, [label]: fallbackOptions }));
        setApiStatus((prev) => ({
          ...prev,
          [label]: {
            status: "fallback",
            message: `API not available: ${endpoint.replace("#", "")}`,
            endpoint,
          },
        }));
        return fallbackOptions;
      }

      setLabelLoading((prev) => ({ ...prev, [label]: true }));
      setLabelError((prev) => ({ ...prev, [label]: "" }));
      setApiStatus((prev) => ({
        ...prev,
        [label]: {
          status: "loading",
          message: "Fetching from API...",
          endpoint,
        },
      }));

      try {
        let finalEndpoint: string;

        // Build endpoint with dependencies
        if (apiConfig.dependsOn) {
          if (typeof apiConfig.dependsOn === "string") {
            const depValue = labelDeps[apiConfig.dependsOn];
            if (!depValue) {
              addDebugMessage(
                `Dependency ${apiConfig.dependsOn} not satisfied for ${label}`
              );
              setLabelLoading((prev) => ({ ...prev, [label]: false }));
              setApiStatus((prev) => ({
                ...prev,
                [label]: {
                  status: "fallback",
                  message: `Waiting for ${apiConfig.dependsOn} selection`,
                  endpoint,
                },
              }));
              return [];
            }
            finalEndpoint = apiConfig.endpoint(currentProjectId, depValue);
          } else if (Array.isArray(apiConfig.dependsOn)) {
            const depValues = apiConfig.dependsOn.map(
              (dep: string) => labelDeps[dep]
            );
            if (depValues.some((val: any) => !val)) {
              addDebugMessage(`Some dependencies not satisfied for ${label}`);
              setLabelLoading((prev) => ({ ...prev, [label]: false }));
              setApiStatus((prev) => ({
                ...prev,
                [label]: {
                  status: "fallback",
                  message: `Waiting for dependencies: ${apiConfig.dependsOn.join(
                    ", "
                  )}`,
                  endpoint,
                },
              }));
              return [];
            }
            finalEndpoint = apiConfig.endpoint(currentProjectId, ...depValues);
          } else {
            finalEndpoint = apiConfig.endpoint(currentProjectId);
          }
        } else {
          finalEndpoint = apiConfig.endpoint(currentProjectId);
        }

        const cacheKey = `${currentResourceType}:${label}:${finalEndpoint}`;
        const data = await fetchWithAuth(cacheKey, finalEndpoint);
        const options = transformApiData(currentResourceType, label, data);

        addDebugMessage(
          `Successfully fetched ${options.length} options for ${label}`
        );

        setLabelOptions((prev) => ({ ...prev, [label]: options }));
        setLabelLoading((prev) => ({ ...prev, [label]: false }));
        setApiStatus((prev) => ({
          ...prev,
          [label]: {
            status: "success",
            message: `Loaded ${options.length} items from API`,
            endpoint: finalEndpoint,
          },
        }));
        return options;
      } catch (err: any) {
        addDebugMessage(`Error fetching options for ${label}: ${err.message}`);

        // Fall back to static data on API failure
        const fallbackOptions =
          FALLBACK_DATA[currentResourceType]?.[label] || [];
        addDebugMessage(
          `Using fallback data for ${label}: ${fallbackOptions.length} options`
        );

        setLabelOptions((prev) => ({ ...prev, [label]: fallbackOptions }));
        setLabelLoading((prev) => ({ ...prev, [label]: false }));
        setLabelError((prev) => ({
          ...prev,
          [label]: `API failed: ${err.message}`,
        }));
        setApiStatus((prev) => ({
          ...prev,
          [label]: {
            status: "error",
            message: `API failed: ${err.message}. Using fallback data.`,
            endpoint,
          },
        }));

        return fallbackOptions;
      }
    },
    [fetchWithAuth, transformApiData, addDebugMessage]
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
        title: newResourceType
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
    const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
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
    mapping.labels.forEach((label) => {
      const apiConfig = (GCP_API_ENDPOINTS as any)[resourceType]?.[label];
      if (!apiConfig || !apiConfig.dependsOn) {
        addDebugMessage(`Fetching independent label: ${label}`);
        fetchDropdownOptions(label, projectId, {});
      } else {
        addDebugMessage(
          `Skipping dependent label: ${label} (depends on: ${apiConfig.dependsOn})`
        );
      }
    });
  }, [resourceType, projectId, fetchDropdownOptions, addDebugMessage]);

  // Handle dependencies: refetch dependent dropdowns when a dependency changes
  useEffect(() => {
    if (Object.keys(dependencyValues).length === 0) return;

    const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
    if (!mapping || !projectId) return;

    addDebugMessage(
      `Dependencies changed: ${JSON.stringify(dependencyValues)}`
    );

    mapping.labels.forEach((label) => {
      const apiConfig = (GCP_API_ENDPOINTS as any)[resourceType]?.[label];
      if (apiConfig && apiConfig.dependsOn) {
        if (typeof apiConfig.dependsOn === "string") {
          if (dependencyValues[apiConfig.dependsOn]) {
            addDebugMessage(`Fetching dependent label: ${label}`);
            fetchDropdownOptions(label, projectId, dependencyValues);
          }
        } else if (Array.isArray(apiConfig.dependsOn)) {
          const allDepsSet = apiConfig.dependsOn.every(
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
  ]);

  // Build query preview
  useEffect(() => {
    let query = `resource.type="${resourceType}"`;
    const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
    if (mapping) {
      mapping.labels.forEach((label: string) => {
        if (resourceLabels[label]) {
          query += ` AND resource.labels.${label}="${resourceLabels[label]}"`;
        }
      });
    }
    additionalQueries.forEach((q: any) => {
      if (q.type === "severity" && q.value) {
        query += ` AND severity="${q.value}"`;
      } else if (q.type === "timestamp" && q.value) {
        query += ` AND timestamp${q.operator || ">="}"${q.value}"`;
      } else if (q.type === "custom" && q.value) {
        query += ` AND (${q.value})`;
      } else if (q.type && q.value) {
        query += ` AND ${q.type}="${q.value}"`;
      }
    });
    setQueryPreview(query);
  }, [resourceType, resourceLabels, additionalQueries]);

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

  // UI for Add Query Modal/Dropdown
  const renderAddQueryModal = () => {
    const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
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
            {mapping.additionalQueries.map((q: string) => (
              <button
                key={q}
                className="w-full text-left px-4 py-3 rounded-xl hover:bg-slate-700/50 text-slate-200 text-sm transition-all duration-200 ease-in-out border border-transparent hover:border-slate-600/50"
                onClick={() => {
                  if (q === "severity") {
                    handleAddQuery("severity", SEVERITY_OPTIONS[0]);
                  } else if (q === "timestamp") {
                    handleAddQuery("timestamp", new Date().toISOString(), ">=");
                  } else {
                    handleAddQuery(q, "");
                  }
                }}
              >
                <span className="font-medium">{q}</span>
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
    const mapping = GCP_RESOURCE_MAPPINGS[resourceType];
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
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Query Builder
            </h2>
            {Object.values(apiStatus).some(
              (s) => s.status === "fallback" || s.status === "error"
            ) && (
              <span className="inline-flex items-center gap-1 text-xs bg-amber-500/20 text-amber-300 px-3 py-1.5 rounded-full border border-amber-500/20">
                <AlertCircle className="w-3 h-3" />
                Using Test Data
              </span>
            )}
          </div>

          <button
            onClick={() => setShowDebug(!showDebug)}
            className="flex items-center gap-2 px-3 py-2 text-xs bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded-lg transition-all duration-200 ease-in-out border border-slate-600/50"
          >
            <Bug className="w-4 h-4" />
            Debug
          </button>
        </div>

        {!accesstoken && (
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

        {showDebug && (
          <>
            {renderApiStatus()}
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
            <SearchableSelect
              options={Object.keys(GCP_RESOURCE_MAPPINGS)}
              value={resourceType}
              onChange={handleResourceTypeChange}
              placeholder="Select resource type"
            />
          </div>
        </div>
      </div>

      {/* Resource Labels */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-slate-200 mb-6">
          Resource Labels
        </h3>
        {renderLabelDropdowns()}
      </div>

      {/* Additional Query Conditions */}
      {additionalQueries.length > 0 && (
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
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-4 mb-8">
        <button
          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 ease-in-out font-medium"
          onClick={() => setShowAddQuery(true)}
          type="button"
        >
          <Plus className="w-4 h-4" /> Add Condition
        </button>

        <button
          className="inline-flex items-center gap-2 px-6 py-3 bg-slate-700/50 hover:bg-slate-700 text-slate-200 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 ease-in-out font-medium"
          onClick={handleClearAll}
          type="button"
        >
          <Trash2 className="w-4 h-4" /> Clear All
        </button>
      </div>

      {/* Query Preview */}
      <div className="mb-8">
        <label className="block text-sm font-medium text-slate-300 mb-3">
          Generated Query
        </label>
        <div className="relative">
          <textarea
            className="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-slate-200 text-sm font-mono resize-none backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all duration-200 ease-in-out"
            value={queryPreview}
            readOnly
            rows={4}
          />
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
    </div>
  );
};
