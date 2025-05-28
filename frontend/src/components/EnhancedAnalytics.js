import React, { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "./AuthContext";
import { 
  Search, Users, Shield, BarChart3, Cloud, Server, Database, Key, 
  Download, RefreshCw, Filter, Eye, Settings, AlertTriangle, 
  CheckCircle, User, ChevronLeft, ChevronRight, TrendingUp,
  Target, Activity, Zap, FileText, XCircle, Info
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EnhancedAnalytics = () => {
  const { token, isAuthenticated } = useAuth();
  
  // Main state
  const [activeView, setActiveView] = useState("overview");
  const [loading, setLoading] = useState(false);
  
  // User analytics state
  const [users, setUsers] = useState([]);
  const [pagination, setPagination] = useState({});
  const [searchEmail, setSearchEmail] = useState("");
  const [selectedProvider, setSelectedProvider] = useState("");
  const [selectedRiskLevel, setSelectedRiskLevel] = useState("");
  const [sortBy, setSortBy] = useState("risk_score");
  const [sortOrder, setSortOrder] = useState("desc");
  const [currentPage, setCurrentPage] = useState(1);
  
  // Provider analytics state
  const [providerAnalytics, setProviderAnalytics] = useState({});
  const [selectedProviderDashboard, setSelectedProviderDashboard] = useState("aws");
  
  // Risk analysis state
  const [selectedUserRisk, setSelectedUserRisk] = useState(null);
  const [riskAnalysisModal, setRiskAnalysisModal] = useState(false);

  // Fetch paginated users with search and filters
  const fetchUsers = async (page = 1, resetPage = false) => {
    if (!isAuthenticated) {
      console.error("User not authenticated");
      return;
    }
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: resetPage ? 1 : page,
        page_size: 20,
        sort_by: sortBy,
        sort_order: sortOrder
      });
      
      if (searchEmail.trim()) params.append('search', searchEmail.trim());
      if (selectedProvider) params.append('provider', selectedProvider);
      if (selectedRiskLevel) params.append('risk_level', selectedRiskLevel);
      
      const response = await axios.get(`${API}/users/paginated?${params.toString()}`);
      setUsers(response.data.users);
      setPagination(response.data.pagination);
      
      if (resetPage) {
        setCurrentPage(1);
      } else {
        setCurrentPage(page);
      }
    } catch (error) {
      console.error("Error fetching users:", error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.error("Authentication error - token may be invalid");
      }
      setUsers([]);
      setPagination({});
    } finally {
      setLoading(false);
    }
  };

  // Fetch provider-specific analytics
  const fetchProviderAnalytics = async (provider) => {
    if (!isAuthenticated) {
      console.error("User not authenticated");
      return;
    }
    
    try {
      const response = await axios.get(`${API}/analytics/dashboard/${provider}`);
      setProviderAnalytics(prev => ({
        ...prev,
        [provider]: response.data
      }));
    } catch (error) {
      console.error(`Error fetching ${provider} analytics:`, error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.error("Authentication error - token may be invalid");
      }
    }
  };

  // Fetch detailed risk analysis for a user
  const fetchUserRiskAnalysis = async (userEmail) => {
    if (!isAuthenticated) {
      console.error("User not authenticated");
      return;
    }
    
    try {
      const response = await axios.get(`${API}/risk-analysis/${encodeURIComponent(userEmail)}`);
      setSelectedUserRisk(response.data);
      setRiskAnalysisModal(true);
    } catch (error) {
      console.error("Error fetching user risk analysis:", error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.error("Authentication error - token may be invalid");
      }
    }
  };

  // Handle dynamic search with debounce
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (activeView === "users") {
        fetchUsers(1, true);
      }
    }, 300);
    
    return () => clearTimeout(timeoutId);
  }, [searchEmail, selectedProvider, selectedRiskLevel, sortBy, sortOrder]);

  // Load data on component mount
  useEffect(() => {
    if (activeView === "users") {
      fetchUsers();
    } else if (activeView === "providers") {
      fetchProviderAnalytics(selectedProviderDashboard);
    }
  }, [activeView, selectedProviderDashboard]);

  const getRiskBadgeColor = (riskLevel) => {
    switch (riskLevel) {
      case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'high': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'low': return 'bg-green-500/20 text-green-400 border-green-500/30';
      default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  const getProviderIcon = (provider) => {
    switch (provider) {
      case 'aws': return '☁️';
      case 'gcp': return '🌩️';
      case 'azure': return '⭐';
      case 'okta': return '🔐';
      default: return '🌐';
    }
  };

  const clearFilters = () => {
    setSearchEmail("");
    setSelectedProvider("");
    setSelectedRiskLevel("");
    setSortBy("risk_score");
    setSortOrder("desc");
  };

  // Don't render if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="text-center py-12">
        <Shield className="w-16 h-16 mx-auto text-slate-400 mb-4" />
        <h3 className="text-xl font-semibold text-white mb-2">Authentication Required</h3>
        <p className="text-slate-400">Please log in to access enhanced analytics.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Navigation */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-white flex items-center">
            <BarChart3 className="w-8 h-8 mr-3" />
            Enhanced Security Analytics
          </h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setActiveView("overview")}
              className={`px-4 py-2 rounded-lg transition-colors duration-200 ${
                activeView === "overview" 
                  ? 'bg-blue-600 text-white' 
                  : 'text-slate-300 hover:bg-slate-700/50'
              }`}
            >
              <TrendingUp className="w-4 h-4 inline mr-2" />
              Overview
            </button>
            <button
              onClick={() => setActiveView("users")}
              className={`px-4 py-2 rounded-lg transition-colors duration-200 ${
                activeView === "users" 
                  ? 'bg-blue-600 text-white' 
                  : 'text-slate-300 hover:bg-slate-700/50'
              }`}
            >
              <Users className="w-4 h-4 inline mr-2" />
              Users
            </button>
            <button
              onClick={() => setActiveView("providers")}
              className={`px-4 py-2 rounded-lg transition-colors duration-200 ${
                activeView === "providers" 
                  ? 'bg-blue-600 text-white' 
                  : 'text-slate-300 hover:bg-slate-700/50'
              }`}
            >
              <Cloud className="w-4 h-4 inline mr-2" />
              Provider Dashboards
            </button>
          </div>
        </div>

        {/* Overview Tab */}
        {activeView === "overview" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                <Users className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-white">{pagination.total_users || "0"}</p>
                <p className="text-slate-300 text-sm">Total Users</p>
              </div>
              <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                <Shield className="w-8 h-8 text-orange-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-white">{users.filter(u => u.cross_provider_admin).length}</p>
                <p className="text-slate-300 text-sm">Cross-Provider Admins</p>
              </div>
              <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-white">{users.filter(u => u.privilege_escalation_count > 0).length}</p>
                <p className="text-slate-300 text-sm">Escalation Risks</p>
              </div>
              <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                <Activity className="w-8 h-8 text-green-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-white">{users.filter(u => u.risk_level === 'high' || u.risk_level === 'critical').length}</p>
                <p className="text-slate-300 text-sm">High Risk Users</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Risk Distribution */}
              <div className="bg-slate-700/30 rounded-lg p-6">
                <h4 className="text-lg font-semibold text-white mb-4">Risk Distribution</h4>
                <div className="space-y-3">
                  {['critical', 'high', 'medium', 'low'].map(level => {
                    const count = users.filter(u => u.risk_level === level).length;
                    return (
                      <div key={level} className="flex items-center justify-between">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getRiskBadgeColor(level)}`}>
                          {level.charAt(0).toUpperCase() + level.slice(1)} Risk
                        </span>
                        <span className="text-white font-bold">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Provider Distribution */}
              <div className="bg-slate-700/30 rounded-lg p-6">
                <h4 className="text-lg font-semibold text-white mb-4">Provider Access</h4>
                <div className="space-y-3">
                  {['aws', 'gcp', 'azure', 'okta'].map(provider => {
                    const count = users.filter(u => u.providers.includes(provider)).length;
                    return (
                      <div key={provider} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-xl">{getProviderIcon(provider)}</span>
                          <span className="text-slate-300">{provider.toUpperCase()}</span>
                        </div>
                        <span className="text-white font-bold">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeView === "users" && (
          <div className="space-y-6">
            {/* Search and Filters */}
            <div className="bg-slate-700/30 rounded-lg p-4">
              <div className="grid grid-cols-1 md:grid-cols-6 gap-4 items-end">
                {/* Dynamic Search */}
                <div className="md:col-span-2">
                  <label className="block text-slate-300 text-sm font-medium mb-2">Search Users</label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                    <input
                      type="text"
                      value={searchEmail}
                      onChange={(e) => setSearchEmail(e.target.value)}
                      placeholder="Type to search by email..."
                      className="w-full pl-10 pr-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {/* Provider Filter */}
                <div>
                  <label className="block text-slate-300 text-sm font-medium mb-2">Provider</label>
                  <select
                    value={selectedProvider}
                    onChange={(e) => setSelectedProvider(e.target.value)}
                    className="w-full bg-slate-800 text-white rounded-lg px-3 py-2 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Providers</option>
                    <option value="aws">AWS</option>
                    <option value="gcp">GCP</option>
                    <option value="azure">Azure</option>
                    <option value="okta">Okta</option>
                  </select>
                </div>

                {/* Risk Level Filter */}
                <div>
                  <label className="block text-slate-300 text-sm font-medium mb-2">Risk Level</label>
                  <select
                    value={selectedRiskLevel}
                    onChange={(e) => setSelectedRiskLevel(e.target.value)}
                    className="w-full bg-slate-800 text-white rounded-lg px-3 py-2 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Levels</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>

                {/* Sort Options */}
                <div>
                  <label className="block text-slate-300 text-sm font-medium mb-2">Sort By</label>
                  <select
                    value={`${sortBy}-${sortOrder}`}
                    onChange={(e) => {
                      const [field, order] = e.target.value.split('-');
                      setSortBy(field);
                      setSortOrder(order);
                    }}
                    className="w-full bg-slate-800 text-white rounded-lg px-3 py-2 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="risk_score-desc">Risk Score (High to Low)</option>
                    <option value="risk_score-asc">Risk Score (Low to High)</option>
                    <option value="user_email-asc">Email (A-Z)</option>
                    <option value="user_email-desc">Email (Z-A)</option>
                    <option value="total_resources-desc">Resources (Most)</option>
                    <option value="total_resources-asc">Resources (Least)</option>
                  </select>
                </div>

                {/* Clear Filters */}
                <div>
                  <button
                    onClick={clearFilters}
                    className="w-full bg-slate-600 hover:bg-slate-500 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Clear</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Users Table */}
            <div className="bg-slate-700/30 rounded-lg overflow-hidden">
              {loading ? (
                <div className="p-8 text-center text-slate-400">
                  <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin" />
                  <p>Loading users...</p>
                </div>
              ) : users.length === 0 ? (
                <div className="p-8 text-center text-slate-400">
                  <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>No users found matching your criteria</p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-slate-800">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">User</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Risk Score</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Providers</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Resources</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Admin Access</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Risks</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-600">
                        {users.map((user, index) => (
                          <tr key={index} className="hover:bg-slate-700/20">
                            <td className="px-6 py-4">
                              <div>
                                <p className="text-white font-medium">{user.user_name || "N/A"}</p>
                                <p className="text-blue-400 text-sm">{user.user_email}</p>
                                {user.is_service_account && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30 mt-1">
                                    Service Account
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center space-x-2">
                                <span className="text-white font-bold">{user.risk_score.toFixed(1)}</span>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getRiskBadgeColor(user.risk_level)}`}>
                                  {user.risk_level.charAt(0).toUpperCase() + user.risk_level.slice(1)}
                                </span>
                              </div>
                              <div className="text-xs text-slate-400 mt-1">
                                Confidence: {(user.confidence_score * 100).toFixed(0)}%
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex space-x-1">
                                {user.providers.map(provider => (
                                  <span key={provider} className="text-lg" title={provider.toUpperCase()}>
                                    {getProviderIcon(provider)}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className="px-6 py-4 text-white">{user.total_resources}</td>
                            <td className="px-6 py-4">
                              <div className="flex items-center space-x-2">
                                <span className="text-white font-medium">{user.admin_access_count}</span>
                                {user.cross_provider_admin && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30">
                                    Cross-Provider
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex flex-wrap gap-1">
                                {user.privilege_escalation_count > 0 && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-500/20 text-orange-400 border border-orange-500/30">
                                    Escalation ({user.privilege_escalation_count})
                                  </span>
                                )}
                                {user.unused_privileges_count > 0 && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                                    Unused ({user.unused_privileges_count})
                                  </span>
                                )}
                                {user.top_risk_factors.length > 0 && (
                                  <span className="text-xs text-slate-400">
                                    {user.top_risk_factors.slice(0, 2).join(", ")}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <button
                                onClick={() => fetchUserRiskAnalysis(user.user_email)}
                                className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm transition-colors duration-200 flex items-center space-x-1"
                              >
                                <Eye className="w-4 h-4" />
                                <span>Details</span>
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  {pagination.total_pages > 1 && (
                    <div className="bg-slate-800 px-6 py-3 flex items-center justify-between">
                      <div className="text-sm text-slate-300">
                        Showing {((pagination.page - 1) * pagination.page_size) + 1} to{' '}
                        {Math.min(pagination.page * pagination.page_size, pagination.total_users)} of{' '}
                        {pagination.total_users} users
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => fetchUsers(pagination.page - 1)}
                          disabled={!pagination.has_prev}
                          className="px-3 py-1 rounded bg-slate-700 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600 transition-colors duration-200"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <span className="text-slate-300">
                          Page {pagination.page} of {pagination.total_pages}
                        </span>
                        <button
                          onClick={() => fetchUsers(pagination.page + 1)}
                          disabled={!pagination.has_next}
                          className="px-3 py-1 rounded bg-slate-700 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600 transition-colors duration-200"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* Provider Dashboards Tab */}
        {activeView === "providers" && (
          <div className="space-y-6">
            {/* Provider Selection */}
            <div className="flex justify-center space-x-4">
              {['aws', 'gcp', 'azure', 'okta'].map(provider => (
                <button
                  key={provider}
                  onClick={() => setSelectedProviderDashboard(provider)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-200 ${
                    selectedProviderDashboard === provider
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  <span className="text-xl">{getProviderIcon(provider)}</span>
                  <span className="font-medium">{provider.toUpperCase()}</span>
                </button>
              ))}
            </div>

            {/* Provider Dashboard Content */}
            {providerAnalytics[selectedProviderDashboard] && (
              <div className="space-y-6">
                {/* Provider Summary */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                    <Users className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {providerAnalytics[selectedProviderDashboard].summary.total_users}
                    </p>
                    <p className="text-slate-300 text-sm">Total Users</p>
                  </div>
                  <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                    <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {providerAnalytics[selectedProviderDashboard].summary.privilege_escalation_count}
                    </p>
                    <p className="text-slate-300 text-sm">Escalation Risks</p>
                  </div>
                  <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                    <Shield className="w-8 h-8 text-orange-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {providerAnalytics[selectedProviderDashboard].summary.cross_account_users}
                    </p>
                    <p className="text-slate-300 text-sm">Cross-Account Users</p>
                  </div>
                  <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                    <TrendingUp className="w-8 h-8 text-green-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {Object.keys(providerAnalytics[selectedProviderDashboard].summary.service_breakdown).length}
                    </p>
                    <p className="text-slate-300 text-sm">Services</p>
                  </div>
                </div>

                {/* Top Risky Services */}
                <div className="bg-slate-700/30 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-white mb-4">
                    Top Risky {selectedProviderDashboard.toUpperCase()} Services
                  </h4>
                  <div className="space-y-3">
                    {providerAnalytics[selectedProviderDashboard].top_risky_services.slice(0, 5).map((service, index) => (
                      <div key={index} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-4">
                        <div>
                          <p className="text-white font-medium">{service.service}</p>
                          <p className="text-slate-400 text-sm">
                            {service.total_users} users • {service.admin_users} admin access
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-white font-bold">{service.avg_risk.toFixed(1)}</p>
                          <p className="text-slate-400 text-xs">Avg Risk</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Top Risks for Provider */}
                <div className="bg-slate-700/30 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-white mb-4">
                    Top {selectedProviderDashboard.toUpperCase()} Risk Users
                  </h4>
                  <div className="space-y-3">
                    {providerAnalytics[selectedProviderDashboard].summary.top_risks.slice(0, 5).map((user, index) => (
                      <div key={index} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-4">
                        <div>
                          <p className="text-white font-medium">{user.user_email}</p>
                          <p className="text-slate-400 text-sm">
                            Primary risks: {user.primary_risks.join(", ")}
                          </p>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="text-right">
                            <p className="text-white font-bold">{user.risk_score.toFixed(1)}</p>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getRiskBadgeColor(user.risk_level)}`}>
                              {user.risk_level.charAt(0).toUpperCase() + user.risk_level.slice(1)}
                            </span>
                          </div>
                          <button
                            onClick={() => fetchUserRiskAnalysis(user.user_email)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm transition-colors duration-200"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Risk Analysis Modal */}
      {riskAnalysisModal && selectedUserRisk && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-white">Risk Analysis Details</h3>
                <button
                  onClick={() => setRiskAnalysisModal(false)}
                  className="text-slate-400 hover:text-white transition-colors duration-200"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-6">
                {/* User Info */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-slate-300 text-sm">User</p>
                      <p className="text-white font-medium">{selectedUserRisk.user_name}</p>
                      <p className="text-blue-400 text-sm">{selectedUserRisk.user_email}</p>
                    </div>
                    <div>
                      <p className="text-slate-300 text-sm">Overall Risk Score</p>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl font-bold text-white">{selectedUserRisk.overall_risk_score.toFixed(1)}</span>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getRiskBadgeColor(selectedUserRisk.risk_level)}`}>
                          {selectedUserRisk.risk_level.charAt(0).toUpperCase() + selectedUserRisk.risk_level.slice(1)}
                        </span>
                      </div>
                      <p className="text-slate-400 text-xs">Confidence: {(selectedUserRisk.confidence_score * 100).toFixed(0)}%</p>
                    </div>
                  </div>
                </div>

                {/* Risk Factors */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-white mb-4">Risk Factors</h4>
                  <div className="space-y-3">
                    {selectedUserRisk.risk_factors.map((factor, index) => (
                      <div key={index} className="bg-slate-800/50 rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="text-white font-medium">{factor.description}</p>
                            <p className="text-slate-400 text-sm mt-1">{factor.justification}</p>
                          </div>
                          <div className="text-right ml-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getRiskBadgeColor(factor.severity)}`}>
                              {factor.severity}
                            </span>
                            <p className="text-slate-400 text-xs mt-1">Weight: {factor.weight.toFixed(1)}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommendations */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-white mb-4">Recommendations</h4>
                  <div className="space-y-2">
                    {selectedUserRisk.recommendations.map((rec, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <p className="text-slate-300 text-sm">{rec}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Privilege Escalation Paths */}
                {selectedUserRisk.privilege_escalation_paths.length > 0 && (
                  <div className="bg-slate-700/30 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-white mb-4">Privilege Escalation Paths</h4>
                    <div className="space-y-3">
                      {selectedUserRisk.privilege_escalation_paths.map((path, index) => (
                        <div key={index} className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-red-400 font-medium">
                              {path.start_privilege} → {path.end_privilege}
                            </span>
                            <span className="text-red-300 text-sm">Risk: {path.risk_score.toFixed(1)}</span>
                          </div>
                          <div className="text-slate-300 text-sm">
                            {path.path_steps.map((step, stepIndex) => (
                              <span key={stepIndex}>
                                {stepIndex > 0 && " → "}
                                {step.action}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Access Summary */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-white mb-4">Access Summary</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-white">{selectedUserRisk.total_resources}</p>
                      <p className="text-slate-300 text-sm">Total Resources</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-white">{selectedUserRisk.admin_access_count}</p>
                      <p className="text-slate-300 text-sm">Admin Access</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-white">{selectedUserRisk.providers_with_access.length}</p>
                      <p className="text-slate-300 text-sm">Providers</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-white">{selectedUserRisk.services_with_access.length}</p>
                      <p className="text-slate-300 text-sm">Services</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedAnalytics;