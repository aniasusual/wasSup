# GCP Log Explorer System

A comprehensive log exploration system for Google Cloud Platform that allows users to view, filter, and analyze logs from any GCP service across all projects with an intuitive tabbed interface.

## Features

### 🚀 Core Features

- **Multi-Service Support**: View logs from all major GCP services including Compute Engine, Cloud Run, GKE, Cloud Storage, and more
- **Deployment-Aware Selection**: Intelligent service selection that adapts based on whether a service requires deployment selection
- **Advanced Filtering**: Comprehensive filtering by severity, resource type, time range, and custom queries
- **Tab Management**: Dynamic tab creation with close buttons, active state, and overflow handling
- **Real-time Log Streaming**: Live log updates with configurable refresh intervals
- **Export Functionality**: Export logs in JSON and CSV formats

### 🎨 User Interface

- **Modern Dark Theme**: Professional dark interface optimized for log viewing
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Keyboard Shortcuts**: Quick navigation and actions
- **Accessibility**: Screen reader support and keyboard navigation

### 🔍 Advanced Log Analysis

- **Structured Data Viewing**: Expandable JSON payload viewing
- **HTTP Request Details**: Complete HTTP request/response information
- **Trace Correlation**: Distributed tracing with trace and span IDs
- **Severity Color Coding**: Visual severity indicators for quick scanning
- **Search & Filter**: Real-time search with debouncing

## Architecture

### Frontend Components

#### Core Components

- `GCPServiceSelector`: Service selection with category grouping
- `DeploymentSelector`: Deployment selection for deployment-based services
- `LogTabs`: Tab management with scrollable interface
- `AdvancedFilters`: Comprehensive filtering panel
- `EnhancedLogViewer`: Advanced log display with structured data

#### Data Models

```typescript
interface GCPService {
  id: string;
  name: string;
  category: "compute" | "storage" | "networking" | "security" | "operations";
  isDeploymentBased: boolean;
  icon: string;
  logTypes: string[];
  availableFilters: FilterOption[];
}

interface LogTab {
  id: string;
  title: string;
  serviceId: string;
  deploymentId?: string;
  isActive: boolean;
  filters: FilterState;
  query: string;
  lastUpdated: Date;
}
```

### Backend Services

#### API Endpoints

- `GET /api/gcp/services`: Get available GCP services
- `GET /api/gcp/services/{service_id}/deployments`: Get deployments for a service
- `GET /api/gcp/logs`: Get logs with filtering
- `POST /api/gcp/logs/query`: Execute advanced queries
- `GET /api/gcp/logs/export`: Export logs in various formats
- `GET /api/gcp/projects`: Get available GCP projects

#### GCP Service Integration

- **Cloud Logging API**: Real-time log retrieval
- **Resource Manager API**: Project and resource discovery
- **Authentication**: Google Cloud IAM integration
- **Error Handling**: Graceful fallbacks to mock data

## Supported GCP Services

### Compute Services

- **Cloud Run**: Containerized applications
- **Google Kubernetes Engine (GKE)**: Container orchestration
- **Compute Engine**: Virtual machines
- **App Engine**: Platform-as-a-Service
- **Cloud Functions**: Serverless functions

### Storage Services

- **Cloud Storage**: Object storage
- **Cloud SQL**: Managed databases
- **Firestore**: NoSQL database
- **BigQuery**: Data warehouse

### Networking Services

- **VPC**: Virtual private cloud
- **Cloud Load Balancing**: Load distribution
- **Cloud CDN**: Content delivery

### Security Services

- **Cloud IAM**: Identity and access management
- **Cloud KMS**: Key management

### Operations Services

- **Cloud Monitoring**: Monitoring and alerting
- **Cloud Logging**: Centralized logging

## Installation & Setup

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+ and pip
- Google Cloud SDK
- GCP project with appropriate permissions

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### GCP Authentication

1. Install Google Cloud SDK
2. Run `gcloud auth application-default login`
3. Set your project: `gcloud config set project YOUR_PROJECT_ID`
4. Enable required APIs:
   ```bash
   gcloud services enable logging.googleapis.com
   gcloud services enable resourcemanager.googleapis.com
   ```

## Usage

### Basic Workflow

1. **Select Service**: Choose from the categorized GCP service list
2. **Select Deployment** (if applicable): Choose specific deployment for deployment-based services
3. **Configure Filters**: Set time range, severity, and other filters
4. **View Logs**: Browse logs with expandable structured data
5. **Export**: Download logs in your preferred format

### Advanced Features

- **Custom Queries**: Use GCP Cloud Logging query syntax
- **Real-time Updates**: Enable live log streaming
- **Tab Management**: Open multiple service/deployment combinations
- **Search**: Real-time search across log messages and metadata

## Configuration

### Environment Variables

```bash
# Backend
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your-project-id
LOG_LEVEL=INFO

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_GCP_PROJECT_ID=your-project-id
```

### Customization

- **Service Configuration**: Add new services in `frontend/src/data/gcpServices.ts`
- **Filter Options**: Customize available filters per service
- **UI Theme**: Modify Tailwind CSS classes for theming
- **API Endpoints**: Extend backend routes for additional functionality

## Development

### Project Structure

```
wasSup/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── GCPServiceSelector.tsx
│   │   │   ├── DeploymentSelector.tsx
│   │   │   ├── LogTabs.tsx
│   │   │   ├── AdvancedFilters.tsx
│   │   │   └── EnhancedLogViewer.tsx
│   │   ├── pages/
│   │   │   └── GCPLogExplorer.tsx
│   │   ├── types/
│   │   │   └── gcp.ts
│   │   └── data/
│   │       └── gcpServices.ts
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── gcp_logs.py
│   │   └── services/
│   │       └── gcp_service.py
│   └── requirements.txt
└── docs/
    └── GCP_Log_Explorer_README.md
```

### Adding New Services

1. Add service definition to `gcpServices.ts`
2. Update backend mock data if needed
3. Test service selection and log retrieval
4. Add any service-specific filters

### Testing

```bash
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend
pytest tests/
```

## Performance Considerations

### Frontend Optimization

- **Virtualization**: Use React Window for large log lists
- **Debouncing**: Implement search debouncing to reduce API calls
- **Memoization**: Cache processed log data
- **Lazy Loading**: Load tabs and logs on demand

### Backend Optimization

- **Caching**: Redis for frequently accessed logs
- **Pagination**: Implement proper pagination for large datasets
- **Rate Limiting**: Prevent API abuse
- **Connection Pooling**: Efficient GCP API connections

## Security

### Authentication

- Google Cloud IAM integration
- Service account authentication
- Project-level access control

### Data Privacy

- Sensitive log data handling
- Audit trail for log access
- Secure credential management

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure proper GCP credentials
2. **API Quotas**: Monitor and adjust API usage limits
3. **Network Issues**: Check firewall and proxy settings
4. **Performance**: Optimize queries and implement caching

### Debug Mode

Enable debug logging:

```bash
# Backend
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# Frontend
npm run dev -- --debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

- Create an issue in the repository
- Check the troubleshooting section
- Review GCP documentation for API-specific issues
