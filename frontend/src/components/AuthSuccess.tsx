import { useEffect, useState } from "react";
import { useAuth } from "../contexts/Auth";
import toast from "react-hot-toast";

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
    const accessToken = urlParams.get("accessToken");

    if (token && accessToken) {
      try {
        login(token, accessToken);
        window.history.replaceState({}, document.title, "/");
        toast.success("Successfully authenticated!");
      } catch (error) {
        console.error("Authentication error:", error);
        setError("Failed to authenticate");
        toast.error(
          `Authentication failed: ${
            error instanceof Error ? error.message : String(error)
          }. Please try logging in again.`
        );
      }
    } else {
      setError("No token received");
      toast.error(
        "No authentication token received from Google. Please try logging in again."
      );
    }
  }, [login, isAuthenticated]);

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  return <div>Authenticating...</div>;
};
