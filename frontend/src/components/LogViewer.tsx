import React, { useState } from "react";
import { ChevronDown, ChevronRight, Copy, Search, Filter } from "lucide-react";
import { LogEntry } from "./LogEntry";

export default function LogViewer({ sampleLogs }: any) {
  const [logs, setLogs] = useState(sampleLogs);
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");

  const filteredLogs = logs.filter((log: any) => {
    const matchesSearch =
      searchTerm === "" ||
      JSON.stringify(log).toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverity =
      severityFilter === "all" ||
      log.severity?.toLowerCase() === severityFilter.toLowerCase();
    return matchesSearch && matchesSeverity;
  });

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      {/* Log Entries */}
      <div className="space-y-4 h-[72vh] overflow-y-auto pr-2">
        {filteredLogs.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            No logs found matching your criteria
          </div>
        ) : (
          filteredLogs.map((log: any) => <LogEntry key={log.id} log={log} />)
        )}
      </div>
    </div>
  );
}
