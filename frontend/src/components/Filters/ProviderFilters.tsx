import React from "react";
import GcpFilters from "./GcpFilters";
import type { CloudProvider } from "../../types/providers";
import type { GCPService, DeploymentInfo } from "../../types/gcp";

interface ProviderFiltersProps {
  selectedProvider: CloudProvider | undefined;
  // GCP specific props
  selectedProject: string;
  setSelectedProject: (project: string) => void;
  projects: any[];
  selectedService: GCPService | undefined;
  onServiceSelect: (service: GCPService) => void;
  selectedDeployment: DeploymentInfo | undefined;
  onDeploymentSelect: (deployment: DeploymentInfo) => void;
}

const ProviderFilters: React.FC<ProviderFiltersProps> = ({
  selectedProvider,
  selectedProject,
  setSelectedProject,
  projects,
  selectedService,
  onServiceSelect,
  selectedDeployment,
  onDeploymentSelect,
}) => {
  if (!selectedProvider) {
    return null;
  }

  // Render provider-specific filters based on the selected provider
  switch (selectedProvider.id) {
    case "gcp":
      return (
        <GcpFilters
          selectedProject={selectedProject}
          setSelectedProject={setSelectedProject}
          projects={projects}
          selectedService={selectedService}
          onServiceSelect={onServiceSelect}
          selectedDeployment={selectedDeployment}
          onDeploymentSelect={onDeploymentSelect}
        />
      );

    case "aws":
      return (
        <div className="bg-gray-900/30 border-b border-gray-800/50">
          <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16 py-4">
            <div className="text-center py-8">
              <div className="text-gray-400 text-lg font-medium mb-2">
                AWS Support Coming Soon
              </div>
              <p className="text-gray-500 text-sm">
                AWS CloudWatch integration will be available in a future update.
              </p>
            </div>
          </div>
        </div>
      );

    case "azure":
      return (
        <div className="bg-gray-900/30 border-b border-gray-800/50">
          <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16 py-4">
            <div className="text-center py-8">
              <div className="text-gray-400 text-lg font-medium mb-2">
                Azure Support Coming Soon
              </div>
              <p className="text-gray-500 text-sm">
                Azure Monitor integration will be available in a future update.
              </p>
            </div>
          </div>
        </div>
      );

    case "digitalocean":
      return (
        <div className="bg-gray-900/30 border-b border-gray-800/50">
          <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16 py-4">
            <div className="text-center py-8">
              <div className="text-gray-400 text-lg font-medium mb-2">
                DigitalOcean Support Coming Soon
              </div>
              <p className="text-gray-500 text-sm">
                DigitalOcean monitoring integration will be available in a
                future update.
              </p>
            </div>
          </div>
        </div>
      );

    case "heroku":
      return (
        <div className="bg-gray-900/30 border-b border-gray-800/50">
          <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16 py-4">
            <div className="text-center py-8">
              <div className="text-gray-400 text-lg font-medium mb-2">
                Heroku Support Coming Soon
              </div>
              <p className="text-gray-500 text-sm">
                Heroku logs integration will be available in a future update.
              </p>
            </div>
          </div>
        </div>
      );

    default:
      return null;
  }
};

export default ProviderFilters;
