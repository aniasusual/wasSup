import { useState } from "react";
import axios from "axios";
import toast from "react-hot-toast";

// Configure axios defaults
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL;

// Login Component
export const Login = () => {
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    try {
      const response = await axios.get("/api/v1/auth/login");
      window.location.href = response.data.auth_url;
    } catch (error: any) {
      let errorMessage = "Failed to initiate login";
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      toast.error(errorMessage);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden">
      {/* Animated background grid */}
      <div className="absolute inset-0 opacity-50">
        <div className="absolute inset-0 bg-grid"></div>
      </div>

      {/* Animated gradient orbs */}
      <div className="absolute top-0 -left-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
      <div className="absolute bottom-0 right-0 w-80 h-80 bg-cyan-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
      <div className="absolute -bottom-40 left-20 w-80 h-80 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>

      <div className="relative z-10 bg-slate-900/80 backdrop-blur-xl p-10 rounded-3xl shadow-2xl max-w-lg w-full border border-slate-800">
        {/* Logo section with animated icon */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="w-24 h-24 bg-gradient-to-br from-cyan-500 via-blue-500 to-purple-600 rounded-3xl flex items-center justify-center shadow-2xl animate-pulse-slow">
              {/* Hand wave emoji-style icon */}
              <svg
                className="w-14 h-14 text-white"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M7.03 4.95L3.49 8.49c-3.32 3.32-3.32 8.7 0 12.02s8.7 3.32 12.02 0l6.01-6.01a2.517 2.517 0 00-.39-3.86l.39-.39c.97-.97.97-2.56 0-3.54-.16-.16-.35-.3-.54-.41a2.497 2.497 0 00-3.72-3.05 2.517 2.517 0 00-3.88-.42l-2.51 2.51a2.493 2.493 0 00-3.84-.39zm1.41 1.42c.2-.2.51-.2.71 0 .2.2.2.51 0 .71l-3.18 3.18a3 3 0 010 4.24l1.41 1.41a5.004 5.004 0 001.12-5.36l6.3-6.3c.2-.2.51-.2.71 0s.2.51 0 .71l-4.6 4.6 1.41 1.41 6.01-6.01c.2-.2.51-.2.71 0 .2.2.2.51 0 .71l-6.01 6.01 1.41 1.41 4.95-4.95c.2-.2.51-.2.71 0 .2.2.2.51 0 .71l-5.66 5.66 1.41 1.41 3.54-3.54c.2-.2.51-.2.71 0 .2.2.2.51 0 .71l-6 6.01c-2.54 2.54-6.65 2.54-9.19 0s-2.54-6.65 0-9.19l3.53-3.54zM8.44 6.37c.2-.2.51-.2.71 0s.2.51 0 .71l-3.18 3.18a3 3 0 010 4.24l1.41 1.41a5.004 5.004 0 001.12-5.36l.52-.52-1.41-1.41-.73.73z" />
              </svg>
            </div>
            <div className="absolute -top-1 -right-1 w-6 h-6 bg-green-400 rounded-full animate-ping"></div>
            <div className="absolute -top-1 -right-1 w-6 h-6 bg-green-400 rounded-full"></div>
          </div>
        </div>

        <h1 className="text-4xl font-bold mb-3 text-center text-white">
          Recce
        </h1>

        <p className="text-cyan-400 text-center mb-2 text-lg font-medium">
          Your AI Log Detective
        </p>

        <p className="text-slate-400 text-center mb-8 text-sm">
          Reconnaissance of the logs
        </p>

        {/* How it works section */}
        <div className="bg-slate-800/50 rounded-xl p-6 mb-8 border border-slate-700">
          <h3 className="text-white font-semibold mb-4 flex items-center">
            <svg
              className="w-5 h-5 mr-2 text-cyan-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            How it works
          </h3>

          <div className="space-y-3 text-sm">
            <div className="flex items-start">
              <span className="text-cyan-400 font-bold mr-2">1.</span>
              <span className="text-slate-300">
                Select your services & add filters:{" "}
                <span className="text-slate-400 italic">
                  time range, severity, service names
                </span>
              </span>
            </div>
            <div className="flex items-start">
              <span className="text-purple-400 font-bold mr-2">2.</span>
              <span className="text-slate-300">
                Tell the chatbot your problem:{" "}
                <span className="text-slate-400 italic">
                  "User can't push to GitHub"
                </span>
              </span>
            </div>
            <div className="flex items-start">
              <span className="text-blue-400 font-bold mr-2">3.</span>
              <span className="text-slate-300">
                AI analyzes logs across all your GCP services: Cloud Run, GKE,
                Cloud Functions, etc.
              </span>
            </div>
            <div className="flex items-start">
              <span className="text-green-400 font-bold mr-2">4.</span>
              <span className="text-slate-300">
                Get instant root cause analysis with relevant logs from each
                service
              </span>
            </div>
          </div>

          <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
            <div className="flex items-start">
              <svg
                className="w-5 h-5 text-yellow-400 mr-2 flex-shrink-0 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="text-xs">
                <p className="text-yellow-400 font-medium">Pro tip:</p>
                <p className="text-slate-400">
                  Better filters = Faster response & more accurate results. Use
                  specific time ranges and service filters to optimize
                  performance.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Service icons */}
        <div className="flex justify-center gap-4 mb-8">
          <div className="text-slate-500 text-xs text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <span className="text-green-400">●</span>
              <span className="text-slate-300 font-medium">
                Currently Supporting:
              </span>
              <span className="text-cyan-400 font-semibold">GCP Logs</span>
            </div>
            <div className="text-slate-600">
              AWS CloudWatch • Azure Monitor • Datadog • More coming soon
            </div>
          </div>
        </div>

        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 text-white py-4 px-6 rounded-xl font-medium hover:from-cyan-500 hover:to-blue-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] shadow-xl hover:shadow-cyan-500/25"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Connecting to Google...
            </span>
          ) : (
            <span className="flex items-center justify-center">
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Start talking to your logs
            </span>
          )}
        </button>

        <p className="text-slate-600 text-xs text-center mt-6">
          Start with GCP • Multi-cloud support launching soon
        </p>
      </div>

      <style>{`
        @keyframes blob {
          0% {
            transform: translate(0px, 0px) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
          100% {
            transform: translate(0px, 0px) scale(1);
          }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        @keyframes pulse-slow {
          0%,
          100% {
            opacity: 1;
          }
          50% {
            opacity: 0.8;
          }
        }
        .animate-pulse-slow {
          animation: pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        .bg-grid {
          background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cdefs%3E%3Cpattern id='grid' width='60' height='60' patternUnits='userSpaceOnUse'%3E%3Cpath d='M 60 0 L 0 0 0 60' fill='none' stroke='rgba(255,255,255,0.03)' stroke-width='1'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100%25' height='100%25' fill='url(%23grid)'/%3E%3C/svg%3E");
        }
      `}</style>
    </div>
  );
};
