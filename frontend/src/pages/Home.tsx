import { useState, useEffect, useCallback, useRef } from "react";
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
import DateTimeSearchBar from "../components/DateTimeSearchBar";
import toast from "react-hot-toast";
import { parseGCPErrorMessage } from "../utils/errorUtils";

export const Home = () => {
  const [selectedService, setSelectedService] = useState<
    GCPService | undefined
  >();
  const [tabs, setTabs] = useState<any[]>([]);
  const [activeTabId, setActiveTabId] = useState<string>("");
  // Change logs to be per-tab
  const [tabLogs, setTabLogs] = useState<Record<string, any[]>>({});
  const [tabNextTokens, setTabNextTokens] = useState<
    Record<string, string | null>
  >({});
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [selectedProvider, setSelectedProvider] = useState<any>();

  // Handler for provider selection
  const handleProviderSelect = (provider: any) => {
    setSelectedProvider(provider);
    // Clear projects when switching providers
    setProjects([]);
    setSelectedProject("");
  };
  const [openQueryBuilderTabId, setOpenQueryBuilderTabId] = useState<
    string | null
  >(null);
  const { token, logout, forceLogout } = useAuth();
  const { fetchLogs } = useLogService();

  // New: Simple search and date/time state
  const [searchQuery, setSearchQuery] = useState("");
  const [startDate, setStartDate] = useState(() => {
    // Default to 1 hour ago
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    const year = oneHourAgo.getFullYear();
    const month = String(oneHourAgo.getMonth() + 1).padStart(2, "0");
    const day = String(oneHourAgo.getDate()).padStart(2, "0");
    const hours = String(oneHourAgo.getHours()).padStart(2, "0");
    const minutes = String(oneHourAgo.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  });
  const [endDate, setEndDate] = useState(() => {
    // Default to now
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  });
  const [pendingSearch, setPendingSearch] = useState({
    searchQuery: "",
    startDate: "",
    endDate: "",
  });

  // Only fetch logs when user clicks Search or presses Enter
  const handleSearch = () => {
    setPendingSearch({ searchQuery, startDate, endDate });
  };

  // Handle time range changes from slider (debounced)
  const handleTimeRangeChange = useCallback(
    (newStartDate: string, newEndDate: string) => {
      console.log("Time range changed:", { newStartDate, newEndDate });
      setPendingSearch({
        searchQuery,
        startDate: newStartDate,
        endDate: newEndDate,
      });
    },
    [searchQuery]
  );

  const [logCount, setLogCount] = useState(100); // Add log count state
  const [isChatbotExpanded, setIsChatbotExpanded] = useState(false); // Add chatbot expand state

  // Initialize pending search with default time values
  useEffect(() => {
    if (
      startDate &&
      endDate &&
      (!pendingSearch.startDate || !pendingSearch.endDate)
    ) {
      setPendingSearch({
        searchQuery: "",
        startDate,
        endDate,
      });
    }
  }, [startDate, endDate, pendingSearch.startDate, pendingSearch.endDate]);

  useEffect(() => {
    // Only fetch projects if we have a token and a selected provider
    if (token && selectedProvider) {
      fetchProjects();
    }
  }, [token, selectedProvider]);

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
      } else {
        // Check for authentication errors
        if (response.status === 401 || response.status === 403) {
          forceLogout("Authentication token expired or invalid");
          return;
        }

        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || response.statusText;
        const userFriendlyMessage = parseGCPErrorMessage(errorMessage);
        toast.error(`Failed to fetch projects: ${userFriendlyMessage}`);
      }
    } catch (error) {
      console.error("Error fetching projects:", error);

      // Check if it's an authentication error
      if (
        error instanceof Error &&
        error.message.includes("Authentication failed")
      ) {
        return; // Already handled by forceLogout
      }

      const errorMessage =
        error instanceof Error ? error.message : String(error);
      const userFriendlyMessage = parseGCPErrorMessage(errorMessage);
      toast.error(`Failed to fetch projects: ${userFriendlyMessage}`);
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
    // Initial fetch for the newly created tab
    void fetchLogsForTab(newTab);
  };

  // Create an insight tab when clicking a relevant log from chat
  const handleOpenInsightFromChat = ({ sourceMessageId, log }: any) => {
    const tabId = `insight-${log.id}-${Date.now()}`;

    // Create a more descriptive title based on log content
    let title = `🔍 AI Insight`;
    if (log.severity === "ERROR") {
      title = `🚨 Error Analysis`;
    } else if (log.severity === "WARNING") {
      title = `⚠️ Warning Investigation`;
    } else if (log.serviceId) {
      title = `🔍 ${log.serviceId} Analysis`;
    }

    // Build a custom query to find related logs
    const customQuery = log.traceId
      ? `traceId="${log.traceId}"`
      : log.insertId
      ? `insertId="${log.insertId}"`
      : `resource.type="${log.serviceId}" AND severity="${log.severity}"`;

    const newTab: LogTab = {
      id: tabId,
      title,
      serviceId: log.serviceId || "unknown",
      isActive: true,
      filters: {
        severity: log.severity ? [log.severity] : [],
        resourceType: log.serviceId || "",
        logType: [],
        sourceLocation: "",
        userAccount: "",
        requestId: log.traceId || "",
        timeRange: "custom",
        customQuery,
        customStartTime: "",
        customEndTime: "",
      },
      query: customQuery,
      lastUpdated: new Date(),
      type: "insight",
      sourceMessageId,
      primaryLogId: log.insertId || log.id,
    };

    setTabs((prev) => [
      ...prev.map((t) => ({ ...t, isActive: false })),
      newTab,
    ]);
    setActiveTabId(tabId);
    setSelectedService(undefined);

    // Fetch logs for the insight tab
    void fetchLogsForTab(newTab);
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
          // Use the title that was set by the query builder
          return updatedTab;
        }
        return tab;
      })
    );
  };

  // Handler for query submission from QueryBuilder
  const handleQuerySubmit = (query: string) => {
    if (!openQueryBuilderTabId) return;

    // Update the tab with the new query and fetch logs
    setTabs((prev) => {
      const updatedTabs = prev.map((tab) =>
        tab.id === openQueryBuilderTabId
          ? { ...tab, query, lastUpdated: new Date() }
          : tab
      );

      // Find the updated tab and fetch logs for it
      const updatedTab = updatedTabs.find(
        (t) => t.id === openQueryBuilderTabId
      );
      if (updatedTab) {
        // Use setTimeout to ensure state update is complete before fetching
        setTimeout(() => {
          fetchLogsForTab(updatedTab);
        }, 0);
      }

      return updatedTabs;
    });

    setOpenQueryBuilderTabId(null);
  };

  // Get the current tab for query builder
  const getCurrentTab = () => {
    if (!openQueryBuilderTabId) return null;
    const tab = tabs.find((t) => t.id === openQueryBuilderTabId);
    return tab || null;
  };

  const currentTab = getCurrentTab();

  // Fetch logs for a specific tab, always applying global search and time filters
  const fetchLogsForTab = async (tab: LogTab) => {
    if (!selectedProvider || !selectedProject || !tab) return;
    setIsLoading(true);

    console.log("fetchLogsForTab called with:", {
      tabId: tab.id,
      tabQuery: tab.query,
      resourceType: tab.filters.resourceType,
      pendingSearch: {
        searchQuery: pendingSearch.searchQuery,
        startDate: pendingSearch.startDate,
        endDate: pendingSearch.endDate,
      },
    });

    try {
      const res = await fetchLogs({
        projectId: selectedProject,
        serviceId: tab.filters.resourceType,
        filter: tab.query, // Use as filter if present
        filters: {
          ...tab.filters,
          customQuery: pendingSearch.searchQuery, // Apply global search
          customStartTime: pendingSearch.startDate, // Apply global start time
          customEndTime: pendingSearch.endDate, // Apply global end time
        },
        pageSize: logCount, // Pass log count
      });
      const logs = Array.isArray(res?.logs) ? res.logs : [];
      const nextToken =
        typeof res?.nextPageToken === "string" ? res.nextPageToken : null;
      setTabLogs((prev) => ({ ...prev, [tab.id]: logs }));
      setTabNextTokens((prev) => ({
        ...prev,
        [tab.id]: nextToken,
      }));
    } catch (e) {
      console.error("Error fetching logs:", e);

      // Check if it's an authentication error
      if (e instanceof Error && e.message.includes("Authentication failed")) {
        return; // Already handled by forceLogout
      }

      setTabLogs((prev) => ({ ...prev, [tab.id]: [] }));
      const errorMessage = e instanceof Error ? e.message : String(e);
      const userFriendlyMessage = parseGCPErrorMessage(errorMessage);
      toast.error(`Failed to fetch logs: ${userFriendlyMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Load more logs using nextPageToken for the active tab
  const loadMoreForActiveTab = useCallback(async () => {
    if (!activeTabId) return;
    if (isLoading || isLoadingMore) return;
    const nextToken = tabNextTokens[activeTabId];
    if (!nextToken) return;

    const tab = tabs.find((t) => t.id === activeTabId);
    if (!tab || !selectedProvider || !selectedProject) return;

    setIsLoadingMore(true);
    try {
      const res = await fetchLogs({
        projectId: selectedProject,
        serviceId: tab.filters.resourceType,
        filter: tab.query,
        filters: {
          ...tab.filters,
          customQuery: pendingSearch.searchQuery,
          customStartTime: pendingSearch.startDate,
          customEndTime: pendingSearch.endDate,
        },
        pageSize: logCount,
        pageToken: nextToken,
      });
      const logs = Array.isArray(res?.logs) ? res.logs : [];
      const next =
        typeof res?.nextPageToken === "string" ? res.nextPageToken : null;
      setTabLogs((prev) => ({
        ...prev,
        [activeTabId]: [...(prev[activeTabId] || []), ...logs],
      }));
      setTabNextTokens((prev) => ({
        ...prev,
        [activeTabId]: next,
      }));
    } catch (e) {
      console.error("Error loading more logs:", e);
    } finally {
      setIsLoadingMore(false);
    }
  }, [
    activeTabId,
    isLoading,
    isLoadingMore,
    tabNextTokens,
    tabs,
    selectedProject,
    fetchLogs,
    pendingSearch.searchQuery,
    pendingSearch.startDate,
    pendingSearch.endDate,
    logCount,
  ]);

  // Infinite scroll: track scroll position on the logs container
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const handleScroll = useCallback(() => {
    const el = scrollContainerRef.current;
    if (!el) return;
    const threshold = 150; // px from bottom
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - threshold) {
      void loadMoreForActiveTab();
    }
  }, [loadMoreForActiveTab]);

  // Fetch logs when active tab, global filters, or its filters/query changes
  useEffect(() => {
    const activeTab = tabs.find((t) => t.id === activeTabId);
    if (activeTab && selectedProject) {
      fetchLogsForTab(activeTab);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    selectedProject,
    pendingSearch.searchQuery,
    pendingSearch.startDate,
    pendingSearch.endDate,
    logCount,
  ]);

  // Manual refresh handler
  const handleRefresh = () => {
    const activeTab = tabs.find((t) => t.id === activeTabId);
    if (activeTab) {
      void fetchLogsForTab(activeTab);
    }
  };

  const refreshTabById = useCallback(
    async (tabId: string) => {
      const tab = tabs.find((t) => t.id === tabId);
      if (tab) {
        await fetchLogsForTab(tab);
      }
    },
    [tabs]
  );

  // Handle chatbot expand toggle
  const handleChatbotToggle = useCallback(() => {
    setIsChatbotExpanded((prev) => !prev);
  }, []);

  return (
    <div className="bg-gray-950 h-screen flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-800/50 sticky top-0 z-50">
        <div className="w-full px-3 sm:px-4 md:px-6 lg:px-8 xl:px-12 2xl:px-16 py-2 sm:py-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-0">
            {/* Logo and Title Section */}
            <div className="flex items-center justify-between sm:justify-start">
              <div className="flex items-center space-x-2 sm:space-x-4">
                <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Recce
                </h1>
                <div className="hidden sm:block h-6 w-px bg-gray-700"></div>
                <div className="hidden sm:block">
                  <span className="text-xs sm:text-sm text-gray-400">
                    Reconnaissance of the logs
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
                  onProviderSelect={handleProviderSelect}
                  className="w-full sm:w-64 md:w-80 lg:w-96"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 sm:gap-3">
                <button
                  onClick={handleRefresh}
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

      {/* Provider-specific filters - only show when provider is selected */}
      {selectedProvider && (
        <ProviderFilters
          selectedProvider={selectedProvider}
          selectedProject={selectedProject}
          setSelectedProject={setSelectedProject}
          projects={projects}
          selectedService={selectedService}
          onServiceSelect={handleServiceSelect}
        />
      )}
      {/* Modern Search and Date/Time Filter Bar - only show when provider is selected */}
      {selectedProvider && (
        <DateTimeSearchBar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          startDate={startDate}
          setStartDate={setStartDate}
          endDate={endDate}
          setEndDate={setEndDate}
          isLoading={isLoading}
          onSearch={handleSearch}
          onTimeRangeChange={handleTimeRangeChange}
        />
      )}

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
              onRefreshTab={refreshTabById}
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
      <main className="flex-1 w-full px-3 sm:px-4 md:px-6 lg:px-8 xl:px-12 2xl:px-16 py-2 sm:py-3 min-h-0">
        {!selectedProvider ? (
          // Show welcome message when no provider is selected
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-16 h-16 sm:w-20 sm:h-20 xl:w-24 xl:h-24 bg-gray-800 rounded-full flex items-center justify-center mb-6 sm:mb-8 xl:mb-10">
              <span className="text-2xl sm:text-3xl xl:text-4xl">☁️</span>
            </div>
            <h2 className="text-xl sm:text-2xl xl:text-3xl font-semibold text-white mb-3 sm:mb-4 xl:mb-6 text-center">
              Welcome to Recce
            </h2>
            <p className="text-gray-400 text-center max-w-md sm:max-w-lg xl:max-w-xl text-sm sm:text-base xl:text-lg mb-6 sm:mb-8 xl:mb-10">
              Select a cloud provider from the header to start exploring your
              logs and get insights from your data.
            </p>
            <div className="text-center">
              <p className="text-gray-500 text-xs sm:text-sm xl:text-base">
                Currently supporting: Google Cloud Platform
              </p>
            </div>
          </div>
        ) : (
          <div className="h-full">
            {isChatbotExpanded ? (
              /* Full-screen Chatbot when expanded */
              <div className="h-full">
                <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl shadow-lg h-full overflow-hidden">
                  <div className="h-full flex flex-col min-h-0">
                    <Chatbot
                      key="chatbot-main" // Use same key to maintain component identity
                      selectedServices={
                        selectedService ? [selectedService.id] : []
                      }
                      projectId={selectedProject}
                      onOpenInsight={handleOpenInsightFromChat}
                      isExpanded={isChatbotExpanded}
                      onToggleExpand={handleChatbotToggle}
                    />
                  </div>
                </div>
              </div>
            ) : (
              /* Normal layout with logs and chatbot side by side */
              <div className="grid grid-cols-1 xl:grid-cols-20 2xl:grid-cols-20 gap-3 sm:gap-4 xl:gap-6 2xl:gap-8 h-full">
                {/* Logs Section */}
                <div className="xl:col-span-13 2xl:col-span-13 flex flex-col min-h-0">
                  {/* Logs Viewer Card */}
                  <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl shadow-lg overflow-hidden flex-1 flex flex-col min-h-0">
                    <div className="px-4 sm:px-6 xl:px-8 py-2 sm:py-3 xl:py-4 border-b border-gray-800/50 bg-gray-900/30">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0">
                        <div className="flex items-center space-x-2 sm:space-x-3 xl:space-x-4">
                          <h3 className="text-base sm:text-lg xl:text-xl font-semibold text-white">
                            Log Entries
                          </h3>
                          {/* Log count dropdown */}
                          <select
                            className="ml-2 px-2 py-1 rounded bg-gray-800 text-blue-400 border border-blue-800 text-xs xl:text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={logCount}
                            onChange={(e) =>
                              setLogCount(Number(e.target.value))
                            }
                            style={{ minWidth: 60 }}
                            title="Select number of logs to display"
                          >
                            {[50, 100, 200, 500, 1000].map((count) => (
                              <option key={count} value={count}>
                                {count}
                              </option>
                            ))}
                          </select>
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
                    <div className="flex-1 flex flex-col min-h-0">
                      {(!activeTabId ||
                        !tabLogs[activeTabId] ||
                        tabLogs[activeTabId].length === 0) &&
                      !isLoading ? (
                        <div className="flex-1 flex flex-col items-center justify-center py-8 sm:py-12 xl:py-16 px-4 sm:px-6 xl:px-8">
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
                        <div
                          ref={scrollContainerRef}
                          onScroll={handleScroll}
                          className="flex-1 overflow-y-auto min-h-0"
                        >
                          <EnhancedLogViewer
                            logs={tabLogs[activeTabId] || []}
                          />
                          {/* Loading more indicator */}
                          {isLoadingMore && (
                            <div className="py-2 text-center text-xs text-gray-400">
                              Loading more...
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Chatbot Section */}
                <div className="xl:col-span-7 2xl:col-span-7 flex flex-col min-h-0">
                  <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl shadow-lg flex-1 flex flex-col min-h-0 xl:sticky xl:top-24 overflow-hidden">
                    <div className="h-full flex flex-col min-h-0">
                      <Chatbot
                        key="chatbot-main" // Use same key to maintain component identity
                        selectedServices={
                          selectedService ? [selectedService.id] : []
                        }
                        projectId={selectedProject}
                        onOpenInsight={handleOpenInsightFromChat}
                        isExpanded={isChatbotExpanded}
                        onToggleExpand={handleChatbotToggle}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default Home;
