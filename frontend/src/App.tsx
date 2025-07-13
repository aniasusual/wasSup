import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import "./App.css";
import Home from "./pages/Home";
import { useAuth } from "./contexts/Auth";
import { useEffect, useState } from "react";
import { AuthSuccess } from "./components/AuthSuccess";
import { Login } from "./components/Login";

const NotFound = () => (
  <div className="min-h-screen bg-black flex items-center justify-center">
    <div className="text-center">
      <h1 className="text-4xl font-bold text-white mb-4">
        404 - Page Not Found
      </h1>
      <p className="text-gray-400 mb-6">
        The page you're looking for doesn't exist.
      </p>
      <a href="/" className="text-blue-500 hover:text-blue-400 underline">
        Go back home
      </a>
    </div>
  </div>
);

function App() {
  const [path, setPath] = useState(window.location.pathname);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    const handleLocationChange = () => setPath(window.location.pathname);
    window.addEventListener("popstate", handleLocationChange);
    return () => window.removeEventListener("popstate", handleLocationChange);
  }, []);

  console.log("path", path);

  // Check if we're on the auth success page and have a token
  const urlParams = new URLSearchParams(window.location.search);
  const hasToken = urlParams.get("token");

  if (path === "/auth/success" && hasToken) {
    console.log("auth success with token");
    return <AuthSuccess />;
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;
