import { useState, useEffect, createContext, useContext } from "react";
import axios from "axios";
import toast from "react-hot-toast";

const API_BASE_URL = "http://localhost:8000";

// Configure axios defaults
axios.defaults.baseURL = API_BASE_URL;

// Global axios interceptor for authentication errors
let authContext: any = null;

// Function to set auth context reference
export const setAuthContext = (context: any) => {
  authContext = context;
};

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      // Use forceLogout if available, otherwise clear tokens manually
      if (authContext?.forceLogout) {
        authContext.forceLogout("Authentication token expired or invalid");
      } else {
        localStorage.removeItem("token");
        localStorage.removeItem("accessToken");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

const AuthContext = createContext<any>(null);

export const AuthProvider = ({ children }: any) => {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [accesstoken, setaccesstoken] = useState(
    localStorage.getItem("accessToken")
  );

  const [isAuthenticated, setIsAuthenticated] = useState(!!token);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common["Authorization"];
    }
  }, [token, accesstoken]);

  const login = (token: any, accessToken: any) => {
    localStorage.setItem("token", token);
    localStorage.setItem("accessToken", accessToken);
    setToken(token);
    setaccesstoken(accessToken);
    setIsAuthenticated(true);
  };

  const logout = async () => {
    try {
      await axios.get("/auth/logout");
      toast.success("Successfully logged out");
    } catch (error) {
      console.error("Logout error:", error);
      toast.error(
        `Failed to logout properly: ${
          error instanceof Error ? error.message : String(error)
        }. You have been logged out locally.`
      );
    }
    localStorage.removeItem("token");
    localStorage.removeItem("accessToken");
    setToken(null);
    setaccesstoken(null);
    setIsAuthenticated(false);
  };

  // Automatic logout for token-related issues
  const forceLogout = (reason: string) => {
    console.log(`Force logout: ${reason}`);
    localStorage.removeItem("token");
    localStorage.removeItem("accessToken");
    setToken(null);
    setaccesstoken(null);
    setIsAuthenticated(false);
    toast.error(`Session expired: ${reason}. Please log in again.`);
  };

  const contextValue = {
    token,
    accesstoken,
    isAuthenticated,
    login,
    logout,
    forceLogout,
  };

  // Set auth context reference for axios interceptor
  useEffect(() => {
    setAuthContext(contextValue);
  }, [contextValue]);

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
