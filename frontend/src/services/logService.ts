import { useAuth } from "../contexts/Auth";
import axios from "axios";
import toast from "react-hot-toast";
import { parseGCPErrorMessage } from "../utils/errorUtils";

export interface LogQueryParams {
    projectId: string;
    serviceId: string;
    deploymentId?: string;
    deploymentData?: {
        service_name?: string;
        location?: string;
        region?: string;
        zone?: string;
        namespace?: string;
        pod_name?: string;
        instance_name?: string;
        function_name?: string;
    };
    filters?: {
        severity?: string[];
        resourceType?: string;
        logType?: string[];
        sourceLocation?: string;
        userAccount?: string;
        requestId?: string;
        timeRange?: string;
        customQuery?: string;
        customStartTime?: string;
        customEndTime?: string;
    };
    searchQuery?: string;
    pageSize?: number;
    pageToken?: string;
    filter?: string; // Added for direct filter string
}

export interface LogResponse {
    logs: any[];
    nextPageToken?: string;
    totalEntries?: number;
}

export const useLogService = () => {
    const { token, forceLogout } = useAuth();

    const buildFilterString = (params: LogQueryParams): string => {
        let baseFilter = params.filter || "";
        const filters: string[] = [];
        if (!baseFilter) {
            // Base resource type filter
            filters.push(`resource.type="${params.serviceId}"`);

            // Deployment-specific filters based on service type
            if (params.deploymentId) {
                switch (params.serviceId) {
                    case "cloud_run_revision":
                        // For Cloud Run, use service_name and location from deployment data
                        if (params.deploymentData?.service_name) {
                            filters.push(`resource.labels.service_name="${params.deploymentData.service_name}"`);
                        } else {
                            filters.push(`resource.labels.service_name="${params.deploymentId}"`);
                        }
                        if (params.deploymentData?.location) {
                            filters.push(`resource.labels.location="${params.deploymentData.location}"`);
                        }
                        break;
                    case "k8s_container":
                        // For GKE, filter by pod name or deployment name
                        if (params.deploymentData?.pod_name) {
                            filters.push(`resource.labels.pod_name="${params.deploymentData.pod_name}"`);
                        } else {
                            filters.push(`resource.labels.pod_name="${params.deploymentId}"`);
                        }
                        if (params.deploymentData?.namespace) {
                            filters.push(`resource.labels.namespace_name="${params.deploymentData.namespace}"`);
                        }
                        break;
                    case "gce_instance":
                        // For Compute Engine, filter by instance name
                        if (params.deploymentData?.instance_name) {
                            filters.push(`resource.labels.instance_name="${params.deploymentData.instance_name}"`);
                        } else {
                            filters.push(`resource.labels.instance_name="${params.deploymentId}"`);
                        }
                        if (params.deploymentData?.zone) {
                            filters.push(`resource.labels.zone="${params.deploymentData.zone}"`);
                        }
                        break;
                    case "gae_app":
                        // For App Engine, filter by service and version
                        if (params.deploymentData?.service_name) {
                            filters.push(`resource.labels.service="${params.deploymentData.service_name}"`);
                        } else {
                            filters.push(`resource.labels.service="${params.deploymentId}"`);
                        }
                        break;
                    case "cloud_function":
                        // For Cloud Functions, filter by function name
                        if (params.deploymentData?.function_name) {
                            filters.push(`resource.labels.function_name="${params.deploymentData.function_name}"`);
                        } else {
                            filters.push(`resource.labels.function_name="${params.deploymentId}"`);
                        }
                        if (params.deploymentData?.region) {
                            filters.push(`resource.labels.region="${params.deploymentData.region}"`);
                        }
                        break;
                    default:
                        // Generic deployment filter
                        filters.push(`resource.labels.deployment_id="${params.deploymentId}"`);
                }
            }

            // Severity filter
            if (params.filters?.severity && params.filters.severity.length > 0) {
                const severityFilter = params.filters.severity
                    .map(s => `severity="${s}"`)
                    .join(" OR ");
                filters.push(`(${severityFilter})`);
            }

            // Resource type filter
            if (params.filters?.resourceType) {
                filters.push(`resource.type="${params.filters.resourceType}"`);
            }

            // Search query filter
            if (params.searchQuery) {
                filters.push(`textPayload:"${params.searchQuery}"`);
            }
        } else {
            filters.push(baseFilter);
        }
        // Always append global search and time filters if present and valid
        if (params.filters?.customQuery && params.filters.customQuery.trim()) {
            filters.push(`(${params.filters.customQuery.trim()})`);
        }
        if (params.filters?.customStartTime) {
            const d = new Date(params.filters.customStartTime);
            if (!isNaN(d.getTime())) {
                filters.push(`timestamp>="${d.toISOString()}"`);
            }
        }
        if (params.filters?.customEndTime) {
            const d = new Date(params.filters.customEndTime);
            if (!isNaN(d.getTime())) {
                filters.push(`timestamp<="${d.toISOString()}"`);
            }
        }
        // Remove any empty or invalid filter parts
        return filters.filter(Boolean).join(" AND ");
    };

    const fetchLogs = async (params: LogQueryParams): Promise<LogResponse> => {
        if (!token) {
            forceLogout("No authentication token available");
            throw new Error("No authentication token available");
        }
        const filterString = buildFilterString(params);

        // Backend request body
        const backendRequestBody: any = {
            projectId: params.projectId,
            filter: filterString,
            orderBy: "timestamp desc",
            pageSize: params.pageSize || 1000,
        };
        if (params.pageToken) {
            backendRequestBody.pageToken = params.pageToken;
        }

        // Try backend first
        try {
            const response = await axios.post(
                '/api/v1/logs/fetch',
                backendRequestBody,
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            // If backend returns logs in expected format, return them
            if (response.data && Array.isArray(response.data.logs)) {
                return {
                    logs: response.data.logs,
                    nextPageToken: response.data.nextPageToken,
                    totalEntries: response.data.totalEntries,
                };
            }
            // If backend response is malformed, fall through to fallback
        } catch (error: any) {
            // Check for authentication/authorization errors
            if (error.response?.status === 401 || error.response?.status === 403) {
                forceLogout("Authentication token expired or invalid");
                throw new Error("Authentication failed");
            }

            // Fallback to direct Google API if backend fails
            console.warn("Backend log fetch failed, falling back to direct GCP API", error);

            // Show error toast for backend failure
            let errorMessage = "Failed to fetch logs from backend";
            if (error.response?.data?.detail) {
                errorMessage = error.response.data.detail;
            } else if (error.response?.status) {
                errorMessage = `${error.response.status} - ${error.response.statusText || 'Unknown error'}`;
            } else if (error.message) {
                errorMessage = error.message;
            } else {
                errorMessage = String(error);
            }
            const userFriendlyMessage = parseGCPErrorMessage(errorMessage);
            toast.error(`Failed to fetch logs: ${userFriendlyMessage}`);
            // Throw so callers can handle error via catch; prevents returning undefined
            throw new Error(errorMessage);
        }

        // Fallback: direct Google API call
        // try {
        //     const requestBody: any = {
        //         resourceNames: [`projects/${params.projectId}`],
        //         filter: filterString,
        //         orderBy: "timestamp desc",
        //         pageSize: params.pageSize || 100
        //     };
        //     if (params.pageToken) {
        //         requestBody.pageToken = params.pageToken;
        //     }
        //     const response = await axios.post(
        //         'https://logging.googleapis.com/v2/entries:list',
        //         requestBody,
        //         {
        //             headers: {
        //                 "Content-Type": "application/json",
        //                 Authorization: `Bearer ${accesstoken}`,
        //             },
        //         }
        //     );
        //     const logs = response.data.entries?.map((entry: any) => ({
        //         id: entry.insertId || Math.random().toString(),
        //         timestamp: new Date(entry.timestamp),
        //         severity: entry.severity || "DEFAULT",
        //         message: entry.textPayload || (entry.jsonPayload?.message || JSON.stringify(entry.jsonPayload) || ""),
        //         resource: {
        //             type: entry.resource?.type || "",
        //             labels: entry.resource?.labels || {}
        //         },
        //         labels: entry.labels || {},
        //         jsonPayload: entry.jsonPayload,
        //         textPayload: entry.textPayload,
        //         httpRequest: entry.httpRequest,
        //         traceId: entry.trace,
        //         spanId: entry.spanId,
        //         logName: entry.logName
        //     })) || [];
        //     return {
        //         logs,
        //         nextPageToken: response.data.nextPageToken,
        //         totalEntries: response.data.entries?.length || 0
        //     };
        // } catch (error: any) {
        //     console.error("Error fetching logs (fallback):", error);
        //     if (error.response?.data?.error?.message) {
        //         throw new Error(error.response.data.error.message);
        //     }
        //     throw error;
        // }
        // If fallback is disabled or not available, return an empty response to satisfy the contract
        return {
            logs: [],
            nextPageToken: undefined,
            totalEntries: 0,
        };
    };

    return {
        fetchLogs,
        buildFilterString
    };
}; 