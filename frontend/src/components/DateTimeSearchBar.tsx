import React, { useMemo, useCallback } from "react";
import { Search } from "lucide-react";
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
  { label: "Last 5 min", minutes: 5 },
  { label: "Last 20 min", minutes: 20 },
  { label: "Last 30 min", minutes: 30 },
  { label: "Last 1 hr", minutes: 60 },
  { label: "Last 24 hr", minutes: 1440 },
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
  // Helper function to convert date to datetime-local format
  const toDateTimeLocal = useCallback((timestamp: number) => {
    return new Date(timestamp - new Date().getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
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

  // Handler for slider change - use useCallback to prevent unnecessary re-renders
  const handleSliderChange = useCallback(
    (values: number | number[]) => {
      if (Array.isArray(values) && values.length === 2) {
        const [newStartTs, newEndTs] = values;

        // Convert timestamps back to datetime-local format
        setStartDate(toDateTimeLocal(newStartTs));
        setEndDate(toDateTimeLocal(newEndTs));
      }
    },
    [setStartDate, setEndDate, toDateTimeLocal]
  );

  // Handler for preset buttons
  const handlePreset = useCallback(
    (minutes: number) => {
      const now = Date.now();
      const fromTs = now - minutes * MS_PER_MIN;

      setStartDate(toDateTimeLocal(fromTs));
      setEndDate(toDateTimeLocal(now));
    },
    [setStartDate, setEndDate, toDateTimeLocal]
  );

  // Handle manual datetime input changes
  const handleStartDateChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setStartDate(e.target.value);
    },
    [setStartDate]
  );

  const handleEndDateChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setEndDate(e.target.value);
    },
    [setEndDate]
  );

  return (
    <div className="w-full flex flex-col gap-4 items-center bg-gray-900/70 border border-gray-800 rounded-xl px-4 py-4 shadow-lg mt-4">
      {/* Preset Buttons */}
      <div className="flex flex-wrap gap-2 mb-2">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            onClick={() => handlePreset(preset.minutes)}
            className="px-3 py-1 rounded bg-gray-800 text-gray-200 hover:bg-blue-600 hover:text-white text-xs border border-gray-700 transition-all"
            type="button"
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Range Slider */}
      <div className="w-full flex flex-col items-center gap-2">
        <div className="w-full px-2">
          <Slider
            range
            min={minTs}
            max={maxTs}
            value={[Math.max(minTs, startTs), Math.min(maxTs, endTs)]}
            onChange={handleSliderChange}
            allowCross={false}
            step={60 * 1000} // 1 minute steps
            trackStyle={[{ backgroundColor: "#2563eb", height: 4 }]}
            handleStyle={[
              {
                borderColor: "#2563eb",
                backgroundColor: "#2563eb",
                width: 16,
                height: 16,
                marginTop: -6,
              },
              {
                borderColor: "#2563eb",
                backgroundColor: "#2563eb",
                width: 16,
                height: 16,
                marginTop: -6,
              },
            ]}
            railStyle={{ backgroundColor: "#1e293b", height: 4 }}
            dotStyle={{ borderColor: "#2563eb" }}
          />
        </div>
        <div className="flex justify-between w-full text-xs text-gray-400 mt-1 px-2">
          <span>{new Date(startTs).toLocaleString()}</span>
          <span>{new Date(endTs).toLocaleString()}</span>
        </div>
      </div>

      {/* Search and manual input */}
      <div className="w-full flex flex-col sm:flex-row gap-4 items-center mt-2">
        <div className="flex-1 flex items-center gap-2 w-full">
          <span className="inline-flex items-center justify-center p-2 bg-gray-800 rounded-lg">
            <Search className="w-5 h-5 text-gray-400" />
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSearch()}
            placeholder="Search logs, messages, or trace IDs..."
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <label className="text-gray-300 text-sm whitespace-nowrap">
            From
          </label>
          <input
            type="datetime-local"
            value={startDate}
            onChange={handleStartDateChange}
            className="bg-gray-800 border border-gray-700 rounded-lg text-white px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
          <label className="text-gray-300 text-sm whitespace-nowrap">To</label>
          <input
            type="datetime-local"
            value={endDate}
            onChange={handleEndDateChange}
            className="bg-gray-800 border border-gray-700 rounded-lg text-white px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
        </div>

        <button
          onClick={onSearch}
          disabled={isLoading}
          className="inline-flex items-center px-5 py-2.5 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md whitespace-nowrap"
        >
          {isLoading ? (
            <svg
              className="animate-spin h-5 w-5 mr-2 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v8z"
              ></path>
            </svg>
          ) : (
            <Search className="w-4 h-4 mr-2" />
          )}
          Search
        </button>
      </div>
    </div>
  );
};

export default DateTimeSearchBar;
