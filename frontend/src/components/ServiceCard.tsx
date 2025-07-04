import { Trash2 } from "lucide-react";

// Service Management Component
export const ServiceCard = ({ service, onDelete }: any) => {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-all">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="text-white font-medium">{service.name}</h3>
          <p className="text-gray-400 text-sm mt-1">
            Added on {new Date(service.addedAt).toLocaleDateString()}
          </p>
        </div>
        <button
          onClick={() => onDelete(service.id)}
          className="text-gray-400 hover:text-red-400 transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
