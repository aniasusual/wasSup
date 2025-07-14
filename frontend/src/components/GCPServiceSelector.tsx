import { useState } from "react";
import { ChevronDown, Search } from "lucide-react";
import type { GCPService } from "../types/gcp";
import { GCP_SERVICES, getServicesByCategory } from "../data/gcpServices";

interface GCPServiceSelectorProps {
  selectedService?: GCPService;
  onServiceSelect: (service: GCPService) => void;
  className?: string;
}

export const GCPServiceSelector = ({
  selectedService,
  onServiceSelect,
  className = "",
}: GCPServiceSelectorProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const servicesByCategory = getServicesByCategory();

  const filteredServices = GCP_SERVICES.filter(
    (service) =>
      service.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      service.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleServiceSelect = (service: GCPService) => {
    onServiceSelect(service);
    setIsOpen(false);
    setSearchQuery("");
  };

  return (
    <div className={`relative ${className}`}>
      {/* Selected Service Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-gray-800 border border-gray-700 rounded-lg text-white hover:bg-gray-700 transition-colors"
      >
        <div className="flex items-center gap-3">
          {selectedService ? (
            <>
              <span className="text-xl">{selectedService.icon}</span>
              <div className="text-left">
                <div className="font-medium">{selectedService.name}</div>
                <div className="text-sm text-gray-400 capitalize">
                  {selectedService.category}
                </div>
              </div>
            </>
          ) : (
            <span className="text-gray-400">Select a GCP Service</span>
          )}
        </div>
        <ChevronDown
          className={`w-5 h-5 text-gray-400 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-gray-900 border border-gray-700 rounded-lg shadow-lg z-50 max-h-96 overflow-hidden">
          {/* Search */}
          <div className="p-3 border-b border-gray-700">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search services..."
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>
          </div>

          {/* Service List */}
          <div className="max-h-80 overflow-y-auto">
            {searchQuery ? (
              // Search results
              <div className="p-2">
                {filteredServices.map((service) => (
                  <button
                    key={service.id}
                    onClick={() => handleServiceSelect(service)}
                    className="w-full flex items-center gap-3 p-3 text-left text-white hover:bg-gray-800 rounded-lg transition-colors"
                  >
                    <span className="text-xl">{service.icon}</span>
                    <div className="flex-1">
                      <div className="font-medium">{service.name}</div>
                      <div className="text-sm text-gray-400 capitalize">
                        {service.category}
                      </div>
                    </div>
                    {service.isDeploymentBased && (
                      <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                        Deployment-based
                      </span>
                    )}
                  </button>
                ))}
                {filteredServices.length === 0 && (
                  <div className="p-3 text-gray-400 text-center">
                    No services found
                  </div>
                )}
              </div>
            ) : (
              // Categorized view
              Object.entries(servicesByCategory).map(([category, services]) => (
                <div
                  key={category}
                  className="border-b border-gray-700 last:border-b-0"
                >
                  <div className="px-3 py-2 bg-gray-800 text-gray-300 text-sm font-medium capitalize">
                    {category}
                  </div>
                  {services.map((service) => (
                    <button
                      key={service.id}
                      onClick={() => handleServiceSelect(service)}
                      className="w-full flex items-center gap-3 p-3 text-left text-white hover:bg-gray-800 transition-colors"
                    >
                      <span className="text-xl">{service.icon}</span>
                      <div className="flex-1">
                        <div className="font-medium">{service.name}</div>
                        <div className="text-sm text-gray-400">
                          {service.isDeploymentBased
                            ? "Deployment-based"
                            : "Direct access"}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              ))
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
