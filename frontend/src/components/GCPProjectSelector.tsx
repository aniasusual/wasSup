import { useEffect, useMemo, useState } from "react";
import { ChevronDown, Search, Edit3, List, Building2, Clock } from "lucide-react";

interface GCPProject {
  project_id: string;
  name: string;
}

const HISTORY_STORAGE_KEY = "recce:gcpProjectHistory";
const HISTORY_LIMIT = 8;

interface GCPProjectSelectorProps {
  selectedProject: string;
  onProjectSelect: (projectId: string) => void;
  projects: GCPProject[];
  className?: string;
}

export const GCPProjectSelector = ({
  selectedProject,
  onProjectSelect,
  projects,
  className = "",
}: GCPProjectSelectorProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isManualInput, setIsManualInput] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [manualProjectId, setManualProjectId] = useState("");
  const [isSettingProject, setIsSettingProject] = useState(false);
  const [history, setHistory] = useState<string[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    try {
      const stored = window.localStorage.getItem(HISTORY_STORAGE_KEY);
      if (!stored) {
        return;
      }
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        const sanitized = parsed
          .filter((item): item is string => typeof item === "string" && item.trim().length > 0)
          .slice(0, HISTORY_LIMIT);
        if (sanitized.length > 0) {
          setHistory(sanitized);
        }
      }
    } catch (error) {
      console.error("Failed to load project history", error);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    try {
      if (history.length === 0) {
        window.localStorage.removeItem(HISTORY_STORAGE_KEY);
      } else {
        window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
      }
    } catch (error) {
      console.error("Failed to persist project history", error);
    }
  }, [history]);

  const addToHistory = (projectId: string) => {
    const trimmed = projectId.trim();
    if (!trimmed) {
      return;
    }
    setHistory((prev) => {
      const deduped = [trimmed, ...prev.filter((item) => item !== trimmed)];
      return deduped.slice(0, HISTORY_LIMIT);
    });
  };

  const clearHistory = () => {
    setHistory([]);
  };

  const historyMatches = useMemo(() => {
    if (!searchQuery.trim()) {
      return history;
    }
    const query = searchQuery.toLowerCase();
    return history.filter((projectId) => projectId.toLowerCase().includes(query));
  }, [history, searchQuery]);

  // Combine fetched projects with manually added ones
  const allProjects = [...projects];
  if (
    selectedProject &&
    !projects.find((p) => p.project_id === selectedProject)
  ) {
    allProjects.push({
      project_id: selectedProject,
      name: selectedProject,
    });
  }

  const filteredProjects = allProjects.filter(
    (project) =>
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.project_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleProjectSelect = (projectId: string) => {
    onProjectSelect(projectId);
    addToHistory(projectId);
    setIsOpen(false);
    setSearchQuery("");
  };

  const handleManualProjectSubmit = () => {
    if (manualProjectId.trim()) {
      setIsSettingProject(true);
      onProjectSelect(manualProjectId.trim());
      addToHistory(manualProjectId.trim());

      setTimeout(() => {
        setIsSettingProject(false);
        setIsManualInput(false);
        setManualProjectId("");
      }, 500);
    }
  };

  const handleToggleInputMode = () => {
    setIsOpen(false);
    setIsManualInput(!isManualInput);
    if (!isManualInput) {
      setManualProjectId(selectedProject);
    } else {
      setManualProjectId("");
    }
  };

  const selectedProjectData = allProjects.find(
    (p) => p.project_id === selectedProject
  );

  const toggleDropdown = () => setIsOpen((prev) => !prev);

  return (
    <div className={`relative ${className}`}>
      {/* Selected Project Display */}
      <div
        role="button"
        tabIndex={0}
        onClick={toggleDropdown}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            toggleDropdown();
          }
        }}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        className="w-full flex items-center justify-between p-3 bg-gradient-to-r from-gray-800 to-gray-900 border border-gray-700/50 rounded-xl text-white hover:bg-gradient-to-r hover:from-gray-700 hover:to-gray-800 transition-all duration-300 shadow-sm cursor-pointer"
      >
        <div className="flex items-center gap-4">
          {selectedProjectData ? (
            <>
              <span className="text-xl">
                <Building2 className="w-5 h-5 text-gray-300" />
              </span>
              <div className="text-left">
                <div className="font-semibold text-base">
                  {selectedProjectData.name}
                </div>
                <div className="text-xs text-gray-300 mt-0.5">
                  {selectedProjectData.project_id}
                </div>
              </div>
            </>
          ) : (
            <span className="text-gray-300 font-medium">
              Select a GCP Project
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleToggleInputMode();
            }}
            className="flex items-center gap-1 text-xs text-gray-300 hover:text-white transition-all duration-200"
            title={
              isManualInput ? "Switch to dropdown" : "Enter project ID manually"
            }
          >
            {isManualInput ? (
              <>
                <List className="w-4 h-4" />
                <span>List</span>
              </>
            ) : (
              <>
                <Edit3 className="w-4 h-4" />
                <span>Manual</span>
              </>
            )}
          </button>
          <ChevronDown
            className={`w-5 h-5 text-gray-300 transition-transform duration-300 ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </div>
      </div>

      {/* Manual Input Mode */}
      {isManualInput && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-gray-900 border border-gray-700/50 rounded-xl shadow-2xl z-50 p-4">
          <div className="space-y-3">
            <input
              type="text"
              value={manualProjectId}
              onChange={(e) => setManualProjectId(e.target.value)}
              placeholder="Enter project ID (e.g., my-project-123)"
              className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 text-sm font-medium"
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  handleManualProjectSubmit();
                }
              }}
            />
            <button
              onClick={handleManualProjectSubmit}
              disabled={!manualProjectId.trim() || isSettingProject}
              className="w-full px-4 py-2.5 text-sm font-semibold text-white bg-blue-600/80 hover:bg-blue-600 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
            >
              {isSettingProject ? "Setting..." : "Set Project"}
            </button>
          </div>
        </div>
      )}

      {/* Dropdown */}
      {isOpen && !isManualInput && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-gray-900 border border-gray-700/50 rounded-xl shadow-2xl z-50 max-h-[32rem] overflow-hidden">
          {/* Search */}
          <div className="p-4 border-b border-gray-700/50">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search projects..."
                className="w-full pl-10 pr-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 text-sm font-medium"
              />
            </div>
          </div>

          {/* Project List */}
          <div className="max-h-[28rem] overflow-y-auto custom-scrollbar">
            {historyMatches.length > 0 && (
              <div className="px-3 pt-3 pb-2 border-b border-gray-800/60">
                <div className="flex items-center justify-between text-[11px] uppercase tracking-wide text-gray-500 mb-2">
                  <span className="inline-flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    Recent Projects
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      clearHistory();
                      setSearchQuery("");
                    }}
                    className="text-[11px] font-semibold text-gray-400 hover:text-red-300 transition-colors"
                  >
                    Clear History
                  </button>
                </div>
                <div className="space-y-1">
                  {historyMatches.map((projectId) => {
                    const matchedProject = allProjects.find(
                      (project) => project.project_id === projectId
                    );
                    const displayName = matchedProject?.name ?? projectId;

                    return (
                      <button
                        key={`history-${projectId}`}
                        onClick={() => handleProjectSelect(projectId)}
                        className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-white transition-colors hover:bg-gray-800/60"
                      >
                        <span className="text-xl">
                          <Building2 className="w-5 h-5 text-gray-300" />
                        </span>
                        <div className="flex-1">
                          <div className="font-semibold text-sm">{displayName}</div>
                          <div className="text-[11px] text-gray-400 mt-0.5">
                            {projectId}
                          </div>
                        </div>
                        {projectId === selectedProject && (
                          <span className="text-xs bg-blue-600/80 text-white px-2 py-1 rounded-lg font-medium">
                            Selected
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
            <div className="p-2">
              {filteredProjects.map((project) => (
                <button
                  key={project.project_id}
                  onClick={() => handleProjectSelect(project.project_id)}
                  className="w-full flex items-center gap-3 p-3 text-left text-white hover:bg-gray-800/50 rounded-lg transition-all duration-200"
                >
                  <span className="text-xl">
                    <Building2 className="w-5 h-5 text-gray-300" />
                  </span>
                  <div className="flex-1">
                    <div className="font-semibold text-sm">{project.name}</div>
                    <div className="text-xs text-gray-300 mt-0.5">
                      {project.project_id}
                    </div>
                  </div>
                  {project.project_id === selectedProject && (
                    <span className="text-xs bg-blue-600/80 text-white px-2 py-1 rounded-lg font-medium">
                      Selected
                    </span>
                  )}
                </button>
              ))}
              {filteredProjects.length === 0 && (
                <div className="p-3 text-gray-300 text-center text-sm">
                  No projects found
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Backdrop */}
      {(isOpen || isManualInput) && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setIsOpen(false);
            setIsManualInput(false);
          }}
        />
      )}
    </div>
  );
};
