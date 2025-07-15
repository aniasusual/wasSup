import { useState, useEffect } from "react";
import { ChevronDown, Loader2, Server } from "lucide-react";
import type { GCPService } from "../types/gcp";
import type { DeploymentInfo } from "../services/deploymentService";
import { useDeploymentService } from "../services/deploymentService";

interface DeploymentSelectorProps {
  service: GCPService;
  selectedDeployment?: DeploymentInfo;
  onDeploymentSelect: (deployment: DeploymentInfo) => void;
  className?: string;
  projectId?: string;
}

export const DeploymentSelector = ({
  service,
  selectedDeployment,
  onDeploymentSelect,
  className = "",
  projectId,
}: DeploymentSelectorProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [deployments, setDeployments] = useState<DeploymentInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const { fetchDeployments } = useDeploymentService();

  useEffect(() => {
    if (service.isDeploymentBased && projectId) {
      fetchDeploymentsForService();
    }
  }, [service.id, service.isDeploymentBased, projectId]);

  const fetchDeploymentsForService = async () => {
    if (!projectId) return;

    setLoading(true);
    try {
      const response = await fetchDeployments(projectId, service.id);
      setDeployments(response.deployments);
    } catch (error) {
      console.error("Error fetching deployments:", error);
      setDeployments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeploymentSelect = (deployment: DeploymentInfo) => {
    onDeploymentSelect(deployment);
    setIsOpen(false);
  };

  if (!service.isDeploymentBased) {
    return null;
  }

  return (
    <div className={`relative ${className}`}>
      {/* Selected Deployment Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-gray-800 border border-gray-700 rounded-lg text-white hover:bg-gray-700 transition-colors"
        disabled={loading}
      >
        <div className="flex items-center gap-3">
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
              <span className="text-gray-400">Loading deployments...</span>
            </>
          ) : selectedDeployment ? (
            <>
              <Server className="w-5 h-5 text-blue-500" />
              <div className="text-left">
                <div className="font-medium">
                  {selectedDeployment.display_name}
                </div>
                <div className="text-sm text-gray-400">
                  {selectedDeployment.type} • {selectedDeployment.status}
                  {selectedDeployment.region &&
                    ` • ${selectedDeployment.region}`}
                  {selectedDeployment.location &&
                    ` • ${selectedDeployment.location}`}
                </div>
              </div>
            </>
          ) : (
            <span className="text-gray-400">Select deployment</span>
          )}
        </div>
        {!loading && (
          <ChevronDown
            className={`w-5 h-5 text-gray-400 transition-transform ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        )}
      </button>

      {/* Dropdown */}
      {isOpen && !loading && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-gray-900 border border-gray-700 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
          <div className="p-2">
            {deployments.length > 0 ? (
              deployments.map((deployment) => (
                <button
                  key={deployment.id}
                  onClick={() => handleDeploymentSelect(deployment)}
                  className="w-full flex items-center gap-3 p-3 text-left text-white hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <Server className="w-5 h-5 text-blue-500" />
                  <div className="flex-1">
                    <div className="font-medium">{deployment.display_name}</div>
                    <div className="text-sm text-gray-400">
                      {deployment.type} • {deployment.status}
                      {deployment.region && ` • ${deployment.region}`}
                      {deployment.location && ` • ${deployment.location}`}
                    </div>
                  </div>
                  <div
                    className={`w-2 h-2 rounded-full ${
                      deployment.status === "RUNNING" ||
                      deployment.status === "ACTIVE" ||
                      deployment.status === "READY"
                        ? "bg-green-500"
                        : "bg-yellow-500"
                    }`}
                  />
                </button>
              ))
            ) : (
              <div className="p-3 text-gray-400 text-center">
                No deployments found
              </div>
            )}
          </div>
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
      )}
    </div>
  );
};
