import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider } from "./contexts/Auth";
import Home from "./pages/Home";
import { Login } from "./components/Login";
import { AuthSuccess } from "./components/AuthSuccess";
import { Toaster } from "react-hot-toast";
import { useAuth } from "./contexts/Auth";
import { useEffect, useState } from "react";
import "./App.css";

const AppContent = () => {
  const [path, setPath] = useState(window.location.pathname);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    const handleLocationChange = () => setPath(window.location.pathname);
    window.addEventListener("popstate", handleLocationChange);
    return () => window.removeEventListener("popstate", handleLocationChange);
  }, []);


  // Check if we're on the auth success page and have a token
  const urlParams = new URLSearchParams(window.location.search);
  const hasToken = urlParams.get("token");

  if (path === "/auth/success" && hasToken) {
    return <AuthSuccess />;
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/home" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster
          position="bottom-left"
          toastOptions={{
            duration: 4000,
            style: {
              background: "#1f2937",
              color: "#f9fafb",
              border: "1px solid #374151",
            },
            success: {
              style: {
                background: "#065f46",
                color: "#d1fae5",
                border: "1px solid #10b981",
              },
            },
            error: {
              style: {
                background: "#991b1b",
                color: "#fecaca",
                border: "1px solid #ef4444",
              },
            },
          }}
        />
      </div>
    </Router>
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
