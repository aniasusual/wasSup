import { useState, useEffect } from "react";
import { Search, RefreshCw, Download, Settings, X } from "lucide-react";
import { ProviderSelector } from "../components/ProviderSelector";
import { LogTabs } from "../components/LogTabs";
import { EnhancedLogViewer } from "../components/EnhancedLogViewer";
import { Chatbot } from "../components/Chatbot";
import ProviderFilters from "../components/Filters/ProviderFilters";
import { useAuth } from "../contexts/Auth";
import { useLogService } from "../services/logService";
import type { GCPService, LogTab } from "../types/gcp";
import { GCPQueryBuilder } from "../components/GCPQueryBuilder";
import { getServiceById } from "../data/gcpResourceMappings";
import DateTimeSearchBar from "../components/DateTimeSearchBar";

export const Home = () => {
  const [selectedService, setSelectedService] = useState<
    GCPService | undefined
  >();
  const [tabs, setTabs] = useState<any[]>([]);
  const [activeTabId, setActiveTabId] = useState<string>("");
  // Change logs to be per-tab
  const [tabLogs, setTabLogs] = useState<Record<string, any[]>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [selectedProvider, setSelectedProvider] = useState<any>();
  const [openQueryBuilderTabId, setOpenQueryBuilderTabId] = useState<
    string | null
  >(null);
  const { token, logout } = useAuth();
  const { fetchLogs } = useLogService();

  // New: Simple search and date/time state
  const [searchQuery, setSearchQuery] = useState("");
  const [startDate, setStartDate] = useState(""); // ISO string
  const [endDate, setEndDate] = useState(""); // ISO string
  const [pendingSearch, setPendingSearch] = useState({
    searchQuery: "",
    startDate: "",
    endDate: "",
  });

  // Only fetch logs when user clicks Search or presses Enter
  const handleSearch = () => {
    setPendingSearch({ searchQuery, startDate, endDate });
  };

  useEffect(() => {
    fetchProjects();
  }, [token]);

  const fetchProjects = async () => {
    if (!token) return;
    try {
      const response = await fetch("/api/v1/logs/projects", {
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

  // Create a new tab when service is selected (allow multiple tabs for same service)
  const handleServiceSelect = (service: GCPService) => {
    const tabId = `${service.id}-${Date.now()}`;
    // Use the user-friendly service name for the tab title
    const tabTitle = service.name;
    const newTab: LogTab = {
      id: tabId,
      title: tabTitle,
      serviceId: service.id,
      isActive: true,
      filters: {
        severity: [],
        resourceType: service.id, // Ensure resourceType is set to the service id
        logType: [],
        sourceLocation: "",
        userAccount: "",
        requestId: "",
        timeRange: "1h",
        customQuery: "",
      },
      query: "",
      lastUpdated: new Date(),
    };
    setTabs((prev) => [...prev, newTab]);
    setActiveTabId(tabId);
    setSelectedService(service);
  };

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
    if (tabId === activeTabId) {
      const remainingTabs = tabs.filter((tab) => tab.id !== tabId);
      if (remainingTabs.length > 0) {
        setActiveTabId(remainingTabs[0].id);
      } else {
        setActiveTabId("");
        setSelectedService(undefined);
      }
    }
    // Close query builder if it's open for this tab
    if (openQueryBuilderTabId === tabId) {
      setOpenQueryBuilderTabId(null);
    }
  };

  // Handler for opening query builder for a tab
  const handleOpenQueryBuilder = (tabId: string) => {
    // Verify the tab exists before opening query builder
    const tab = tabs.find((tab) => tab.id === tabId);
    if (tab) {
      setOpenQueryBuilderTabId(tabId);
    } else {
      console.error(`Tab with id ${tabId} not found`);
    }
  };

  // Handler for closing query builder
  const handleCloseQueryBuilder = () => {
    setOpenQueryBuilderTabId(null);
  };

  // Handler for updating a tab (e.g., when query builder changes resource type)
  const handleUpdateTab = (updatedTab: LogTab) => {
    setTabs((prev) =>
      prev.map((tab) => {
        if (tab.id === updatedTab.id) {
          // Update the tab title if resourceType changed
          const svc = getServiceById(updatedTab.filters.resourceType);
          return {
            ...updatedTab,
            title: svc ? svc.id : updatedTab.title,
          };
        }
        return tab;
      })
    );
  };

  // Handler for query submission from QueryBuilder
  const handleQuerySubmit = (query: string) => {
    if (!openQueryBuilderTabId) return;
    setTabs((prev) =>
      prev.map((tab) =>
        tab.id === openQueryBuilderTabId
          ? { ...tab, query, lastUpdated: new Date() }
          : tab
      )
    );
    setOpenQueryBuilderTabId(null);
    // Fetch logs for this tab after updating query
    const tab = tabs.find((t) => t.id === openQueryBuilderTabId);
    if (tab) {
      fetchLogsForTab({ ...tab, query });
    }
  };

  // Get the current tab for query builder
  const getCurrentTab = () => {
    if (!openQueryBuilderTabId) return null;
    const tab = tabs.find((t) => t.id === openQueryBuilderTabId);
    return tab || null;
  };

  const currentTab = getCurrentTab();

  // Fetch logs for a specific tab
  const fetchLogsForTab = async (tab: LogTab) => {
    if (!selectedProject || !tab) return;
    setIsLoading(true);
    try {
      const res = await fetchLogs({
        projectId: selectedProject,
        serviceId: tab.filters.resourceType,
        searchQuery: tab.query,
        filters: {
          ...tab.filters,
        },
      });
      setTabLogs((prev) => ({ ...prev, [tab.id]: res.logs }));
    } catch (e) {
      setTabLogs((prev) => ({ ...prev, [tab.id]: [] }));
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch logs when active tab or its filters/query changes
  useEffect(() => {
    const activeTab = tabs.find((t) => t.id === activeTabId);
    if (activeTab && selectedProject) {
      fetchLogsForTab(activeTab);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTabId, selectedProject, tabs]);

  return (
    <div className="bg-gray-950 min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-800/50 sticky top-0 z-50">
        <div className="w-full px-3 sm:px-4 md:px-6 lg:px-8 xl:px-12 2xl:px-16 py-2 sm:py-3 md:py-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-0">
            {/* Logo and Title Section */}
            <div className="flex items-center justify-between sm:justify-start">
              <div className="flex items-center space-x-2 sm:space-x-4">
                <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Wassup?
                </h1>
                <div className="hidden sm:block h-6 w-px bg-gray-700"></div>
                <div className="hidden sm:block">
                  <span className="text-xs sm:text-sm text-gray-400">
                    Exploring the logs. Wanna join?
                  </span>
                </div>
              </div>
            </div>

            {/* Controls Section */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
              {/* Provider Selector */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
                <label className="text-xs sm:text-sm font-medium text-gray-300 whitespace-nowrap">
                  Cloud Provider
                </label>
                <ProviderSelector
                  selectedProvider={selectedProvider}
                  onProviderSelect={setSelectedProvider}
                  className="w-full sm:w-64 md:w-80 lg:w-96"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 sm:gap-3">
                <button
                  onClick={() => {}}
                  disabled={isLoading}
                  className="flex-1 sm:flex-none inline-flex items-center justify-center px-2 sm:px-3 py-2 text-xs sm:text-sm font-medium text-gray-300 bg-gray-800/50 border border-gray-700 rounded-lg hover:bg-gray-700/50 hover:text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <RefreshCw
                    className={`w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2 ${
                      isLoading ? "animate-spin" : ""
                    }`}
                  />
                  <span className="hidden sm:inline">Refresh</span>
                </button>
                <button
                  onClick={() => {}}
                  disabled={
                    !activeTabId ||
                    !tabLogs[activeTabId] ||
                    tabLogs[activeTabId].length === 0
                  }
                  className="flex-1 sm:flex-none inline-flex items-center justify-center px-2 sm:px-3 py-2 text-xs sm:text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Download className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                  <span className="hidden sm:inline">Export</span>
                </button>
                <button className="inline-flex items-center justify-center p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-all duration-200">
                  <Settings className="w-3 h-3 sm:w-4 sm:h-4" />
                </button>
                <button
                  onClick={logout}
                  className="flex-1 sm:flex-none inline-flex items-center justify-center px-2 sm:px-3 py-2 text-xs sm:text-sm font-medium text-red-400 bg-gray-800/50 border border-gray-700 rounded-lg hover:bg-red-500/20 hover:text-red-500 transition-all duration-200"
                >
                  <svg
                    className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2h4a2 2 0 012 2v1"
                    />
                  </svg>
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Modern Search and Date/Time Filter Bar */}
      <DateTimeSearchBar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        startDate={startDate}
        setStartDate={setStartDate}
        endDate={endDate}
        setEndDate={setEndDate}
        isLoading={isLoading}
        onSearch={handleSearch}
      />

      {/* Provider-specific filters */}
      <ProviderFilters
        selectedProvider={selectedProvider}
        selectedProject={selectedProject}
        setSelectedProject={setSelectedProject}
        projects={projects}
        selectedService={selectedService}
        onServiceSelect={handleServiceSelect}
        selectedDeployment={undefined}
        onDeploymentSelect={() => {}}
      />

      {/* Tabs */}
      {tabs.length > 0 && (
        <div className="">
          <div className="w-full px-3 sm:px-4 md:px-6 lg:px-8 xl:px-12 2xl:px-16">
            <LogTabs
              tabs={tabs}
              activeTabId={activeTabId}
              onTabSelect={handleTabSelect}
              onTabClose={handleTabClose}
              onOpenQueryBuilder={handleOpenQueryBuilder}
            />
          </div>
        </div>
      )}

      {/* Query Builder Modal (only when settings icon is clicked and tab exists) */}
      {openQueryBuilderTabId && currentTab && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="relative w-full max-w-5xl mx-4 max-h-[90vh] overflow-y-auto">
            {/* Close button */}
            <button
              className="absolute top-4 right-4 z-10 p-2 bg-gray-800 text-gray-300 rounded-full hover:bg-gray-700 hover:text-white transition-all shadow-lg"
              onClick={handleCloseQueryBuilder}
              title="Close Query Builder"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Query Builder */}
            <GCPQueryBuilder
              tab={currentTab}
              projectId={selectedProject}
              onUpdateTab={handleUpdateTab}
              onQuerySubmit={handleQuerySubmit}
              isActive={true}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 w-full px-3 sm:px-4 md:px-6 lg:px-8 xl:px-12 2xl:px-16 py-4 sm:py-6">
        <div className="grid grid-cols-1 xl:grid-cols-20 2xl:grid-cols-20 gap-4 sm:gap-6 xl:gap-8 2xl:gap-12 h-full">
          {/* Logs Section */}
          <div className="xl:col-span-13 2xl:col-span-13 space-y-3 sm:space-y-4 xl:space-y-6">
            {/* Logs Viewer Card */}
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl shadow-lg overflow-hidden">
              <div className="px-4 sm:px-6 xl:px-8 py-3 sm:py-4 xl:py-6 border-b border-gray-800/50 bg-gray-900/30">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0">
                  <div className="flex items-center space-x-2 sm:space-x-3 xl:space-x-4">
                    <h3 className="text-base sm:text-lg xl:text-xl font-semibold text-white">
                      Log Entries
                    </h3>
                    {activeTabId &&
                      tabLogs[activeTabId] &&
                      tabLogs[activeTabId].length > 0 && (
                        <span className="inline-flex items-center px-2 py-0.5 sm:px-2.5 xl:px-3 xl:py-1 rounded-full text-xs xl:text-sm font-medium bg-blue-900/20 text-blue-400 border border-blue-800">
                          {tabLogs[activeTabId].length} entries
                        </span>
                      )}
                  </div>
                  {isLoading && (
                    <div className="flex items-center space-x-2 xl:space-x-3 text-gray-400">
                      <RefreshCw className="w-3 h-3 sm:w-4 sm:h-4 animate-spin" />
                      <span className="text-xs sm:text-sm xl:text-base">
                        Loading logs...
                      </span>
                    </div>
                  )}
                </div>
              </div>
              <div className="relative">
                {(!activeTabId ||
                  !tabLogs[activeTabId] ||
                  tabLogs[activeTabId].length === 0) &&
                !isLoading ? (
                  <div className="flex flex-col items-center justify-center py-8 sm:py-12 xl:py-16 px-4 sm:px-6 xl:px-8">
                    <div className="w-12 h-12 sm:w-16 sm:h-16 xl:w-20 xl:h-20 bg-gray-800 rounded-full flex items-center justify-center mb-3 sm:mb-4 xl:mb-6">
                      <Search className="w-6 h-6 sm:w-8 sm:h-8 xl:w-10 xl:h-10 text-gray-400" />
                    </div>
                    <h3 className="text-base sm:text-lg xl:text-xl font-medium text-gray-300 mb-2 xl:mb-3 text-center">
                      No logs found
                    </h3>
                    <p className="text-gray-500 text-center max-w-sm sm:max-w-md xl:max-w-lg text-xs sm:text-sm xl:text-lg">
                      {!selectedProject || !selectedService
                        ? "Select a project and service to start exploring logs"
                        : "Try adjusting your search query or filters to find relevant logs"}
                    </p>
                  </div>
                ) : (
                  <div className="max-h-[calc(100vh-300px)] sm:max-h-[calc(100vh-350px)] xl:max-h-[calc(100vh-400px)] overflow-y-auto">
                    <EnhancedLogViewer logs={tabLogs[activeTabId] || []} />
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Chatbot Section */}
          <div className="xl:col-span-7 2xl:col-span-7">
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl shadow-lg overflow-hidden h-[300px] sm:h-[400px] xl:h-[calc(100vh-300px)] 2xl:h-[calc(100vh-280px)] xl:sticky xl:top-24">
              <div className="px-3 sm:px-4 xl:px-6 py-2 sm:py-3 xl:py-4 border-b border-gray-800/50 bg-gray-900/30">
                <h3 className="text-xs sm:text-sm xl:text-base font-semibold text-white">
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
