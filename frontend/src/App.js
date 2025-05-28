import React, { useState } from "react";
import "./App.css";
import { AuthProvider, useAuth } from "./components/AuthContext";
import LandingPage from "./components/LandingPage";
import LoginPage from "./components/LoginPage";
import SignupPage from "./components/SignupPage";
import UserManagement from "./components/UserManagement";
import SettingsPage from "./components/SettingsPage";
import CloudAccessVisualizer from "./components/CloudAccessVisualizer";
import { Shield, Users, Settings, LogOut, Menu, X } from "lucide-react";

const AuthenticatedApp = () => {
  const { user, logout, isAdmin } = useAuth();
  const [currentView, setCurrentView] = useState("visualizer");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { id: "visualizer", name: "Access Visualizer", icon: Shield, available: true },
    { id: "users", name: "User Management", icon: Users, available: isAdmin },
    { id: "settings", name: "Settings", icon: Settings, available: true },
  ];

  const renderCurrentView = () => {
    switch (currentView) {
      case "visualizer":
        return <CloudAccessVisualizer />;
      case "users":
        return isAdmin ? <UserManagement /> : <div className="text-center text-slate-400">Access Denied</div>;
      case "settings":
        return <SettingsPage />;
      default:
        return <CloudAccessVisualizer />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="bg-slate-800/80 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-blue-400" />
              <h1 className="text-xl font-bold text-white">Cloud Access Visualizer</h1>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-8">
              {navigation.filter(item => item.available).map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentView(item.id)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                      currentView === item.id
                        ? "bg-blue-600 text-white"
                        : "text-slate-300 hover:bg-slate-700 hover:text-white"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </button>
                );
              })}
            </nav>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <div className="hidden md:block text-right">
                <p className="text-white text-sm font-medium">{user?.email}</p>
                <p className="text-slate-400 text-xs capitalize">{user?.role}</p>
              </div>
              <button
                onClick={logout}
                className="flex items-center space-x-2 px-3 py-2 text-slate-300 hover:text-white hover:bg-slate-700 rounded-md transition-colors duration-200"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden md:inline">Logout</span>
              </button>
              
              {/* Mobile menu button */}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 text-slate-300 hover:text-white hover:bg-slate-700 rounded-md"
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {sidebarOpen && (
          <div className="md:hidden bg-slate-800 border-t border-slate-700">
            <div className="px-4 py-2 space-y-1">
              <div className="py-2 border-b border-slate-700">
                <p className="text-white text-sm font-medium">{user?.email}</p>
                <p className="text-slate-400 text-xs capitalize">{user?.role}</p>
              </div>
              {navigation.filter(item => item.available).map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setCurrentView(item.id);
                      setSidebarOpen(false);
                    }}
                    className={`flex items-center space-x-2 w-full px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                      currentView === item.id
                        ? "bg-blue-600 text-white"
                        : "text-slate-300 hover:bg-slate-700 hover:text-white"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderCurrentView()}
      </main>
    </div>
  );
};

const App = () => {
  const [showLandingPage, setShowLandingPage] = useState(true);
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);

  const handleLoginClick = () => {
    setShowLandingPage(false);
    setShowLogin(true);
    setShowSignup(false);
  };

  const handleSignupClick = () => {
    setShowLandingPage(false);
    setShowLogin(false);
    setShowSignup(true);
  };

  const handleBackToLanding = () => {
    setShowLogin(false);
    setShowSignup(false);
    setShowLandingPage(true);
  };

  const handleBackToLogin = () => {
    setShowSignup(false);
    setShowLogin(true);
  };

  const handleSignupSuccess = (userData) => {
    // Show success message and redirect to login
    console.log("Signup successful:", userData);
    setShowSignup(false);
    setShowLogin(true);
  };

  if (showLandingPage) {
    return <LandingPage onLoginClick={handleLoginClick} />;
  }

  if (showSignup) {
    return (
      <SignupPage 
        onBack={handleBackToLogin}
        onSignupSuccess={handleSignupSuccess}
      />
    );
  }

  return (
    <AuthProvider>
      <AppContent 
        showLogin={showLogin}
        onBackToLanding={handleBackToLanding}
        onShowSignup={handleSignupClick}
      />
    </AuthProvider>
  );
};

const AppContent = ({ showLogin, onBackToLanding, onShowSignup }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-slate-300">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage onBack={onBackToLanding} onShowSignup={onShowSignup} />;
  }

  return <AuthenticatedApp />;
};

export default App;