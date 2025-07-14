import { useState, useEffect } from "react";
import { ChevronDown, Loader2, Server } from "lucide-react";
import type { GCPService, DeploymentInfo } from "../types/gcp";
import { useAuth } from "../contexts/Auth";
import axios from "axios";

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
  const { token } = useAuth();

  useEffect(() => {
    if (service.isDeploymentBased && projectId) {
      fetchDeployments();
    }
  }, [service.id, service.isDeploymentBased, projectId, token]);

  const fetchDeployments = async () => {
    if (!projectId || !token) return;

    setLoading(true);
    try {
      // Use the existing logs API to get deployments for the service
      const response = await axios.post("/api/logs/query", {
        project_id: projectId,
        filter: `resource.type="${service.id}"`,
        page_size: 100,
        order_by: "timestamp desc",
      });

      if (response.data && response.data.logs) {
        // Extract unique deployments from the logs
        const deploymentMap = new Map<string, DeploymentInfo>();

        response.data.logs.forEach((log: any) => {
          if (log.resource_labels) {
            // Extract deployment info based on service type
            let deploymentId = "";
            let deploymentName = "";
            let deploymentType = "";

            switch (service.id) {
              case "cloud_run_revision":
                deploymentId =
                  log.resource_labels.service_name ||
                  log.resource_labels.revision_name ||
                  "";
                deploymentName =
                  log.resource_labels.service_name || "Unknown Service";
                deploymentType = "service";
                break;
              case "k8s_container":
                deploymentId =
                  log.resource_labels.cluster_name ||
                  log.resource_labels.namespace_name ||
                  "";
                deploymentName =
                  log.resource_labels.cluster_name ||
                  log.resource_labels.namespace_name ||
                  "Unknown Cluster";
                deploymentType = "cluster";
                break;
              case "gce_instance":
                deploymentId =
                  log.resource_labels.instance_id ||
                  log.resource_labels.instance_name ||
                  "";
                deploymentName =
                  log.resource_labels.instance_name ||
                  log.resource_labels.instance_id ||
                  "Unknown Instance";
                deploymentType = "instance";
                break;
              case "gae_app":
                deploymentId =
                  log.resource_labels.service_id ||
                  log.resource_labels.version_id ||
                  "";
                deploymentName =
                  log.resource_labels.service_id ||
                  log.resource_labels.version_id ||
                  "Unknown Service";
                deploymentType = "application";
                break;
              case "cloud_function":
                deploymentId = log.resource_labels.function_name || "";
                deploymentName =
                  log.resource_labels.function_name || "Unknown Function";
                deploymentType = "function";
                break;
              default:
                deploymentId =
                  log.resource_labels.deployment_id ||
                  log.resource_labels.name ||
                  "";
                deploymentName =
                  log.resource_labels.name ||
                  log.resource_labels.deployment_id ||
                  "Unknown Deployment";
                deploymentType = "deployment";
            }

            if (deploymentId) {
              deploymentMap.set(deploymentId, {
                id: deploymentId,
                name: deploymentName,
                type: deploymentType,
                status: "RUNNING", // Default status since we can't determine from logs
                region:
                  log.resource_labels.region || log.resource_labels.zone || "",
                zone: log.resource_labels.zone || "",
                namespace: log.resource_labels.namespace_name || "",
                service: log.resource_labels.service_name || "",
              });
            }
          }
        });

        setDeployments(Array.from(deploymentMap.values()));
      }
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
                <div className="font-medium">{selectedDeployment.name}</div>
                <div className="text-sm text-gray-400">
                  {selectedDeployment.type} • {selectedDeployment.status}
                  {selectedDeployment.region &&
                    ` • ${selectedDeployment.region}`}
                  {selectedDeployment.zone && ` • ${selectedDeployment.zone}`}
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
                    <div className="font-medium">{deployment.name}</div>
                    <div className="text-sm text-gray-400">
                      {deployment.type} • {deployment.status}
                      {deployment.region && ` • ${deployment.region}`}
                      {deployment.zone && ` • ${deployment.zone}`}
                    </div>
                  </div>
                  <div
                    className={`w-2 h-2 rounded-full ${
                      deployment.status === "RUNNING" ||
                      deployment.status === "ACTIVE"
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
