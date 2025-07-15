import React from "react";
import { Search, Filter, ChevronDown, RefreshCw } from "lucide-react";
import { AdvancedFilters } from "../AdvancedFilters";
import type { FilterState } from "../../types/gcp";

interface CommonFiltersProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  showAdvancedFilters: boolean;
  setShowAdvancedFilters: (show: boolean) => void;
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  handleSearch: () => void;
  isLoading: boolean;
  disabled?: boolean;
}

const CommonFilters: React.FC<CommonFiltersProps> = ({
  searchQuery,
  setSearchQuery,
  showAdvancedFilters,
  setShowAdvancedFilters,
  filters,
  onFiltersChange,
  handleSearch,
  isLoading,
  disabled = false,
}) => {
  return (
    <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-4 sm:p-6 xl:p-8 shadow-lg">
      <div className="space-y-3 sm:space-y-4 xl:space-y-6">
        {/* Search Bar */}
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 xl:gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search logs, messages, or trace IDs..."
              disabled={disabled}
              className="w-full pl-10 pr-4 py-2.5 sm:py-3 xl:py-4 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
            />
          </div>

          <div className="flex gap-2 xl:gap-3">
            <button
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              disabled={disabled}
              className={`inline-flex items-center px-3 sm:px-4 xl:px-6 py-2.5 sm:py-3 xl:py-4 text-xs sm:text-sm font-medium border rounded-lg transition-all duration-200 ${
                showAdvancedFilters
                  ? "text-blue-400 bg-blue-900/20 border-blue-700"
                  : "text-gray-300 bg-gray-800/50 border-gray-700 hover:bg-gray-700/50"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <Filter className="w-3 h-3 sm:w-4 sm:h-4 mr-1.5 sm:mr-2" />
              <span className="hidden sm:inline">Filters</span>
              <ChevronDown
                className={`w-3 h-3 sm:w-4 sm:h-4 ml-1.5 sm:ml-2 transition-transform ${
                  showAdvancedFilters ? "rotate-180" : ""
                }`}
              />
            </button>

            <button
              onClick={handleSearch}
              disabled={isLoading || disabled}
              className="inline-flex items-center px-4 sm:px-6 xl:px-8 py-2.5 sm:py-3 xl:py-4 text-xs sm:text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-3 h-3 sm:w-4 sm:h-4 mr-1.5 sm:mr-2 animate-spin" />
                  <span className="hidden sm:inline">Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-3 h-3 sm:w-4 sm:h-4 mr-1.5 sm:mr-2" />
                  <span className="hidden sm:inline">Search</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Advanced Filters */}
        {showAdvancedFilters && (
          <div className="border-t border-gray-800 pt-3 sm:pt-4 xl:pt-6">
            <AdvancedFilters
              filters={filters}
              onFiltersChange={onFiltersChange}
              service={undefined}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default CommonFilters;
