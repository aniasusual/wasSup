import { useState } from "react";
import { ChevronDown } from "lucide-react";

export const ServiceSelector = ({
  services,
  selectedServices,
  onToggle,
}: any) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white flex items-center justify-between hover:bg-gray-750 transition-colors"
      >
        <span className="text-sm">
          {selectedServices.length === 0
            ? "Select services"
            : `${selectedServices.length} service${
                selectedServices.length > 1 ? "s" : ""
              } selected`}
        </span>
        <ChevronDown
          className={`w-4 h-4 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute z-10 w-full mt-2 bg-gray-800 border border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {services.map((service: any) => (
            <label
              key={service.id}
              className="flex items-center px-4 py-2 hover:bg-gray-700 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedServices.some((s: any) => s.id === service.id)}
                onChange={() => onToggle(service.id)}
                className="mr-3 rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500"
              />
              <span className="text-white text-sm">{service.name}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
};
