export interface GCPService {
    id: string;
    name: string;
    category: "compute" | "storage" | "networking" | "security" | "operations";
    isDeploymentBased: boolean;
    icon: string;
    logTypes: string[];
    availableFilters: FilterOption[];
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
} 