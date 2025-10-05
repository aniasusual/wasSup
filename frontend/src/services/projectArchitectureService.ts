import { useAuth } from '../contexts/Auth';
import axios from 'axios';

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
    try {
      const response = await axios.post('/api/v1/project-architecture/', data, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to create/update project architecture';
      throw new Error(errorMessage);
    }
  };

  const getArchitectureByProject = async (projectId: string): Promise<ProjectArchitecture | null> => {
    try {
      const response = await axios.get(`/api/v1/project-architecture/project/${projectId}`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      const errorMessage = error.response?.data?.detail || 'Failed to get project architecture';
      throw new Error(errorMessage);
    }
  };

  const updateArchitecture = async (projectId: string, data: ProjectArchitectureUpdate): Promise<ProjectArchitecture> => {
    try {
      const response = await axios.put(`/api/v1/project-architecture/project/${projectId}`, data, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to update project architecture';
      throw new Error(errorMessage);
    }
  };

  const deleteArchitecture = async (projectId: string): Promise<void> => {
    try {
      await axios.delete(`/api/v1/project-architecture/project/${projectId}`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to delete project architecture';
      throw new Error(errorMessage);
    }
  };

  return {
    createOrUpdateArchitecture,
    getArchitectureByProject,
    updateArchitecture,
    deleteArchitecture,
  };
};
