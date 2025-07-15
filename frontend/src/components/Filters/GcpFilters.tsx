import React from "react";
import { GCPServiceSelector } from "../GCPServiceSelector";
import { GCPProjectSelector } from "../GCPProjectSelector";
import { DeploymentSelector } from "../DeploymentSelector";
// import type { GCPService, DeploymentInfo } from "../../types/gcp";

// interface GcpFiltersProps {
//   selectedProject: string;
//   setSelectedProject: (project: string) => void;
//   projects: any[];
//   selectedService: GCPService | undefined;
//   onServiceSelect: (service: GCPService) => void;
//   selectedDeployment: DeploymentInfo | undefined;
//   onDeploymentSelect: (deployment: DeploymentInfo) => void;
// }

const GcpFilters: React.FC<any> = ({
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
        <div className="w-full px-3 sm:px-4 md:px-6 lg:px-8 xl:px-12 2xl:px-16 py-3 sm:py-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3 sm:gap-4 xl:gap-6">
            <div className="space-y-2">
              <label className="block text-xs sm:text-sm font-medium text-gray-300">
                GCP Project
              </label>
              <GCPProjectSelector
                selectedProject={selectedProject}
                onProjectSelect={setSelectedProject}
                projects={projects}
              />
            </div>

            <div className="space-y-2">
              <label className="block text-xs sm:text-sm font-medium text-gray-300">
                GCP Service
              </label>
              <GCPServiceSelector
                selectedService={selectedService}
                onServiceSelect={onServiceSelect}
              />
            </div>

            {selectedService?.isDeploymentBased && (
              <div className="space-y-2">
                <label className="block text-xs sm:text-sm font-medium text-gray-300">
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
