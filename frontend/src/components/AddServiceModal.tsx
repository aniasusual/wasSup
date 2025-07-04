import { useState } from "react";
import { Upload } from "lucide-react";

export const AddServiceModal = ({ isOpen, onClose, onAdd }: any) => {
  const [serviceName, setServiceName] = useState("");
  const [jsonKey, setJsonKey] = useState(null);
  const [error, setError] = useState("");

  const handleFileUpload = (e: any) => {
    const file = e.target.files[0];
    if (file && file.type === "application/json") {
      setJsonKey(file);
      setError("");
    } else {
      setError("Please upload a valid JSON file");
    }
  };

  const handleSubmit = () => {
    if (!serviceName || !jsonKey) {
      setError("Please provide both service name and JSON key");
      return;
    }

    onAdd({
      id: Date.now().toString(),
      name: serviceName,
      keyFile: jsonKey,
      addedAt: new Date().toISOString(),
    });

    setServiceName("");
    setJsonKey(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold text-white mb-4">
          Add New Service
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Service Name
            </label>
            <input
              type="text"
              value={serviceName}
              onChange={(e) => setServiceName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              placeholder="e.g., Production API"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              JSON Secret Key
            </label>
            <div className="border-2 border-dashed border-gray-700 rounded-lg p-4 text-center hover:border-gray-600 transition-colors">
              <input
                type="file"
                accept=".json"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-400">
                  {jsonKey ? jsonKey.name : "Click to upload JSON key file"}
                </p>
              </label>
            </div>
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Add Service
          </button>
        </div>
      </div>
    </div>
  );
};
