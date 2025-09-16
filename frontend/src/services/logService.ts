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

        // Handle project_logs service type
        if (params.serviceId === "project_logs") {
            // For project logs, we don't add any resource type filters, allowing all logs
        }

        // If we have a base filter from query builder, use it as the primary filter
        if (baseFilter) {
            filters.push(baseFilter);
        } else {
            // Only build resource type and deployment filters if no base filter is provided
            // Base resource type filter - skip for project_logs
            if (params.serviceId !== "project_logs") {
                filters.push(`resource.type="${params.serviceId}"`);
            }

            // Deployment-specific filters based on service type
            if (params.deploymentId && params.serviceId !== "project_logs") {
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
                        break;
                    default:
                        // Generic deployment filter
                        filters.push(`resource.labels.deployment_id="${params.deploymentId}"`);
                        break;
                }
            }
        }

        // Add additional filters from the filters object
        if (params.filters) {
            // Only add severity filter if not already present in base filter
            if (params.filters.severity && params.filters.severity.length > 0 && !baseFilter.includes('severity')) {
                const severityFilter = params.filters.severity.map(s => `severity="${s}"`).join(' OR ');
                filters.push(`(${severityFilter})`);
            }

            // Add global search query if provided and not already in base filter
            if (params.filters.customQuery && !baseFilter.includes(params.filters.customQuery)) {
                filters.push(params.filters.customQuery);
            }

            // Time range filter (if custom start/end times are provided and not already in base filter)
            if (params.filters.customStartTime && params.filters.customEndTime && !baseFilter.includes('timestamp')) {
                // Convert datetime-local format to RFC 3339 format for GCP
                const startTime = new Date(params.filters.customStartTime).toISOString();
                const endTime = new Date(params.filters.customEndTime).toISOString();
                filters.push(`timestamp>="${startTime}" AND timestamp<="${endTime}"`);
            }
        }

        // Combine all filters
        const finalFilter = filters.length > 0 ? filters.join(' AND ') : "";

        // Debug logging for filter building
        console.log("Filter building:", {
            baseFilter: baseFilter,
            hasBaseFilter: !!baseFilter,
            serviceId: params.serviceId,
            filters: filters,
            finalFilter: finalFilter,
            customQuery: params.filters?.customQuery,
            customStartTime: params.filters?.customStartTime,
            customEndTime: params.filters?.customEndTime
        });

        // Debug logging for time filters
        if (params.filters?.customStartTime && params.filters?.customEndTime) {
            console.log("Time filters:", {
                customStartTime: params.filters.customStartTime,
                customEndTime: params.filters.customEndTime,
                startTime: new Date(params.filters.customStartTime).toISOString(),
                endTime: new Date(params.filters.customEndTime).toISOString(),
                finalFilter
            });
        }

        if (params.serviceId === "project_logs") {
        }

        return finalFilter;
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
            // If backend response is malformed, throw error
        } catch (error: any) {
            // Check for authentication/authorization errors
            if (error.response?.status === 401 || error.response?.status === 403) {
                forceLogout("Authentication token expired or invalid");
                throw new Error("Authentication failed");
            }

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

        // If backend fails, throw the error
        throw error;
    };

    return {
        fetchLogs,
        buildFilterString
    };
}; 