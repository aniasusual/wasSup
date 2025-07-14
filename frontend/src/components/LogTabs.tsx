import { useState, useRef, useEffect } from "react";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import type { LogTab } from "../types/gcp";

interface LogTabsProps {
  tabs: LogTab[];
  activeTabId: string;
  onTabSelect: (tabId: string) => void;
  onTabClose: (tabId: string) => void;
  className?: string;
}

export const LogTabs = ({
  tabs,
  activeTabId,
  onTabSelect,
  onTabClose,
  className = "",
}: LogTabsProps) => {
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);
  const tabsContainerRef = useRef<HTMLDivElement>(null);
  const tabsWrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkScrollButtons();
  }, [tabs]);

  const checkScrollButtons = () => {
    if (!tabsContainerRef.current || !tabsWrapperRef.current) return;

    const container = tabsContainerRef.current;
    const wrapper = tabsWrapperRef.current;

    setShowLeftArrow(wrapper.scrollLeft > 0);
    setShowRightArrow(
      wrapper.scrollLeft < wrapper.scrollWidth - container.clientWidth
    );
  };

  const scrollLeft = () => {
    if (tabsWrapperRef.current) {
      tabsWrapperRef.current.scrollBy({ left: -200, behavior: "smooth" });
    }
  };

  const scrollRight = () => {
    if (tabsWrapperRef.current) {
      tabsWrapperRef.current.scrollBy({ left: 200, behavior: "smooth" });
    }
  };

  const handleTabClose = (e: React.MouseEvent, tabId: string) => {
    e.stopPropagation();
    onTabClose(tabId);
  };

  const getTabTitle = (tab: LogTab) => {
    if (tab.deploymentId) {
      return `${tab.title} - ${tab.deploymentId}`;
    }
    return tab.title;
  };

  return (
    <div className={`bg-gray-900 border-b border-gray-800 ${className}`}>
      <div className="flex items-center">
        {/* Scroll Left Button */}
        {showLeftArrow && (
          <button
            onClick={scrollLeft}
            className="flex-shrink-0 p-2 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}

        {/* Tabs Container */}
        <div ref={tabsContainerRef} className="flex-1 overflow-hidden">
          <div
            ref={tabsWrapperRef}
            className="flex space-x-1 p-2 overflow-x-auto scrollbar-hide"
            onScroll={checkScrollButtons}
          >
            {tabs.map((tab) => (
              <div
                key={tab.id}
                onClick={() => onTabSelect(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-t-lg cursor-pointer transition-colors flex-shrink-0 min-w-0 ${
                  tab.id === activeTabId
                    ? "bg-gray-800 text-white border-b-2 border-blue-500"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white"
                }`}
              >
                <span className="truncate max-w-32">{getTabTitle(tab)}</span>
                <button
                  onClick={(e) => handleTabClose(e, tab.id)}
                  className="flex-shrink-0 p-1 rounded hover:bg-gray-600 transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Scroll Right Button */}
        {showRightArrow && (
          <button
            onClick={scrollRight}
            className="flex-shrink-0 p-2 text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
