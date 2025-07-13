import { useState } from "react";

export const ServiceTabs = ({ selectedServices, logs, setLogs }: any) => {
  if (selectedServices.length === 0) return null;
  const [activeTab, setActiveTab] = useState(selectedServices[0]?.id || null);

  const handleTabSelection = (serviceId: any) => {
    setActiveTab(serviceId);
    console.log("logs: ", logs);
    const filteredLogs = logs.filter((log: any) => log.serviceId === serviceId);
    setLogs(filteredLogs);
  };

  return (
    <div>
      {/* Header with subtle gradient */}
      <div className="">
        <div className="flex items-center justify-between">
          <h3 className="text-slate-200 font-semibold text-sm tracking-wide uppercase">
            Active Services
          </h3>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
            <span className="text-slate-400 text-xs font-medium">
              {selectedServices.length} service
              {selectedServices.length !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs Container */}
      <div className="p-6">
        <div className="relative">
          {/* Background glow effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-blue-500/10 rounded-lg blur-xl"></div>

          {/* Tabs */}
          {selectedServices.length == 0 ? (
            <h1>
              No services selected! Please select a service to see its logs.
            </h1>
          ) : (
            <div className="relative flex flex-wrap gap-3">
              {selectedServices.map((service: any, index: number) => {
                const isActive = activeTab === service.id;
                return (
                  <button
                    key={service.id}
                    onClick={() => handleTabSelection(service.id)}
                    className={`
                    group relative flex items-center gap-3 px-5 py-3 rounded-lg text-sm font-medium 
                    transition-all duration-300 ease-in-out transform hover:scale-105
                    ${
                      isActive
                        ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/25 border border-blue-500/50"
                        : "bg-slate-800/80 text-slate-300 border border-slate-700/50 hover:bg-slate-700/80 hover:border-slate-600/50 hover:text-slate-200"
                    }
                  `}
                  >
                    {/* Service Icon/Indicator */}
                    <div
                      className={`
                    w-2 h-2 rounded-full transition-all duration-300
                    ${
                      isActive
                        ? "bg-emerald-400 shadow-lg shadow-emerald-400/50 animate-pulse"
                        : "bg-slate-500 group-hover:bg-slate-400"
                    }
                  `}
                    ></div>

                    {/* Service Name */}
                    <span className="font-semibold tracking-wide">
                      {service.name}
                    </span>

                    {/* Service Type Badge */}
                    {service.type && (
                      <span
                        className={`
                        text-xs px-2 py-1 rounded-full font-medium transition-all duration-300
                        ${
                          isActive
                            ? "bg-blue-800/60 text-blue-100 border border-blue-600/30"
                            : "bg-slate-700/80 text-slate-300 border border-slate-600/50 group-hover:bg-slate-600/80"
                        }
                      `}
                      >
                        {service.type}
                      </span>
                    )}

                    {/* Active Indicator */}
                    {isActive && (
                      <div className="flex items-center gap-1">
                        <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></div>
                        <span className="text-xs text-emerald-400 font-medium">
                          ACTIVE
                        </span>
                      </div>
                    )}

                    {/* Hover glow effect */}
                    <div
                      className={`
                    absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300
                    ${
                      isActive
                        ? "bg-gradient-to-r from-blue-600/20 to-blue-700/20"
                        : "bg-slate-600/20"
                    }
                  `}
                    ></div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Bottom indicator line */}
        <div className="mt-4 h-px bg-gradient-to-r from-transparent via-slate-600/50 to-transparent"></div>
      </div>
    </div>
  );
};
