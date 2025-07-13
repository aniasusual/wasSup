import { useState } from "react";
import { Plus, Search } from "lucide-react";
import { ServiceCard } from "../components/ServiceCard";
import { ServiceSelector } from "../components/ServiceSelector";
import { TimeRangeSelector } from "../components/TimeRangeSelector";
import { Chatbot } from "../components/Chatbot";
import { AddServiceModal } from "../components/AddServiceModal";
import LogViewer from "../components/LogViewer";
import { ServiceTabs } from "../components/ServiceTabs";

export const Home = () => {
  const [services, setServices] = useState<any[]>([]);
  const [selectedServices, setSelectedServices] = useState<any[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [timeRange, setTimeRange] = useState("1h");
  const [searchQuery, setSearchQuery] = useState("");
  const [logs, setLogs] = useState([
    {
      id: "1",
      timestamp: "2024-01-15T10:30:45.123Z",
      severity: "ERROR",
      resource: {
        type: "gce_instance",
        labels: {
          instance_id: "1234567890123456789",
          zone: "us-central1-a",
        },
      },
      jsonPayload: {
        message: "Database connection failed",
        error: {
          code: "ECONNREFUSED",
          errno: -61,
          syscall: "connect",
          address: "10.0.0.1",
          port: 5432,
        },
        stack:
          "Error: Database connection failed\n    at Connection.connect (/app/db.js:45:12)\n    at processTicksAndRejections (node:internal/process/task_queues:96:5)",
      },
      labels: {
        service: "web-server",
        version: "1.2.3",
      },
    },
    {
      id: "2",
      timestamp: "2024-01-15T10:29:30.456Z",
      severity: "INFO",
      resource: {
        type: "k8s_container",
        labels: {
          cluster_name: "production-cluster",
          namespace_name: "default",
          pod_name: "web-app-7d4b9c8f6d-xyz12",
        },
      },
      textPayload: "User authentication successful for user ID: 12345",
      labels: {
        service: "auth-service",
        version: "2.1.0",
      },
    },
    {
      id: "3",
      timestamp: "2024-01-15T10:28:15.789Z",
      severity: "WARNING",
      resource: {
        type: "cloud_function",
        labels: {
          function_name: "process-webhook",
          region: "us-central1",
        },
      },
      jsonPayload: {
        message: "Rate limit approaching",
        metrics: {
          requests_per_minute: 850,
          limit: 1000,
          usage_percentage: 85,
        },
        recommendation: "Consider implementing request queuing",
      },
      httpRequest: {
        requestMethod: "POST",
        requestUrl: "https://api.example.com/webhook",
        status: 200,
        responseSize: "1024",
        userAgent: "Mozilla/5.0 (compatible; Webhook/1.0)",
      },
    },
  ]);

  const handleAddService = (service: any) => {
    setServices([...services, service]);
  };

  const handleDeleteService = (serviceId: any) => {
    setServices(services.filter((s) => s.id !== serviceId));
    setSelectedServices((prev) =>
      prev.some((s) => s.id === serviceId)
        ? prev.filter((s) => s.id !== serviceId)
        : [...prev, services.find((s) => s.id === serviceId)]
    );
  };

  const toggleServiceSelection = (serviceId: string) => {
    setSelectedServices((prev) =>
      prev.some((s) => s.id === serviceId)
        ? prev.filter((s) => s.id !== serviceId)
        : [...prev, services.find((s) => s.id === serviceId)]
    );
  };

  return (
    <div className="bg-black min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">wasSUP</h1>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              Add Service
            </button>
          </div>
        </div>
      </header>

      {/* Services Section */}
      {services.length > 0 && (
        <section className="container mx-auto px-4 py-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            Configured Services
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {services.map((service) => (
              <ServiceCard
                key={service.id}
                service={service}
                onDelete={handleDeleteService}
              />
            ))}
          </div>
        </section>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 flex-grow">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Logs Section */}
          <div className="lg:col-span-3 space-y-6">
            {/* Filters */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <div className="space-y-4">
                {/* Service Selector */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Select Services
                  </label>
                  <ServiceSelector
                    services={services}
                    selectedServices={selectedServices}
                    onToggle={toggleServiceSelection}
                  />
                </div>

                {/* Time Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Time Range
                  </label>
                  <TimeRangeSelector
                    value={timeRange}
                    onChange={setTimeRange}
                  />
                </div>

                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search logs..."
                    className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Logs Viewer */}
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <ServiceTabs
                selectedServices={selectedServices}
                logs={logs}
                setLogs={setLogs}
              />
              <div className="mt-4 max-h-[60vh] overflow-y-auto">
                <LogViewer sampleLogs={logs} />
              </div>
            </div>
          </div>

          {/* Chatbot Section */}
          <div className="lg:col-span-2">
            <div className="bg-gray-900 border border-gray-800 rounded-lg h-[80vh] lg:sticky lg:top-4 overflow-hidden">
              <Chatbot selectedServices={selectedServices} />
            </div>
          </div>
        </div>
      </main>

      {/* Add Service Modal */}
      <AddServiceModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddService}
      />
    </div>
  );
};

export default Home;
