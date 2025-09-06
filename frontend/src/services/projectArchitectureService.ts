import { useAuth } from '../contexts/Auth';

export interface ProjectArchitecture {
  id: string;
  project_id: string;
  architecture_prompt: string;
  created_by?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectArchitectureCreate {
  project_id: string;
  architecture_prompt: string;
  created_by?: string;
  is_active?: boolean;
}

export interface ProjectArchitectureUpdate {
  architecture_prompt?: string;
  is_active?: boolean;
}

export const useProjectArchitectureService = () => {
  const { token } = useAuth();

  const createOrUpdateArchitecture = async (data: ProjectArchitectureCreate): Promise<ProjectArchitecture> => {
    const response = await fetch('/api/v1/project-architecture/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to create/update project architecture');
    }

    return response.json();
  };

  const getArchitectureByProject = async (projectId: string): Promise<ProjectArchitecture | null> => {
    const response = await fetch(`/api/v1/project-architecture/project/${projectId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to get project architecture');
    }

    return response.json();
  };

  const updateArchitecture = async (projectId: string, data: ProjectArchitectureUpdate): Promise<ProjectArchitecture> => {
    const response = await fetch(`/api/v1/project-architecture/project/${projectId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to update project architecture');
    }

    return response.json();
  };

  const deleteArchitecture = async (projectId: string): Promise<void> => {
    const response = await fetch(`/api/v1/project-architecture/project/${projectId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to delete project architecture');
    }
  };

  return {
    createOrUpdateArchitecture,
    getArchitectureByProject,
    updateArchitecture,
    deleteArchitecture,
  };
};
