# Frontend - GCP Log Explorer

A modern React frontend for the GCP Log Explorer system, built with TypeScript, Vite, and Tailwind CSS.

## Features

- **Modern UI**: Built with React 19, TypeScript, and Tailwind CSS
- **Real-time Log Streaming**: Live updates for log analysis
- **Advanced Log Viewer**: Comprehensive log analysis and filtering interface
- **Multi-tab Interface**: Organize multiple log queries simultaneously
- **Project Architecture**: Visualize and manage GCP project architecture
- **Authentication**: Secure OAuth2 integration with Google
- **Responsive Design**: Works seamlessly on desktop and mobile

## Tech Stack

- **React 19** - Modern React with latest features
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Query** - Data fetching and caching
- **React Router** - Client-side routing
- **React Hot Toast** - Beautiful notifications
- **Lucide React** - Icon library
- **React Markdown** - Markdown rendering
- **React Syntax Highlighter** - Code syntax highlighting

## Project Structure

```
frontend/src/
├── components/           # Reusable UI components
│   │   ├── EmptyState.tsx
│   │   ├── MessageAnalysis.tsx
│   │   ├── ProperMarkdownRenderer.tsx
│   │   └── UserMessage.tsx
│   ├── Filters/         # Filter components
│   │   ├── GcpFilters.tsx
│   │   └── ProviderFilters.tsx
│   ├── AuthSuccess.tsx
│   ├── DateTimeSearchBar.tsx
│   ├── EnhancedLogViewer.tsx
│   ├── GCPProjectSelector.tsx
│   ├── GCPQueryBuilder.tsx
│   ├── GCPServiceSelector.tsx
│   ├── JsonViewer.tsx
│   ├── LogEntry.tsx
│   ├── Login.tsx
│   ├── LogTabs.tsx
│   ├── ProjectArchitecturePrompt.tsx
│   └── ProviderSelector.tsx
├── contexts/            # React contexts
│   └── Auth.tsx
├── data/               # Static data and mappings
│   └── gcpResourceMappings.ts
├── pages/              # Page components
│   └── Home.tsx
├── services/           # API services
│   ├── logService.ts
│   └── projectArchitectureService.ts
├── types/              # TypeScript type definitions
│   ├── gcp.ts
│   └── providers.ts
├── utils/              # Utility functions
│   └── errorUtils.ts
├── App.tsx             # Main app component
├── App.css             # Global styles
├── index.css           # CSS entry point
└── main.tsx            # App entry point
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

### Lint

```bash
npm run lint
```

## Key Components

### Log Analysis System
- **Real-time Streaming**: Live log updates with efficient filtering
- **Advanced Filtering**: Comprehensive filter options for log analysis
- **Multi-tab Support**: Organize multiple log queries simultaneously

### Log Management
- **Multi-tab Interface**: Organize multiple log queries
- **Real-time Updates**: Live streaming of log entries
- **Advanced Filtering**: Complex query building with GCP filters
- **Time Range Selection**: Interactive time range picker

### Project Architecture
- **Visual Architecture**: Store and visualize GCP project architecture
- **Service Discovery**: Automatic discovery of GCP services
- **Architecture Analysis**: AI-powered architecture insights

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_FRONTEND_URL=http://localhost:5173
```

## API Integration

The frontend communicates with the backend API through:

- **Authentication**: OAuth2 flow with Google
- **Log Services**: Real-time log fetching and analysis
- **Project Architecture**: Architecture management and analysis
- **Real-time Updates**: Live streaming for log analysis