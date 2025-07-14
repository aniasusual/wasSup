import React from "react";
import { GCPServiceSelector } from "../GCPServiceSelector";
import { DeploymentSelector } from "../DeploymentSelector";
import type { GCPService, DeploymentInfo } from "../../types/gcp";

interface GcpFiltersProps {
  selectedProject: string;
  setSelectedProject: (project: string) => void;
  projects: any[];
  selectedService: GCPService | undefined;
  onServiceSelect: (service: GCPService) => void;
  selectedDeployment: DeploymentInfo | undefined;
  onDeploymentSelect: (deployment: DeploymentInfo) => void;
}

const GcpFilters: React.FC<GcpFiltersProps> = ({
  selectedProject,
  setSelectedProject,
  projects,
  selectedService,
  onServiceSelect,
  selectedDeployment,
  onDeploymentSelect,
}) => {
  return (
    <div>
      {/* Project and Service Selection */}
      <div className="bg-gray-900/30 border-b border-gray-800/50">
        <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16 py-4">
          <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 xl:gap-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">
                GCP Project
              </label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full px-3 py-2.5 bg-gray-800/50 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <option value="">Select a project</option>
                {projects.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.name} ({project.project_id})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">
                GCP Service
              </label>
              <GCPServiceSelector
                selectedService={selectedService}
                onServiceSelect={onServiceSelect}
              />
            </div>

            {selectedService?.isDeploymentBased && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">
                  Deployment
                </label>
                <DeploymentSelector
                  service={selectedService}
                  selectedDeployment={selectedDeployment}
                  onDeploymentSelect={onDeploymentSelect}
                  projectId={selectedProject}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GcpFilters;
