// import axios from "axios";
// import { AuthSuccess } from "../components/AuthSuccess";
// import { Login } from "../components/Login";
// import { useAuth } from "../contexts/Auth";

// const API_BASE_URL = "http://localhost:8000";

// // Configure axios defaults
// axios.defaults.baseURL = API_BASE_URL;

// // Logs Viewer Component
// const LogsViewer = () => {
//   const { logout } = useAuth();
//   const [logs, setLogs] = useState([]);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState(null);
//   const [projectId, setProjectId] = useState("");
//   const [filter, setFilter] = useState("");
//   const [pageSize, setPageSize] = useState(50);

//   const fetchLogs = async () => {
//     if (!projectId) {
//       setError("Please enter a project ID");
//       return;
//     }

//     setLoading(true);
//     setError(null);

//     try {
//       const response = await axios.post("/logs/query", {
//         project_id: projectId,
//         filter: filter || undefined,
//         page_size: pageSize,
//       });
//       setLogs(response.data);
//     } catch (error) {
//       setError(error.response?.data?.detail || "Failed to fetch logs");
//     } finally {
//       setLoading(false);
//     }
//   };

//   const getSeverityColor = (severity) => {
//     const colors = {
//       DEBUG: "text-gray-500",
//       INFO: "text-blue-500",
//       NOTICE: "text-green-500",
//       WARNING: "text-yellow-500",
//       ERROR: "text-red-500",
//       CRITICAL: "text-red-700",
//       ALERT: "text-red-900",
//       EMERGENCY: "text-red-900 font-bold",
//     };
//     return colors[severity] || "text-gray-700";
//   };

//   return (
//     <div className="min-h-screen bg-gray-100">
//       <nav className="bg-white shadow-sm px-6 py-4">
//         <div className="flex justify-between items-center">
//           <h1 className="text-xl font-semibold">GCP Logs Viewer</h1>
//           <button
//             onClick={logout}
//             className="text-gray-600 hover:text-gray-800 transition-colors"
//           >
//             Logout
//           </button>
//         </div>
//       </nav>

//       <div className="container mx-auto px-4 py-8">
//         <div className="bg-white rounded-lg shadow-md p-6 mb-6">
//           <h2 className="text-lg font-semibold mb-4">Query Logs</h2>

//           <div className="space-y-4">
//             <div>
//               <label className="block text-sm font-medium text-gray-700 mb-1">
//                 Project ID
//               </label>
//               <input
//                 type="text"
//                 value={projectId}
//                 onChange={(e) => setProjectId(e.target.value)}
//                 placeholder="your-gcp-project-id"
//                 className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
//               />
//             </div>

//             <div>
//               <label className="block text-sm font-medium text-gray-700 mb-1">
//                 Filter (optional)
//               </label>
//               <input
//                 type="text"
//                 value={filter}
//                 onChange={(e) => setFilter(e.target.value)}
//                 placeholder='severity="ERROR" OR resource.type="gce_instance"'
//                 className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
//               />
//               <p className="text-xs text-gray-500 mt-1">
//                 Use Cloud Logging filter syntax
//               </p>
//             </div>

//             <div>
//               <label className="block text-sm font-medium text-gray-700 mb-1">
//                 Page Size
//               </label>
//               <select
//                 value={pageSize}
//                 onChange={(e) => setPageSize(Number(e.target.value))}
//                 className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
//               >
//                 <option value={10}>10</option>
//                 <option value={25}>25</option>
//                 <option value={50}>50</option>
//                 <option value={100}>100</option>
//               </select>
//             </div>

//             <button
//               onClick={fetchLogs}
//               disabled={loading}
//               className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 disabled:bg-gray-400 transition-colors"
//             >
//               {loading ? "Fetching logs..." : "Fetch Logs"}
//             </button>
//           </div>

//           {error && (
//             <div className="mt-4 p-3 bg-red-100 text-red-700 rounded">
//               {error}
//             </div>
//           )}
//         </div>

//         {logs.length > 0 && (
//           <div className="bg-white rounded-lg shadow-md p-6">
//             <h2 className="text-lg font-semibold mb-4">
//               Logs ({logs.length} entries)
//             </h2>

//             <div className="space-y-3">
//               {logs.map((log) => (
//                 <div
//                   key={log.insertId}
//                   className="border rounded p-3 hover:bg-gray-50"
//                 >
//                   <div className="flex items-start justify-between mb-2">
//                     <span
//                       className={`font-medium ${getSeverityColor(
//                         log.severity
//                       )}`}
//                     >
//                       {log.severity}
//                     </span>
//                     <span className="text-sm text-gray-500">
//                       {new Date(log.timestamp).toLocaleString()}
//                     </span>
//                   </div>

//                   <div className="text-sm text-gray-800 mb-2">
//                     {log.message}
//                   </div>

//                   {log.resource && Object.keys(log.resource).length > 0 && (
//                     <details className="text-xs text-gray-600">
//                       <summary className="cursor-pointer hover:text-gray-800">
//                         Resource Details
//                       </summary>
//                       <pre className="mt-2 p-2 bg-gray-100 rounded overflow-x-auto">
//                         {JSON.stringify(log.resource, null, 2)}
//                       </pre>
//                     </details>
//                   )}
//                 </div>
//               ))}
//             </div>
//           </div>
//         )}
//       </div>
//     </div>
//   );
// };

// Main App Component
// export default function App() {
//   const [path, setPath] = useState(window.location.pathname);

//   useEffect(() => {
//     const handleLocationChange = () => setPath(window.location.pathname);
//     window.addEventListener("popstate", handleLocationChange);
//     return () => window.removeEventListener("popstate", handleLocationChange);
//   }, []);

//   return (
//     <AuthProvider>
//       <AppContent path={path} />
//     </AuthProvider>
//   );
// }

// export const AuthContent = ({ path }: any) => {
//   const { isAuthenticated } = useAuth();

//   if (path === "/auth/success") {
//     return <AuthSuccess />;
//   }

//   if (!isAuthenticated) {
//     return <Login />;
//   }

//   //   return <LogsViewer />;
// };
