# Project Architecture Feature Demo

## Overview
The Project Architecture feature allows users to define and store comprehensive project architecture descriptions for each GCP project. This information is then used to provide better context for log analysis and AI insights.

## Features Implemented

### Backend (MongoDB + FastAPI)
1. **MongoDB Integration**
   - Connection to MongoDB Atlas cluster
   - Database: `recce`
   - Collection: `project_architectures`

2. **API Endpoints**
   - `POST /api/v1/project-architecture/` - Create/Update project architecture
   - `GET /api/v1/project-architecture/project/{project_id}` - Get architecture by project
   - `PUT /api/v1/project-architecture/project/{project_id}` - Update architecture
   - `DELETE /api/v1/project-architecture/project/{project_id}` - Delete architecture
   - `GET /api/v1/project-architecture/` - List all architectures

3. **Data Model**
   ```python
   {
     "id": "ObjectId",
     "project_id": "gcp-project-id",
     "architecture_prompt": "Complete project architecture description",
     "created_by": "user@example.com",
     "is_active": true,
     "created_at": "2024-01-01T00:00:00Z",
     "updated_at": "2024-01-01T00:00:00Z"
   }
   ```

### Frontend (React + TypeScript)
1. **ProjectArchitecturePrompt Component**
   - Modern, responsive design with dark theme
   - Auto-loads existing architecture when project is selected
   - Edit mode with save/cancel functionality
   - Real-time validation and change detection
   - Loading states and error handling

2. **Integration with Home Page**
   - Appears after project selection
   - Seamlessly integrated with existing UI
   - Passes architecture data to Chatbot component

3. **Service Layer**
   - `useProjectArchitectureService` hook
   - Full CRUD operations
   - Error handling and user feedback

## How It Works

1. **Project Selection**: When a user selects a GCP project, the architecture prompt component automatically loads
2. **Auto-Load**: If an architecture exists for the project, it's displayed in read-only mode
3. **Edit Mode**: Users can click "Edit" or "Add Architecture" to enter edit mode
4. **Save**: Changes are saved to MongoDB and the UI updates
5. **Context**: The architecture description is passed to the AI chatbot for better insights

## UI Features

- **Modern Design**: Glass-morphism effects, gradients, and smooth animations
- **Responsive**: Works on all screen sizes
- **Accessible**: Proper ARIA labels and keyboard navigation
- **User-Friendly**: Clear visual feedback and intuitive controls

## Database Schema

The architecture data is stored in MongoDB with the following structure:
- One architecture per project (upsert behavior)
- Automatic timestamps for created/updated
- User tracking for audit purposes
- Active/inactive status for future features

## Security

- All endpoints require authentication
- User context is tracked for audit purposes
- Input validation and sanitization
- MongoDB connection with proper error handling

## Next Steps

The architecture data can now be used by:
1. AI agents for better log analysis context
2. Query builders for smarter suggestions
3. Insight generation for more relevant recommendations
4. Documentation generation
5. Architecture compliance checking

## Testing

The backend is running on `http://localhost:8000` and all endpoints are functional. The frontend component is integrated and ready for use.
