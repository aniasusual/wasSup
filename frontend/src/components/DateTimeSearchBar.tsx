import React, { useMemo, useCallback, useState } from "react";
import { Search, Clock, Calendar, Filter, X } from "lucide-react";
import Slider from "rc-slider";
import "rc-slider/assets/index.css";

interface DateTimeSearchBarProps {
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  startDate: string;
  setStartDate: (d: string) => void;
  endDate: string;
  setEndDate: (d: string) => void;
  isLoading?: boolean;
  onSearch: () => void;
}

const PRESETS = [
  { label: "5m", minutes: 5, color: "bg-green-600 hover:bg-green-700" },
  { label: "20m", minutes: 20, color: "bg-blue-600 hover:bg-blue-700" },
  { label: "1h", minutes: 60, color: "bg-purple-600 hover:bg-purple-700" },
  { label: "6h", minutes: 360, color: "bg-orange-600 hover:bg-orange-700" },
  { label: "24h", minutes: 1440, color: "bg-red-600 hover:bg-red-700" },
];

const MS_PER_MIN = 60 * 1000;

const DateTimeSearchBar: React.FC<DateTimeSearchBarProps> = ({
  searchQuery,
  setSearchQuery,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  isLoading = false,
  onSearch,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activePreset, setActivePreset] = useState<string | null>(null);

  // Helper function to convert date to datetime-local format
  const toDateTimeLocal = useCallback((timestamp: number) => {
    return new Date(timestamp - new Date().getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
  }, []);

  // Format time for display
  const formatTime = useCallback((timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - timestamp;
    const diffMins = Math.floor(diffMs / MS_PER_MIN);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return "now";
  }, []);

  // Slider range: from 24hr ago to now (fixed values)
  const minTs = useMemo(() => Date.now() - 24 * 60 * MS_PER_MIN, []);
  const maxTs = useMemo(() => Date.now(), []);

  // Convert ISO strings to timestamps for slider, with fallbacks
  const startTs = useMemo(() => {
    if (!startDate) return Date.now() - 5 * MS_PER_MIN;
    const ts = new Date(startDate).getTime();
    return isNaN(ts) ? Date.now() - 5 * MS_PER_MIN : ts;
  }, [startDate]);

  const endTs = useMemo(() => {
    if (!endDate) return Date.now();
    const ts = new Date(endDate).getTime();
    return isNaN(ts) ? Date.now() : ts;
  }, [endDate]);

  // Handler for slider change
  const handleSliderChange = useCallback(
    (values: number | number[]) => {
      if (Array.isArray(values) && values.length === 2) {
        const [newStartTs, newEndTs] = values;
        setStartDate(toDateTimeLocal(newStartTs));
        setEndDate(toDateTimeLocal(newEndTs));
        setActivePreset(null); // Clear active preset when manually adjusting
      }
    },
    [setStartDate, setEndDate, toDateTimeLocal]
  );

  // Handler for preset buttons
  const handlePreset = useCallback(
    (minutes: number, label: string) => {
      const now = Date.now();
      const fromTs = now - minutes * MS_PER_MIN;

      setStartDate(toDateTimeLocal(fromTs));
      setEndDate(toDateTimeLocal(now));
      setActivePreset(label);
    },
    [setStartDate, setEndDate, toDateTimeLocal]
  );

  // Handle manual datetime input changes
  const handleStartDateChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setStartDate(e.target.value);
      setActivePreset(null);
    },
    [setStartDate]
  );

  const handleEndDateChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setEndDate(e.target.value);
      setActivePreset(null);
    },
    [setEndDate]
  );

  const clearSearch = useCallback(() => {
    setSearchQuery("");
  }, [setSearchQuery]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        onSearch();
      }
    },
    [onSearch]
  );

  return (
    <div className="w-full rounded-2xl shadow-2xl backdrop-blur-sm">
      {/* Main Search Bar */}
      <div className="p-4 sm:p-6">
        <div className="flex flex-col lg:flex-row gap-4 items-stretch lg:items-center">
          {/* Search Input */}
          <div className="flex-1 relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none z-10">
              <Search className="h-5 w-5 text-gray-400 group-focus-within:text-blue-400 transition-colors" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search logs, errors, trace IDs..."
              className="w-full pl-12 pr-10 py-3 bg-gray-800/80 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 backdrop-blur-sm"
            />
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-white transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Quick Time Presets */}
          <div className="flex flex-wrap gap-2 lg:gap-1 xl:gap-2">
            {PRESETS.map((preset) => (
              <button
                key={preset.label}
                onClick={() => handlePreset(preset.minutes, preset.label)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 transform hover:scale-105 active:scale-95 ${
                  activePreset === preset.label
                    ? `${preset.color} text-white shadow-lg`
                    : "bg-gray-700/80 text-gray-300 hover:bg-gray-600/80 hover:text-white"
                } border border-gray-600/30`}
                type="button"
              >
                {preset.label}
              </button>
            ))}
          </div>

          {/* Advanced Toggle & Search Button */}
          <div className="flex gap-2">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                showAdvanced
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700/80 text-gray-300 hover:bg-gray-600/80"
              } border border-gray-600/30`}
              type="button"
            >
              <Filter className="h-4 w-4" />
              <span className="hidden sm:inline">Advanced</span>
            </button>

            <button
              onClick={onSearch}
              disabled={isLoading}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-600 disabled:to-gray-700 text-white rounded-lg font-medium transition-all duration-200 flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:scale-105 active:scale-95 disabled:transform-none disabled:opacity-50"
            >
              {isLoading ? (
                <div className="h-4 w-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">Search</span>
            </button>
          </div>
        </div>
      </div>

      {/* Advanced Controls */}
      {showAdvanced && (
        <div className="border-t border-gray-700/50 p-4 sm:p-6 bg-gray-800/30 rounded-b-2xl">
          <div className="space-y-6">
            {/* Time Range Slider */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm text-gray-300">
                <Clock className="h-4 w-4" />
                <span className="font-medium">Time Range</span>
                <span className="text-gray-500">
                  ({formatTime(startTs)} → {formatTime(endTs)})
                </span>
              </div>

              <div className="px-2">
                <Slider
                  range
                  min={minTs}
                  max={maxTs}
                  value={[Math.max(minTs, startTs), Math.min(maxTs, endTs)]}
                  onChange={handleSliderChange}
                  allowCross={false}
                  step={60 * 1000} // 1 minute steps
                  trackStyle={[
                    {
                      backgroundColor: "#3B82F6",
                      height: 6,
                      borderRadius: 3,
                    },
                  ]}
                  handleStyle={[
                    {
                      borderColor: "#3B82F6",
                      backgroundColor: "#3B82F6",
                      width: 20,
                      height: 20,
                      marginTop: -7,
                      boxShadow: "0 0 0 3px rgba(59, 130, 246, 0.2)",
                    },
                    {
                      borderColor: "#3B82F6",
                      backgroundColor: "#3B82F6",
                      width: 20,
                      height: 20,
                      marginTop: -7,
                      boxShadow: "0 0 0 3px rgba(59, 130, 246, 0.2)",
                    },
                  ]}
                  railStyle={{
                    backgroundColor: "#374151",
                    height: 6,
                    borderRadius: 3,
                  }}
                />
              </div>

              <div className="flex justify-between text-xs text-gray-400 px-2">
                <span className="bg-gray-700/50 px-2 py-1 rounded">
                  {new Date(startTs).toLocaleString()}
                </span>
                <span className="bg-gray-700/50 px-2 py-1 rounded">
                  {new Date(endTs).toLocaleString()}
                </span>
              </div>
            </div>

            {/* Manual Date/Time Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-gray-300 font-medium">
                  <Calendar className="h-4 w-4" />
                  Start Time
                </label>
                <input
                  type="datetime-local"
                  value={startDate}
                  onChange={handleStartDateChange}
                  className="w-full bg-gray-800/80 border border-gray-600/50 rounded-lg text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all text-sm"
                />
              </div>

              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-gray-300 font-medium">
                  <Calendar className="h-4 w-4" />
                  End Time
                </label>
                <input
                  type="datetime-local"
                  value={endDate}
                  onChange={handleEndDateChange}
                  className="w-full bg-gray-800/80 border border-gray-600/50 rounded-lg text-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all text-sm"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DateTimeSearchBar;
