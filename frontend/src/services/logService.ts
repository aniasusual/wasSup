import { useAuth } from "../contexts/Auth";
import axios from "axios";

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
}

export interface LogResponse {
    logs: any[];
    nextPageToken?: string;
    totalEntries?: number;
}

export const useLogService = () => {
    const { accesstoken } = useAuth();

    const buildFilterString = (params: LogQueryParams): string => {
        const filters: string[] = [];

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

        // Custom query filter
        if (params.filters?.customQuery) {
            filters.push(`(${params.filters.customQuery})`);
        }

        // Time range filter
        const customStart = params.filters?.customStartTime;
        const customEnd = params.filters?.customEndTime;
        if (customStart || customEnd) {
            if (customStart) {
                filters.push(`timestamp>="${new Date(customStart).toISOString()}"`);
            }
            if (customEnd) {
                filters.push(`timestamp<="${new Date(customEnd).toISOString()}"`);
            }
        } else if (params.filters?.timeRange) {
            const now = new Date();
            let startTime: Date;

            switch (params.filters.timeRange) {
                case "1h":
                    startTime = new Date(now.getTime() - 60 * 60 * 1000);
                    break;
                case "6h":
                    startTime = new Date(now.getTime() - 6 * 60 * 60 * 1000);
                    break;
                case "24h":
                    startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                    break;
                case "7d":
                    startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                    break;
                case "30d":
                    startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                    break;
                default:
                    startTime = new Date(now.getTime() - 60 * 60 * 1000); // Default to 1 hour
            }

            filters.push(`timestamp>="${startTime.toISOString()}"`);
        }

        return filters.join(" AND ");
    };

    const fetchLogs = async (params: LogQueryParams): Promise<LogResponse> => {
        if (!accesstoken) {
            throw new Error("No authentication token available");
        }

        try {
            const filterString = buildFilterString(params);

            const requestBody: any = {
                resourceNames: [`projects/${params.projectId}`],
                filter: filterString,
                orderBy: "timestamp desc",
                pageSize: params.pageSize || 100
            };

            if (params.pageToken) {
                requestBody.pageToken = params.pageToken;
            }

            const response = await axios.post(
                'https://logging.googleapis.com/v2/entries:list',
                requestBody,
                {
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${accesstoken}`,
                    },
                }
            );

            // Transform the response to match our LogEntry format
            const logs = response.data.entries?.map((entry: any) => ({
                id: entry.insertId || Math.random().toString(),
                timestamp: new Date(entry.timestamp),
                severity: entry.severity || "DEFAULT",
                message: entry.textPayload || (entry.jsonPayload?.message || JSON.stringify(entry.jsonPayload) || ""),
                resource: {
                    type: entry.resource?.type || "",
                    labels: entry.resource?.labels || {}
                },
                labels: entry.labels || {},
                jsonPayload: entry.jsonPayload,
                textPayload: entry.textPayload,
                httpRequest: entry.httpRequest,
                traceId: entry.trace,
                spanId: entry.spanId,
                logName: entry.logName
            })) || [];

            return {
                logs,
                nextPageToken: response.data.nextPageToken,
                totalEntries: response.data.entries?.length || 0
            };

        } catch (error: any) {
            console.error("Error fetching logs:", error);
            if (error.response?.data?.error?.message) {
                throw new Error(error.response.data.error.message);
            }
            throw error;
        }
    };

    return {
        fetchLogs,
        buildFilterString
    };
}; 