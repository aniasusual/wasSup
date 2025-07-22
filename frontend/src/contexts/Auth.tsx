import { useState, useEffect, createContext, useContext } from "react";
import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

// Configure axios defaults
axios.defaults.baseURL = API_BASE_URL;

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
    } catch (error) {
      console.error("Logout error:", error);
    }
    localStorage.removeItem("token");
    setToken(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider
      value={{ token, accesstoken, isAuthenticated, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
