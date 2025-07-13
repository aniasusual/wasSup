import { useEffect, useState } from "react";
import { useAuth } from "../contexts/Auth";

// Auth Success Component
export const AuthSuccess = () => {
  const { login, isAuthenticated } = useAuth();
  const [error, setError] = useState<any>(null);

  useEffect(() => {
    // If already authenticated, redirect to home
    if (isAuthenticated) {
      window.history.replaceState({}, document.title, "/");
      return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token");

    if (token) {
      login(token);
      window.history.replaceState({}, document.title, "/");
    } else {
      setError("No token received");
    }
  }, [login, isAuthenticated]);

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  return <div>Authenticating...</div>;
};
