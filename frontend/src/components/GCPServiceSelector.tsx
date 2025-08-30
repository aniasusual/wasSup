import { useState } from "react";
import { ChevronDown, Search, Plus } from "lucide-react";
import { GCP_RESOURCE_MAPPINGS } from "../data/gcpResourceMappings";

// Helper: Map service ids to categories based on the order in GCP_RESOURCE_MAPPINGS
const CATEGORY_MAP: Record<string, string> = {
  // Compute
  cloud_run_revision: "compute",
  k8s_container: "compute",
  k8s_cluster: "compute",
  k8s_node: "compute",
  k8s_pod: "compute",
  gce_instance: "compute",
  cloud_function: "compute",
  gae_app: "compute",
  // Storage
  cloudsql_database: "storage",
  gcs_bucket: "storage",
  bigtable_instance: "storage",
  datastore_database: "storage",
  spanner_instance: "storage",
  firestore_database: "storage",
  // Networking
  vpc_flow_log: "networking",
  gce_network: "networking",
  gce_subnetwork: "networking",
  vpn_gateway: "networking",
  http_load_balancer: "networking",
  tcp_ssl_proxy_load_balancer: "networking",
  internal_http_load_balancer: "networking",
  network_load_balancer: "networking",
  // Data & Analytics
  bigquery_dataset: "data-analytics",
  bigquery_project: "data-analytics",
  dataflow_job: "data-analytics",
  dataproc_cluster: "data-analytics",
  pubsub_topic: "data-analytics",
  pubsub_subscription: "data-analytics",
  // AI/ML
  ml_job: "ai-ml",
  aiplatform_training_job: "ai-ml",
  aiplatform_endpoint: "ai-ml",
  // API & Developer
  api_gateway: "api-dev",
  cloud_endpoints_service: "api-dev",
  cloud_build: "api-dev",
  cloud_source_repo: "api-dev",
  // Monitoring & Operations
  uptime_url: "monitoring",
  logging_sink: "monitoring",
  // Security & Identity
  service_account: "security",
  // Scheduler & Tasks
  cloud_scheduler_job: "scheduler",
  cloud_tasks_queue: "scheduler",
  // Cache
  redis_instance: "cache",
  memcache_instance: "cache",
  // Other
  cloud_composer_environment: "other",
  datastream_stream: "other",
  cloud_dns_zone: "other",
  certificate_manager: "other",
  // Global/Generic
  global: "other",
  project: "other",
};

function humanizeServiceName(id: string) {
  return id
    .replace(/_/g, " ")
    .replace(/\b\w/g, (l) => l.toUpperCase())
    .replace(/\b([a-z])/g, (l) => l.toUpperCase())
    .replace(/\bGcp\b/i, "GCP")
    .replace(/\bApi\b/i, "API")
    .replace(/\bMl\b/i, "ML")
    .replace(/\bAi\b/i, "AI")
    .replace(/\bId\b/i, "ID")
    .replace(/\bDns\b/i, "DNS")
    .replace(/\bSql\b/i, "SQL")
    .replace(/\bVpc\b/i, "VPC")
    .replace(/\bK8s\b/i, "K8s")
    .replace(/\bGce\b/i, "GCE")
    .replace(/\bGcs\b/i, "GCS")
    .replace(/\bGae\b/i, "GAE")
    .replace(/\bIam\b/i, "IAM");
}

const getServices = () => {
  return Object.keys(GCP_RESOURCE_MAPPINGS).map((id) => ({
    id,
    name: humanizeServiceName(id),
    category: CATEGORY_MAP[id] || "other",
  }));
};

const getServicesByCategory = () => {
  const services = getServices();
  return services.reduce((acc, service) => {
    if (!acc[service.category]) acc[service.category] = [];
    acc[service.category].push(service);
    return acc;
  }, {} as Record<string, { id: string; name: string; category: string }[]>);
};

interface GCPServiceSelectorProps {
  selectedService?: { id: string; name: string; category: string };
  onServiceSelect: (service: {
    id: string;
    name: string;
    category: string;
  }) => void;
  className?: string;
}

