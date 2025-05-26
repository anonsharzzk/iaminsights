import React, { useState } from "react";
import "./App.css";
import { AuthProvider, useAuth } from "./components/AuthContext";
import LandingPage from "./components/LandingPage";
import LoginPage from "./components/LoginPage";
import UserManagement from "./components/UserManagement";
import SettingsPage from "./components/SettingsPage";
import CloudAccessVisualizer from "./components/CloudAccessVisualizer";
import { Shield } from "lucide-react";

const App = () => {
  const [showLandingPage, setShowLandingPage] = useState(true);

  if (showLandingPage) {
    return <LandingPage onLoginClick={() => setShowLandingPage(false)} />;
  }

  return (
    <AuthProvider>
      <AuthenticatedAppContent />
    </AuthProvider>
  );
};

const AuthenticatedAppContent = () => {
  const { user, isAuthenticated } = useAuth();
  const [activeView, setActiveView] = useState("visualizer");

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const renderContent = () => {
    switch (activeView) {
      case "visualizer":
        return <CloudAccessVisualizer />;
      case "users":
        return <UserManagement />;
      case "settings":
        return <SettingsPage />;
      default:
        return <CloudAccessVisualizer />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Navigation */}
      <nav className="bg-slate-800/80 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveView("visualizer")}>
                <Shield className="w-8 h-8 text-blue-400" />
                <h1 className="text-2xl font-bold text-white">Cloud Access Visualizer</h1>
              </div>
              <div className="hidden md:flex items-center space-x-6">
                <button
                  onClick={() => setActiveView("visualizer")}
                  className={`text-sm font-medium ${activeView === "visualizer" ? "text-blue-400" : "text-slate-300 hover:text-white"}`}
                >
                  Visualizer
                </button>
                {user?.isAdmin && (
                  <button
                    onClick={() => setActiveView("users")}
                    className={`text-sm font-medium ${activeView === "users" ? "text-blue-400" : "text-slate-300 hover:text-white"}`}
                  >
                    User Management
                  </button>
                )}
                <button
                  onClick={() => setActiveView("settings")}
                  className={`text-sm font-medium ${activeView === "settings" ? "text-blue-400" : "text-slate-300 hover:text-white"}`}
                >
                  Settings
                </button>
              </div>
            </div>
            <div className="text-sm text-slate-300">
              {user?.email}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main>
        {renderContent()}
      </main>
    </div>
  );
};

export default App;