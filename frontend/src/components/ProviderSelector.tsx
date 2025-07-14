import { useState } from "react";
import { ChevronDown, Search, Check } from "lucide-react";
import type { CloudProvider } from "../types/providers";
import { CLOUD_PROVIDERS } from "../types/providers";

interface ProviderSelectorProps {
  selectedProvider?: CloudProvider;
  onProviderSelect: (provider: CloudProvider) => void;
  className?: string;
}

export const ProviderSelector = ({
  selectedProvider,
  onProviderSelect,
  className = "",
}: ProviderSelectorProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredProviders = CLOUD_PROVIDERS.filter(
    (provider) =>
      provider.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      provider.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleProviderSelect = (provider: CloudProvider) => {
    if (provider.isEnabled) {
      onProviderSelect(provider);
      setIsOpen(false);
      setSearchQuery("");
    }
  };

  return (
    <div className={`relative ${className}`}>
      {/* Selected Provider Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2.5 bg-gray-800/50 border border-gray-700 rounded-lg text-white hover:bg-gray-700/50 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        <div className="flex items-center gap-3">
          {selectedProvider ? (
            <>
              <span className="text-xl">{selectedProvider.icon}</span>
              <div className="text-left">
                <div className="font-medium text-sm">
                  {selectedProvider.name}
                </div>
                <div className="text-xs text-gray-400">
                  {selectedProvider.description}
                </div>
              </div>
            </>
          ) : (
            <span className="text-gray-400 text-sm">Select cloud provider</span>
          )}
        </div>
        <ChevronDown
          className={`w-4 h-4 text-gray-400 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-gray-900 border border-gray-700 rounded-lg shadow-lg z-50 max-h-80 overflow-hidden">
          {/* Search */}
          <div className="p-3 border-b border-gray-700">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search providers..."
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>
          </div>

          {/* Provider List */}
          <div className="max-h-60 overflow-y-auto">
            {filteredProviders.length > 0 ? (
              filteredProviders.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => handleProviderSelect(provider)}
                  disabled={!provider.isEnabled}
                  className={`w-full flex items-center gap-3 p-3 text-left transition-colors ${
                    provider.isEnabled
                      ? "text-white hover:bg-gray-800 cursor-pointer"
                      : "text-gray-500 cursor-not-allowed"
                  }`}
                >
                  <div className="flex items-center gap-3 flex-1">
                    <span className="text-xl">{provider.icon}</span>
                    <div className="flex-1">
                      <div className="font-medium text-sm">{provider.name}</div>
                      <div className="text-xs text-gray-400">
                        {provider.description}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {!provider.isEnabled && (
                      <span className="text-xs bg-gray-700 text-gray-400 px-2 py-1 rounded">
                        Coming Soon
                      </span>
                    )}
                    {selectedProvider?.id === provider.id && (
                      <Check className="w-4 h-4 text-blue-500" />
                    )}
                  </div>
                </button>
              ))
            ) : (
              <div className="p-3 text-gray-400 text-center text-sm">
                No providers found
              </div>
            )}
          </div>
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
      )}
    </div>
  );
};