export const GCPServiceSelector = ({
  selectedService,
  onServiceSelect,
  className = "",
}: GCPServiceSelectorProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const servicesByCategory = getServicesByCategory();
  const allServices = getServices();

  const filteredServices = allServices.filter(
    (service) =>
      service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      service.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleServiceSelect = (service: {
    id: string;
    name: string;
    category: string;
  }) => {
    onServiceSelect(service);
    setIsOpen(false);
    setSearchQuery("");
  };

  const handleProjectLogsSelect = () => {
    // Create a special service object for project-wide logs
    const projectLogsService = {
      id: "project_logs",
      name: "Project Logs",
      category: "all" as any,
    };
    onServiceSelect(projectLogsService);
    setIsOpen(false);
    setSearchQuery("");
  };

  return (
    <div className={`relative ${className}`}>
      {/* Selected Service Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-gradient-to-r from-gray-800 to-gray-900 border border-gray-700/50 rounded-xl text-white hover:bg-gradient-to-r hover:from-gray-700 hover:to-gray-800 transition-all duration-300 shadow-sm"
      >
        <div className="flex items-center gap-4">
          {selectedService ? (
            <>
              <div className="text-left">
                <div className="font-semibold text-base">
                  {selectedService.name}
                </div>
                <div className="text-xs text-gray-300 capitalize mt-0.5">
                  {selectedService.category === "all"
                    ? "All Services"
                    : selectedService.category}
                </div>
              </div>
            </>
          ) : (
            <span className="text-gray-300 font-medium">
              Select a GCP Service
            </span>
          )}
        </div>
        <ChevronDown
          className={`w-5 h-5 text-gray-300 transition-transform duration-300 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-gray-900 border border-gray-700/50 rounded-xl shadow-2xl z-50 max-h-[32rem] overflow-hidden">
          {/* Search */}
          <div className="p-4 border-b border-gray-700/50">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search services..."
                className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 text-sm font-medium"
              />
            </div>
          </div>

          {/* Project Logs Option - Always visible at top */}
          <div className="p-2 border-b border-gray-700/50">
            <button
              onClick={handleProjectLogsSelect}
              className="w-full flex items-center gap-3 p-3 text-left text-white hover:bg-blue-600/20 rounded-lg transition-all duration-200 border border-blue-600/30 hover:border-blue-500/50 group"
              title="View all logs across all GCP services in this project"
            >
              <div className="w-8 h-8 bg-blue-600/20 rounded-lg flex items-center justify-center group-hover:bg-blue-600/30 transition-colors">
                <span className="text-blue-400 text-lg">☁️</span>
              </div>
              <div className="flex-1">
                <div className="font-semibold text-sm text-blue-300 group-hover:text-blue-200 transition-colors">
                  Project Logs
                </div>
                <div className="text-xs text-blue-400/70 group-hover:text-blue-300/80 mt-0.5 transition-colors">
                  View all logs across all services
                </div>
              </div>
              <div className="text-xs text-blue-400/50 group-hover:text-blue-300/60">
                All Services
              </div>
            </button>
          </div>

          {/* Service List */}
          <div className="max-h-[28rem] overflow-y-auto custom-scrollbar">
            {searchQuery ? (
              // Search results
              <div className="p-2">
                {filteredServices.map((service) => (
                  <div
                    key={service.id}
                    className="flex items-center gap-2 px-2 py-1"
                  >
                    <button
                      onClick={() => handleServiceSelect(service)}
                      className="flex-1 flex items-center gap-3 p-3 text-left text-white hover:bg-gray-800/50 rounded-lg transition-all duration-200"
                    >
                      <div className="flex-1">
                        <div className="font-semibold text-sm">
                          {service.name}
                        </div>
                        <div className="text-xs text-gray-300 capitalize mt-0.5">
                          {service.category}
                        </div>
                      </div>
                    </button>
                    <button
                      onClick={() => handleServiceSelect(service)}
                      className="p-2 text-gray-400 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all duration-200"
                      title={`Select ${service.name}`}
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              // Categorized services
              Object.entries(servicesByCategory).map(([category, services]) => (
                <div key={category} className="p-2">
                  <div className="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-700/30 mb-2">
                    {category.replace(/-/g, " ")}
                  </div>
                  {services.map((service) => (
                    <div
                      key={service.id}
                      className="flex items-center gap-2 px-2 py-1"
                    >
                      <button
                        onClick={() => handleServiceSelect(service)}
                        className="flex-1 flex items-center gap-3 p-3 text-left text-white hover:bg-gray-800/50 rounded-lg transition-all duration-200"
                      >
                        <div className="flex-1">
                          <div className="font-semibold text-sm">
                            {service.name}
                          </div>
                          <div className="text-xs text-gray-300 capitalize mt-0.5">
                            {service.category}
                          </div>
                        </div>
                      </button>
                      <button
                        onClick={() => handleServiceSelect(service)}
                        className="p-2 text-gray-400 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all duration-200"
                        title={`Select ${service.name}`}
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
