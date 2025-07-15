import { useState } from "react";
import { ChevronDown, Search, Edit3, List, Building2 } from "lucide-react";

interface GCPProject {
  project_id: string;
  name: string;
}

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
    setIsOpen(false);
    setSearchQuery("");
  };

  const handleManualProjectSubmit = () => {
    if (manualProjectId.trim()) {
      setIsSettingProject(true);
      onProjectSelect(manualProjectId.trim());

      setTimeout(() => {
        setIsSettingProject(false);
        setIsManualInput(false);
        setManualProjectId("");
      }, 500);
    }
  };

  const handleToggleInputMode = () => {
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

  return (
    <div className={`relative ${className}`}>
      {/* Selected Project Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-gray-800 border border-gray-700 rounded-lg text-white hover:bg-gray-700 transition-colors"
      >
        <div className="flex items-center gap-3">
          {selectedProjectData ? (
            <>
              <span className="text-xl">
                <Building2 className="w-5 h-5" />
              </span>
              <div className="text-left">
                <div className="font-medium">{selectedProjectData.name}</div>
                <div className="text-sm text-gray-400">
                  {selectedProjectData.project_id}
                </div>
              </div>
            </>
          ) : (
            <span className="text-gray-400">Select a GCP Project</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleToggleInputMode();
            }}
            className="flex items-center space-x-1 text-xs text-gray-400 hover:text-gray-300 transition-colors duration-200"
            title={
              isManualInput ? "Switch to dropdown" : "Enter project ID manually"
            }
          >
            {isManualInput ? (
              <>
                <List className="w-3 h-3" />
                <span>List</span>
              </>
            ) : (
              <>
                <Edit3 className="w-3 h-3" />
                <span>Manual</span>
              </>
            )}
          </button>
          <ChevronDown
            className={`w-5 h-5 text-gray-400 transition-transform ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </div>
      </button>

      {/* Manual Input Mode */}
      {isManualInput && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-gray-900 border border-gray-700 rounded-lg shadow-lg z-50 p-3">
          <div className="space-y-3">
            <input
              type="text"
              value={manualProjectId}
              onChange={(e) => setManualProjectId(e.target.value)}
              placeholder="Enter project ID (e.g., my-project-123)"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  handleManualProjectSubmit();
                }
              }}
            />
            <button
              onClick={handleManualProjectSubmit}
              disabled={!manualProjectId.trim() || isSettingProject}
              className="w-full px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSettingProject ? "Setting..." : "Set Project"}
            </button>
          </div>
        </div>
      )}

      {/* Dropdown */}
      {isOpen && !isManualInput && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-gray-900 border border-gray-700 rounded-lg shadow-lg z-50 max-h-96 overflow-hidden">
          {/* Search */}
          <div className="p-3 border-b border-gray-700">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search projects..."
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>
          </div>

          {/* Project List */}
          <div className="max-h-80 overflow-y-auto">
            <div className="p-2">
              {filteredProjects.map((project) => (
                <button
                  key={project.project_id}
                  onClick={() => handleProjectSelect(project.project_id)}
                  className="w-full flex items-center gap-3 p-3 text-left text-white hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <span className="text-xl">
                    <Building2 className="w-5 h-5" />
                  </span>
                  <div className="flex-1">
                    <div className="font-medium">{project.name}</div>
                    <div className="text-sm text-gray-400">
                      {project.project_id}
                    </div>
                  </div>
                  {project.project_id === selectedProject && (
                    <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                      Selected
                    </span>
                  )}
                </button>
              ))}
              {filteredProjects.length === 0 && (
                <div className="p-3 text-gray-400 text-center">
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
