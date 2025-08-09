import { useState, useRef, useEffect, useCallback } from "react";
import {
  X,
  ChevronLeft,
  ChevronRight,
  Settings,
  RefreshCw,
} from "lucide-react";
import type { LogTab } from "../types/gcp";
import { GCP_RESOURCE_MAPPINGS } from "../data/gcpResourceMappings";

interface LogTabsProps {
  tabs: LogTab[];
  activeTabId: string;
  onTabSelect: (tabId: string) => void;
  onTabClose: (tabId: string) => void;
  onOpenQueryBuilder: (tabId: string) => void;
  onRefreshTab?: (tabId: string) => void;
  className?: string;
}

const getServiceIcon = (serviceId: string) => {
  return null;
};

const getTabTitle = (tab: LogTab) => {
  // Use the resourceType from filters if available, otherwise fall back to serviceId
  const resourceType = tab.filters?.resourceType || tab.serviceId;
  const svc =
    GCP_RESOURCE_MAPPINGS[resourceType as keyof typeof GCP_RESOURCE_MAPPINGS];
  return svc ? svc.id : tab.title;
};

export const LogTabs = ({
  tabs,
  activeTabId,
  onTabSelect,
  onTabClose,
  onOpenQueryBuilder,
  onRefreshTab,
  className = "",
}: LogTabsProps) => {
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);
  const tabsContainerRef = useRef<HTMLDivElement>(null);
  const tabsWrapperRef = useRef<HTMLDivElement>(null);

  const checkScrollButtons = useCallback(() => {
    const container = tabsContainerRef.current;
    const wrapper = tabsWrapperRef.current;
    if (!container || !wrapper) return;

    const leftArrowNeeded = wrapper.scrollLeft > 0;
    const rightArrowNeeded =
      wrapper.scrollLeft + container.offsetWidth < wrapper.scrollWidth;

    setShowLeftArrow((prev) =>
      prev !== leftArrowNeeded ? leftArrowNeeded : prev
    );
    setShowRightArrow((prev) =>
      prev !== rightArrowNeeded ? rightArrowNeeded : prev
    );
  }, []);

  useEffect(() => {
    checkScrollButtons();

    const container = tabsContainerRef.current;
    if (!container) return;

    const resizeObserver = new ResizeObserver(() => {
      checkScrollButtons();
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
    };
  }, [checkScrollButtons]);

  useEffect(() => {
    const timer = setTimeout(() => {
      checkScrollButtons();
    }, 0);

    return () => clearTimeout(timer);
  }, [tabs.length, checkScrollButtons]);

  const scrollLeft = () => {
    const wrapper = tabsWrapperRef.current;
    if (wrapper) {
      wrapper.scrollBy({ left: -200, behavior: "smooth" });
    }
  };

  const scrollRight = () => {
    const wrapper = tabsWrapperRef.current;
    if (wrapper) {
      wrapper.scrollBy({ left: 200, behavior: "smooth" });
    }
  };

  const handleTabClose = (e: React.MouseEvent, tabId: string) => {
    e.stopPropagation();
    onTabClose(tabId);
  };

  return (
    <nav className={`relative w-full ${className}`} aria-label="Log Tabs Bar">
      <div className="flex items-end h-14">
        {/* Scroll Left Button */}
        {showLeftArrow && (
          <button
            onClick={scrollLeft}
            aria-label="Scroll tabs left"
            className="flex-shrink-0 ml-3 mb-2 p-2 rounded-full bg-gray-800/80 hover:bg-gray-700/80 transition-all duration-300 text-gray-300 hover:text-white shadow-md hover:shadow-lg z-20"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        )}

        {/* Tabs Container */}
        <div ref={tabsContainerRef} className="flex-1 overflow-hidden px-2">
          <div
            ref={tabsWrapperRef}
            className="flex items-end overflow-x-auto scrollbar-hide h-full"
            onScroll={checkScrollButtons}
          >
            {tabs.map((tab, index) => (
              <div
                key={tab.id}
                onClick={() => onTabSelect(tab.id)}
                className={`group relative flex items-center gap-2 px-4 py-3 cursor-pointer min-w-[180px] flex-shrink-0 transition-all duration-300 select-none
                  ${
                    tab.id === activeTabId
                      ? "bg-gradient-to-b from-gray-800 to-gray-900 text-white border-t-2 border-blue-500 shadow-xl"
                      : "bg-gray-800/40 text-gray-300 hover:bg-gray-700/60 hover:text-white border-t-2 border-transparent hover:border-gray-600/70"
                  }
                  ${index === 0 ? "rounded-tl-xl ml-3" : ""}
                  ${index === tabs.length - 1 ? "rounded-tr-xl mr-3" : ""}
                `}
                style={{
                  clipPath:
                    tab.id === activeTabId
                      ? "polygon(10px 100%, 0px 10px, 10px 0%, calc(100% - 10px) 0%, 100% 10px, calc(100% - 10px) 100%)"
                      : "polygon(0 100%, 0 0, 100% 0, 100% 100%)",
                  marginRight:
                    tab.id === activeTabId && index !== tabs.length - 1
                      ? "-10px"
                      : "2px",
                  zIndex: tab.id === activeTabId ? 30 : 20 - index,
                }}
                aria-current={tab.id === activeTabId ? "page" : undefined}
                tabIndex={0}
                role="tab"
              >
                {/* Tab background overlay */}
                <div
                  className={`absolute inset-0 ${
                    tab.id === activeTabId
                      ? "bg-gradient-to-b from-blue-500/10 to-transparent"
                      : "bg-gradient-to-b from-gray-700/10 to-transparent"
                  }`}
                  style={{
                    clipPath: "inherit",
                  }}
                />

                <div className="relative flex items-center justify-between w-full gap-2 z-10">
                  <div className="flex items-center gap-2 min-w-0">
                    {getServiceIcon(tab.serviceId)}
                    <span className="truncate max-w-[100px] text-sm font-semibold tracking-tight">
                      {getTabTitle(tab)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    {/* Refresh Tab */}
                    {onRefreshTab && (
                      <button
                        className="p-1.5 rounded-full hover:bg-blue-500/30 text-blue-400 hover:text-blue-300 focus:bg-blue-500/40 focus:text-blue-200 transition-all duration-200 flex-shrink-0"
                        title="Refresh tab"
                        aria-label="Refresh tab"
                        onClick={(e) => {
                          e.stopPropagation();
                          onRefreshTab(tab.id);
                        }}
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    )}
                    {/* Query Builder Icon */}
                    <button
                      className="p-1.5 rounded-full hover:bg-blue-500/30 text-blue-400 hover:text-blue-300 focus:bg-blue-500/40 focus:text-blue-200 transition-all duration-200 flex-shrink-0"
                      title="Open Query Builder"
                      aria-label="Open Query Builder"
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenQueryBuilder(tab.id);
                      }}
                    >
                      <Settings className="w-4 h-4" />
                    </button>
                    {/* Close Button */}
                    <button
                      onClick={(e) => handleTabClose(e, tab.id)}
                      className={`p-1 rounded-full transition-all duration-200 flex-shrink-0 ${
                        tab.id === activeTabId
                          ? "text-gray-300 hover:bg-red-500/30 hover:text-red-300"
                          : "text-gray-400 hover:bg-red-500/30 hover:text-red-300 opacity-0 group-hover:opacity-100"
                      }`}
                      title="Close tab"
                      aria-label="Close tab"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Scroll Right Button */}
        {showRightArrow && (
          <button
            onClick={scrollRight}
            aria-label="Scroll tabs right"
            className="flex-shrink-0 mr-3 mb-2 p-2 rounded-full bg-gray-800/80 hover:bg-gray-700/80 transition-all duration-300 text-gray-300 hover:text-white shadow-md hover:shadow-lg z-20"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Tab bar bottom border */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-600/40 to-transparent" />
    </nav>
  );
};
