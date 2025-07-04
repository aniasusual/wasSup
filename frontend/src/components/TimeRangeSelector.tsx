import React, { useState, useEffect } from "react";
import {
  Plus,
  Search,
  Filter,
  Calendar,
  Clock,
  ChevronDown,
  X,
  Upload,
  Check,
  MessageSquare,
  Send,
  Settings,
  Trash2,
} from "lucide-react";

export const TimeRangeSelector = ({ value, onChange }: any) => {
  const [customRange, setCustomRange] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const presets = [
    { label: "Last 15 minutes", value: "15m" },
    { label: "Last hour", value: "1h" },
    { label: "Last 24 hours", value: "24h" },
    { label: "Last 7 days", value: "7d" },
    { label: "Last 30 days", value: "30d" },
    { label: "Custom range", value: "custom" },
  ];

  const handlePresetChange = (preset: any) => {
    if (preset === "custom") {
      setCustomRange(true);
    } else {
      setCustomRange(false);
      onChange(preset);
    }
  };

  const applyCustomRange = () => {
    onChange({ start: startDate, end: endDate });
    setCustomRange(false);
  };

  return (
    <div className="relative">
      <div className="flex gap-2">
        {presets.map((preset) => (
          <button
            key={preset.value}
            onClick={() => handlePresetChange(preset.value)}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              value === preset.value
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-300 hover:bg-gray-700"
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {customRange && (
        <div className="absolute z-20 mt-2 p-4 bg-gray-800 border border-gray-700 rounded-lg shadow-lg">
          <div className="space-y-3">
            <div>
              <label className="block text-sm text-gray-300 mb-1">
                Start Date
              </label>
              <input
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-1">
                End Date
              </label>
              <input
                type="datetime-local"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm"
              />
            </div>
            <button
              onClick={applyCustomRange}
              className="w-full px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
            >
              Apply Range
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
