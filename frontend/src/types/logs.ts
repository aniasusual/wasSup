export interface LogEntry {
    id: string;
    timestamp: string;
    severity: 'ERROR' | 'WARNING' | 'INFO' | 'DEBUG';
    message: string;
    service: string;
    resource: {
        type: string;
        labels: Record<string, string>;
    };
}

export interface Filter {
    severity: string;
    service: string;
    timeRange: string;
    searchText: string;
}

export interface ChatMessage {
    id: string;
    content: string;
    sender: 'user' | 'ai';
    timestamp: Date;
}