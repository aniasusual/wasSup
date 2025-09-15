import React, { useState, useEffect, useCallback } from 'react';
import { Save, Edit3, X, Building2, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { useProjectArchitectureService, type ProjectArchitecture } from '../services/projectArchitectureService';
import toast from 'react-hot-toast';

interface ProjectArchitecturePromptProps {
  projectId: string;
  onArchitectureChange?: (architecture: string) => void;
  className?: string;
}

export const ProjectArchitecturePrompt: React.FC<ProjectArchitecturePromptProps> = ({
  projectId,
  onArchitectureChange,
  className = '',
}) => {
  const [architecture, setArchitecture] = useState<ProjectArchitecture | null>(null);
  const [prompt, setPrompt] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const { getArchitectureByProject, createOrUpdateArchitecture } = useProjectArchitectureService();

  // Load architecture when project changes
  useEffect(() => {
    if (projectId) {
      loadArchitecture();
    } else {
      setArchitecture(null);
      setPrompt('');
      setIsEditing(false);
    }
  }, [projectId]);

  // Check for changes
  useEffect(() => {
    if (architecture) {
      setHasChanges(prompt !== architecture.architecture_prompt);
    } else {
      setHasChanges(prompt.trim().length > 0);
    }
  }, [prompt, architecture]);

  const loadArchitecture = useCallback(async () => {
    if (!projectId) return;

    setIsLoading(true);
    try {
      const arch = await getArchitectureByProject(projectId);
      if (arch) {
        setArchitecture(arch);
        setPrompt(arch.architecture_prompt);
        onArchitectureChange?.(arch.architecture_prompt);
      } else {
        setArchitecture(null);
        setPrompt('');
        setIsEditing(true); // Start editing if no architecture exists
      }
    } catch (error) {
      toast.error('Failed to load project architecture');
    } finally {
      setIsLoading(false);
    }
  }, [projectId, getArchitectureByProject, onArchitectureChange]);

  const handleSave = async () => {
    if (!projectId || !prompt.trim()) {
      toast.error('Please enter a project architecture description');
      return;
    }

    setIsSaving(true);
    try {
      const arch = await createOrUpdateArchitecture({
        project_id: projectId,
        architecture_prompt: prompt.trim(),
        is_active: true,
      });

      setArchitecture(arch);
      setIsEditing(false);
      setHasChanges(false);
      onArchitectureChange?.(arch.architecture_prompt);
      toast.success('Project architecture saved successfully');
    } catch (error) {
      toast.error('Failed to save project architecture');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    if (architecture) {
      setPrompt(architecture.architecture_prompt);
      setIsEditing(false);
    } else {
      setPrompt('');
    }
    setHasChanges(false);
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  if (isLoading) {
    return (
      <div className={`bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6 ${className}`}>
        <div className="flex items-center justify-center space-x-2">
          <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
          <span className="text-gray-400">Loading project architecture...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl shadow-lg ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-900/20 rounded-lg">
              <Building2 className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Project Architecture</h3>
              <p className="text-sm text-gray-400">
                {architecture ? 'Define your project architecture' : 'No architecture defined yet'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {!isEditing ? (
              <>
                <button
                  onClick={handleEdit}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-300 bg-gray-800/50 border border-gray-700 rounded-lg hover:bg-gray-700/50 hover:text-white transition-all duration-200"
                >
                  <Edit3 className="w-4 h-4 mr-2" />
                  {architecture ? 'Edit' : 'Add Architecture'}
                </button>
                <button
                  onClick={() => setIsCollapsed(!isCollapsed)}
                  className="inline-flex items-center p-2 text-gray-400 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all duration-200"
                  title={isCollapsed ? 'Expand' : 'Collapse'}
                >
                  {isCollapsed ? (
                    <ChevronDown className="w-4 h-4" />
                  ) : (
                    <ChevronUp className="w-4 h-4" />
                  )}
                </button>
              </>
            ) : (
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleCancel}
                  disabled={isSaving}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-300 bg-gray-800/50 border border-gray-700 rounded-lg hover:bg-gray-700/50 hover:text-white transition-all duration-200 disabled:opacity-50"
                >
                  <X className="w-4 h-4 mr-2" />
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={!hasChanges || isSaving || !prompt.trim()}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSaving ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <div className="p-6">
          {isEditing ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Architecture Description
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe your complete project architecture including services, components, data flow, infrastructure, and any other relevant details..."
                  className="w-full h-48 px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  disabled={isSaving}
                />
                <p className="mt-2 text-xs text-gray-500">
                  Provide a comprehensive description of your project architecture to help with log analysis and insights.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {architecture ? (
                <div className="prose prose-invert max-w-none">
                  <div className="bg-gray-800/30 rounded-lg p-4 border border-gray-700/50">
                    <pre className="whitespace-pre-wrap text-sm text-gray-300 font-mono leading-relaxed">
                      {architecture.architecture_prompt}
                    </pre>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Last updated: {new Date(architecture.updated_at).toLocaleString()}</span>
                    {architecture.created_by && (
                      <span>Created by: {architecture.created_by}</span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Building2 className="w-8 h-8 text-gray-400" />
                  </div>
                  <h4 className="text-lg font-medium text-gray-300 mb-2">No Architecture Defined</h4>
                  <p className="text-gray-500 mb-4">
                    Define your project architecture to get better insights and analysis.
                  </p>
                  <button
                    onClick={handleEdit}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 transition-all duration-200"
                  >
                    <Building2 className="w-4 h-4 mr-2" />
                    Add Architecture
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProjectArchitecturePrompt;
