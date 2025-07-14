import { useState, useEffect } from "react";
import { Search, RefreshCw, Download, Settings } from "lucide-react";
import { ProviderSelector } from "../components/ProviderSelector";
import { LogTabs } from "../components/LogTabs";
import { EnhancedLogViewer } from "../components/EnhancedLogViewer";
import { Chatbot } from "../components/Chatbot";
import ProviderFilters from "../components/Filters/ProviderFilters";
import CommonFilters from "../components/Filters/CommonFilters";
import { useAuth } from "../contexts/Auth";
import type {
  GCPService,
  LogTab,
  LogEntry,
  DeploymentInfo,
  FilterState,
} from "../types/gcp";
import type { CloudProvider } from "../types/providers";

export const Home = () => {
  const [selectedService, setSelectedService] = useState<
    GCPService | undefined
  >();
  const [selectedDeployment, setSelectedDeployment] = useState<
    DeploymentInfo | undefined
  >();
  const [tabs, setTabs] = useState<LogTab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string>("");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    severity: [],
    resourceType: "",
    logType: [],
    sourceLocation: "",
    userAccount: "",
    requestId: "",
    timeRange: "1h",
    customQuery: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [selectedProvider, setSelectedProvider] = useState<
    CloudProvider | undefined
  >();
  const { token } = useAuth();

  // Fetch projects on component mount
  useEffect(() => {
    fetchProjects();
  }, [token]);

  const fetchProjects = async () => {
    if (!token) return;

    try {
      const response = await fetch("/api/logs/projects", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProjects(data.projects || []);
        if (data.projects && data.projects.length > 0) {
          setSelectedProject(data.projects[0].project_id);
        }
      }
    } catch (error) {
      console.error("Error fetching projects:", error);
    }
  };

  // Create a new tab when service/deployment is selected
  useEffect(() => {
    if (selectedService) {
      const tabId = selectedDeployment
        ? `${selectedService.id}-${selectedDeployment.id}`
        : selectedService.id;

      const existingTab = tabs.find((tab) => tab.id === tabId);

      if (!existingTab) {
        const newTab: LogTab = {
          id: tabId,
          title: selectedService.name,
          serviceId: selectedService.id,
          deploymentId: selectedDeployment?.id,
          isActive: true,
          filters: { ...filters },
          query: "",
          lastUpdated: new Date(),
        };

        setTabs((prev) => [...prev, newTab]);
        setActiveTabId(tabId);
      } else {
        setActiveTabId(tabId);
      }
    }
  }, [selectedService, selectedDeployment]);

  // Update active tab when changed
  useEffect(() => {
    setTabs((prev) =>
      prev.map((tab) => ({
        ...tab,
        isActive: tab.id === activeTabId,
      }))
    );
  }, [activeTabId]);

  const handleTabSelect = (tabId: string) => {
    setActiveTabId(tabId);
  };

  const handleTabClose = (tabId: string) => {
    setTabs((prev) => prev.filter((tab) => tab.id !== tabId));

    // If closing active tab, switch to another tab
    if (tabId === activeTabId) {
      const remainingTabs = tabs.filter((tab) => tab.id !== tabId);
      if (remainingTabs.length > 0) {
        setActiveTabId(remainingTabs[0].id);
      } else {
        setActiveTabId("");
        setSelectedService(undefined);
        setSelectedDeployment(undefined);
      }
    }
  };

  const handleServiceSelect = (service: GCPService) => {
    setSelectedService(service);
    if (!service.isDeploymentBased) {
      setSelectedDeployment(undefined);
    }
  };

  const handleDeploymentSelect = (deployment: DeploymentInfo) => {
    setSelectedDeployment(deployment);
  };

  const handleProviderSelect = (provider: CloudProvider) => {
    setSelectedProvider(provider);
    // Reset service-specific selections when provider changes
    setSelectedService(undefined);
    setSelectedDeployment(undefined);
    // Keep tabs, search, and filters independent of provider
  };

  const handleFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters);
    // Update active tab's filters
    if (activeTabId) {
      setTabs((prev) =>
        prev.map((tab) =>
          tab.id === activeTabId ? { ...tab, filters: newFilters } : tab
        )
      );
    }
  };

  const handleSearch = async () => {
    if (!selectedProject || !selectedService) return;

    setIsLoading(true);
    try {
      // Build filter string for GCP Logging API
      let filterStr = `resource.type="${selectedService.id}"`;

      if (selectedDeployment) {
        filterStr += ` AND resource.labels.deployment_id="${selectedDeployment.id}"`;
      }

      if (filters.severity.length > 0) {
        const severityFilter = filters.severity
          .map((s) => `severity="${s}"`)
          .join(" OR ");
        filterStr += ` AND (${severityFilter})`;
      }

      if (filters.resourceType) {
        filterStr += ` AND resource.type="${filters.resourceType}"`;
      }

      if (searchQuery) {
        filterStr += ` AND textPayload:"${searchQuery}"`;
      }

      if (filters.customQuery) {
        filterStr += ` AND ${filters.customQuery}`;
      }

      const response = await fetch("/api/logs/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          project_id: selectedProject,
          filter: filterStr,
          page_size: 100,
          order_by: "timestamp desc",
        }),
      });

      if (response.ok) {
        const data = await response.json();
        // Convert the API response to our LogEntry format
        const convertedLogs = data.logs.map((log: any) => ({
          id: log.insertId || Math.random().toString(),
          timestamp: new Date(log.timestamp),
          severity: log.severity,
          message: log.message,
          resource: {
            type: log.resource_type,
            labels: log.resource_labels || {},
          },
          labels: log.labels || {},
          jsonPayload: log.jsonPayload,
          textPayload: log.textPayload,
          httpRequest: log.httpRequest,
          traceId: log.traceId,
          spanId: log.spanId,
        }));

        setLogs(convertedLogs);
      }
    } catch (error) {
      console.error("Error fetching logs:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = () => {
    handleSearch();
  };

  const handleExport = () => {
    const dataStr = JSON.stringify(logs, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `gcp-logs-${new Date().toISOString()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-gray-950 min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-800/50 sticky top-0 z-50">
        <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16 py-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Wassup?
              </h1>
              <div className="hidden md:block h-6 w-px bg-gray-700"></div>
              <div className="hidden md:block">
                <span className="text-sm text-gray-400">
                  Exploring the logs. Wanna join?
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-300">
                  Cloud Provider
                </label>
                <ProviderSelector
                  selectedProvider={selectedProvider}
                  onProviderSelect={handleProviderSelect}
                  className="w-94"
                />
              </div>

              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-300 bg-gray-800/50 border border-gray-700 rounded-lg hover:bg-gray-700/50 hover:text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw
                  className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
                />
                Refresh
              </button>
              <button
                onClick={handleExport}
                disabled={logs.length === 0}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>

              <button className="inline-flex items-center p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-all duration-200">
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Provider-specific filters */}
      <ProviderFilters
        selectedProvider={selectedProvider}
        selectedProject={selectedProject}
        setSelectedProject={setSelectedProject}
        projects={projects}
        selectedService={selectedService}
        onServiceSelect={handleServiceSelect}
        selectedDeployment={selectedDeployment}
        onDeploymentSelect={handleDeploymentSelect}
      />

      {/* Common filters - independent of provider */}
      <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16 py-4">
        <CommonFilters
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          showAdvancedFilters={showAdvancedFilters}
          setShowAdvancedFilters={setShowAdvancedFilters}
          filters={filters}
          onFiltersChange={handleFiltersChange}
          handleSearch={handleSearch}
          isLoading={isLoading}
          disabled={
            !selectedProvider ||
            (selectedProvider.id === "gcp" &&
              (!selectedProject || !selectedService))
          }
        />
      </div>

      {/* Tabs */}
      {tabs.length > 0 && (
        <div className="bg-gray-900/20 border-b border-gray-800/50">
          <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16">
            <LogTabs
              tabs={tabs}
              activeTabId={activeTabId}
              onTabSelect={handleTabSelect}
              onTabClose={handleTabClose}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 w-full px-4 sm:px-6 lg:px-8 xl:px-12 2xl:px-16 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-20 xl:grid-cols-20 2xl:grid-cols-20 gap-6 xl:gap-8 2xl:gap-12 h-full">
          {/* Logs Section */}
          <div className="lg:col-span-13 xl:col-span-13 2xl:col-span-13 space-y-4 xl:space-y-6">
            {/* Logs Viewer Card */}
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl shadow-lg overflow-hidden">
              <div className="px-6 py-4 xl:px-8 xl:py-6 border-b border-gray-800/50 bg-gray-900/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3 xl:space-x-4">
                    <h3 className="text-lg xl:text-xl font-semibold text-white">
                      Log Entries
                    </h3>
                    {logs.length > 0 && (
                      <span className="inline-flex items-center px-2.5 py-0.5 xl:px-3 xl:py-1 rounded-full text-xs xl:text-sm font-medium bg-blue-900/20 text-blue-400 border border-blue-800">
                        {logs.length} entries
                      </span>
                    )}
                  </div>

                  {isLoading && (
                    <div className="flex items-center space-x-2 xl:space-x-3 text-gray-400">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span className="text-sm xl:text-base">
                        Loading logs...
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="relative">
                {logs.length === 0 && !isLoading ? (
                  <div className="flex flex-col items-center justify-center py-12 xl:py-16 px-6 xl:px-8">
                    <div className="w-16 h-16 xl:w-20 xl:h-20 bg-gray-800 rounded-full flex items-center justify-center mb-4 xl:mb-6">
                      <Search className="w-8 h-8 xl:w-10 xl:h-10 text-gray-400" />
                    </div>
                    <h3 className="text-lg xl:text-xl font-medium text-gray-300 mb-2 xl:mb-3">
                      No logs found
                    </h3>
                    <p className="text-gray-500 text-center max-w-md xl:max-w-lg xl:text-lg">
                      {!selectedProject || !selectedService
                        ? "Select a project and service to start exploring logs"
                        : "Try adjusting your search query or filters to find relevant logs"}
                    </p>
                  </div>
                ) : (
                  <div className="max-h-[calc(100vh-400px)] xl:max-h-[calc(100vh-350px)] overflow-y-auto">
                    <EnhancedLogViewer logs={logs} />
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Chatbot Section */}
          <div className="lg:col-span-7 xl:col-span-7 2xl:col-span-7">
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl shadow-lg overflow-hidden h-[calc(100vh-300px)] xl:h-[calc(100vh-280px)] sticky top-24">
              <div className="px-4 xl:px-6 py-3 xl:py-4 border-b border-gray-800/50 bg-gray-900/30">
                <h3 className="text-sm xl:text-base font-semibold text-white">
                  AI Assistant
                </h3>
              </div>
              <div className="h-full">
                <Chatbot selectedServices={[]} />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Home;
