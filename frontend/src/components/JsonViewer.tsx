import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

export const JsonViewer = ({ data, level = 0 }: any) => {
  const [expandedKeys, setExpandedKeys] = useState(new Set());

  const toggleExpand = (key: any) => {
    const newExpanded = new Set(expandedKeys);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedKeys(newExpanded);
  };

  if (data === null) return <span className="text-gray-500">null</span>;
  if (data === undefined)
    return <span className="text-gray-500">undefined</span>;

  if (typeof data !== "object") {
    const valueClass =
      typeof data === "string"
        ? "text-green-400"
        : typeof data === "number"
        ? "text-blue-400"
        : typeof data === "boolean"
        ? "text-purple-400"
        : "text-gray-300";
    return <span className={valueClass}>{JSON.stringify(data)}</span>;
  }

  const isArray = Array.isArray(data);
  const entries = isArray
    ? data.map((item, index) => [index, item])
    : Object.entries(data);

  return (
    <div className={level > 0 ? "ml-4" : ""}>
      <span className="text-gray-500">{isArray ? "[" : "{"}</span>
      <div className="ml-2">
        {entries.map(([key, value]) => {
          const keyStr = `${level}-${key}`;
          const isObject = value && typeof value === "object";
          const isExpanded = expandedKeys.has(keyStr);

          return (
            <div key={keyStr} className="py-1">
              <div className="flex items-start">
                {isObject && (
                  <button
                    onClick={() => toggleExpand(keyStr)}
                    className="text-gray-400 hover:text-gray-200 mr-1 mt-0.5"
                  >
                    {isExpanded ? (
                      <ChevronDown size={14} />
                    ) : (
                      <ChevronRight size={14} />
                    )}
                  </button>
                )}
                <span className="text-blue-300 font-medium">
                  {isArray ? key : `"${key}"`}:
                </span>
                <span className="ml-2">
                  {isObject ? (
                    <div>
                      <span className="text-gray-500">
                        {Array.isArray(value)
                          ? `[${value.length}]`
                          : `{${Object.keys(value).length}}`}
                      </span>
                      {isExpanded && (
                        <JsonViewer data={value} level={level + 1} />
                      )}
                    </div>
                  ) : (
                    <JsonViewer data={value} level={level + 1} />
                  )}
                </span>
              </div>
            </div>
          );
        })}
      </div>
      <span className="text-gray-500">{isArray ? "]" : "}"}</span>
    </div>
  );
};
