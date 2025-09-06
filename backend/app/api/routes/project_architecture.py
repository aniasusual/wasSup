from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
from app.models.project_architecture import (
    ProjectArchitecture,
    ProjectArchitectureCreate,
    ProjectArchitectureUpdate
)
from app.services.project_architecture_service import project_architecture_service
from app.api.helpers.authHelper import get_current_user

router = APIRouter()

@router.post("/", response_model=ProjectArchitecture, status_code=status.HTTP_201_CREATED)
async def create_project_architecture(
    architecture_data: ProjectArchitectureCreate,
    current_user: str = Depends(get_current_user)
):
    """Create or update project architecture"""
    try:
        # Add the current user to the architecture data
        architecture_data.created_by = current_user
        
        architecture = await project_architecture_service.create_architecture(architecture_data)
        return architecture
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project architecture: {str(e)}"
        )

@router.get("/project/{project_id}", response_model=Optional[ProjectArchitecture])
async def get_project_architecture(
    project_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get project architecture by project ID"""
    try:
        architecture = await project_architecture_service.get_architecture_by_project(project_id)
        return architecture
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project architecture: {str(e)}"
        )

@router.put("/project/{project_id}", response_model=Optional[ProjectArchitecture])
async def update_project_architecture(
    project_id: str,
    update_data: ProjectArchitectureUpdate,
    current_user: str = Depends(get_current_user)
):
    """Update project architecture"""
    try:
        architecture = await project_architecture_service.update_architecture(project_id, update_data)
        if not architecture:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project architecture not found"
            )
        return architecture
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project architecture: {str(e)}"
        )

@router.delete("/project/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_architecture(
    project_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete project architecture"""
    try:
        success = await project_architecture_service.delete_architecture(project_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project architecture not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project architecture: {str(e)}"
        )

@router.get("/", response_model=list[ProjectArchitecture])
async def list_project_architectures(
    skip: int = 0,
    limit: int = 100,
    current_user: str = Depends(get_current_user)
):
    """List all project architectures"""
    try:
        architectures = await project_architecture_service.list_architectures(skip, limit)
        return architectures
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list project architectures: {str(e)}"
        )
