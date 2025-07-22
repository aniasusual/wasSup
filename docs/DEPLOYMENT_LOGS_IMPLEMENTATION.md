# Deployment-Specific Log Fetching Implementation

## Overview

This implementation provides deployment-specific log fetching for GCP services by directly calling the GCP Logging API from the frontend. The system supports multiple GCP services and automatically applies the correct filters based on the service type and deployment selection.

## Architecture

### 1. Log Service (`frontend/src/services/logService.ts`)

The log service handles direct communication with the GCP Logging API v2. It provides:

- **`fetchLogs(params: LogQueryParams)`**: Main function to fetch logs with deployment-specific filtering
- **`buildFilterString(params: LogQueryParams)`**: Builds the appropriate filter string based on service type and deployment

### 2. Deployment Service (`frontend/src/services/deploymentService.ts`)

Enhanced deployment service that fetches deployments for different GCP services:

- **Cloud Run**: Fetches services from Cloud Run API
- **GKE**: Fetches clusters from Container API
- **Compute Engine**: Fetches instances from Compute API
- **Cloud Functions**: Fetches functions from Cloud Functions API
- **App Engine**: Fetches services and versions

### 3. Filter Logic

The system automatically applies the correct resource labels based on service type:

#### Cloud Run (`cloud_run_revision`)

```javascript
resource.type="cloud_run_revision" AND
resource.labels.service_name="service-name" AND
resource.labels.location="us-central1"
```

#### GKE (`k8s_container`)

```javascript
resource.type="k8s_container" AND
resource.labels.pod_name="pod-name" AND
resource.labels.namespace_name="namespace"
```

#### Compute Engine (`gce_instance`)

```javascript
resource.type="gce_instance" AND
resource.labels.instance_name="instance-name" AND
resource.labels.zone="us-central1-a"
```

#### Cloud Functions (`cloud_function`)

```javascript
resource.type="cloud_function" AND
resource.labels.function_name="function-name" AND
resource.labels.region="us-central1"
```

## Usage

### 1. Select a Service

Users select a GCP service from the service selector. The system determines if the service is deployment-based.

### 2. Select a Deployment (if applicable)

For deployment-based services, users must select a specific deployment/instance to view logs.

### 3. Apply Filters

Users can apply various filters:

- **Severity**: ERROR, WARNING, INFO, DEBUG
- **Time Range**: 1h, 6h, 24h, 7d, 30d
- **Search Query**: Text search in log messages
- **Custom Query**: Advanced filter expressions

### 4. Fetch Logs

The system automatically:

1. Builds the appropriate filter string based on service type and deployment
2. Calls the GCP Logging API directly from the frontend
3. Transforms the response to match the application's log format
4. Displays logs in the log viewer

## Implementation Details

### Log Query Parameters

```typescript
interface LogQueryParams {
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
  };
  searchQuery?: string;
  pageSize?: number;
  pageToken?: string;
}
```

### Deployment Information

```typescript
interface DeploymentInfo {
  id: string;
  name: string;
  type: string;
  status: string;
  region?: string;
  zone?: string;
  namespace?: string;
  service?: string;
  // Service-specific fields
  service_name?: string; // Cloud Run
  revision_name?: string; // Cloud Run
  cluster_name?: string; // GKE
  pod_name?: string; // GKE
  instance_name?: string; // Compute Engine
  function_name?: string; // Cloud Functions
  location?: string; // Generic
}
```

## Error Handling

The implementation includes comprehensive error handling:

1. **API Access Errors**: Falls back to mock data when APIs are not accessible
2. **Authentication Errors**: Proper error messages for token issues
3. **Network Errors**: Graceful handling of network failures
4. **Invalid Filters**: Validation of filter parameters

## Security Considerations

1. **Token Management**: Uses access tokens from the authentication context
2. **API Permissions**: Requires appropriate GCP IAM permissions for each service
3. **CORS**: Handles CORS issues with direct API calls
4. **Rate Limiting**: Respects GCP API rate limits

## Future Enhancements

1. **Pagination**: Support for large log datasets with pagination
2. **Real-time Updates**: WebSocket or polling for real-time log updates
3. **Advanced Filtering**: More sophisticated filter combinations
4. **Export Functionality**: Export logs in various formats
5. **Log Analytics**: Built-in log analysis and insights
6. **Multi-service Support**: View logs from multiple services simultaneously

## Testing

The implementation includes fallback mock data for testing purposes when APIs are not accessible. This allows for development and testing without requiring full GCP access.

## Dependencies

- `axios`: HTTP client for API calls
- `@types/gcp`: TypeScript definitions for GCP services
- Authentication context for token management
