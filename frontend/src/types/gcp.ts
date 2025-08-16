export interface GCPService {
    id: string;
    name: string;
    category: "compute" | "storage" | "networking" | "security" | "operations" | "data-analytics" | "ai-ml" | "api-dev" | "monitoring" | "scheduler" | "cache" | "other";
}

export interface FilterOption {
    id: string;
    name: string;
    type: "select" | "multiselect" | "text" | "date";
    options?: string[];
}

export interface LogTab {
    id: string;
    title: string;
    serviceId: string;
    deploymentId?: string;
    isActive: boolean;
    filters: FilterState;
    query: string;
    lastUpdated: Date;
    type?: 'standard' | 'insight';
    sourceMessageId?: string;
    primaryLogId?: string;
}

export interface FilterState {
    severity: string[];
    resourceType: string;
    logType: string[];
    sourceLocation: string;
    userAccount: string;
    requestId: string;
    timeRange: string;
    customQuery: string;
    customStartTime?: string;
    customEndTime?: string;
}

export interface ResourceInfo {
    type: string;
    labels: Record<string, string>;
}

export interface LogEntry {
    id: string;
    timestamp: Date;
    severity: "ERROR" | "WARNING" | "INFO" | "DEBUG";
    message: string;
    resource: ResourceInfo;
    labels: Record<string, string>;
    structuredData?: any;
    traceId?: string;
    spanId?: string;
    httpRequest?: {
        requestMethod: string;
        requestUrl: string;
        status: number;
        responseSize: string;
        userAgent: string;
    };
    textPayload?: string;
    jsonPayload?: any;
}

export interface GCPProject {
    id: string;
    name: string;
    displayName: string;
}

export interface DeploymentInfo {
    id: string;
    name: string;
    type: string;
    status: string;
    region?: string;
    zone?: string;
    namespace?: string;
    service?: string;
    // Additional fields for different service types
    service_name?: string; // For Cloud Run
    revision_name?: string; // For Cloud Run
    cluster_name?: string; // For GKE
    pod_name?: string; // For GKE
    instance_name?: string; // For Compute Engine
    function_name?: string; // For Cloud Functions
    location?: string; // Generic location field
} 