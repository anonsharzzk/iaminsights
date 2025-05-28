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

  // Overview analytics state
  const [overviewStats, setOverviewStats] = useState({
    total_users: 0,
    cross_provider_admins: 0,
    escalation_risks: 0,
    high_risk_users: 0,
    risk_distribution: { critical: 0, high: 0, medium: 0, low: 0 },
    provider_distribution: { aws: 0, gcp: 0, azure: 0, okta: 0 }
  });

  // Fetch overview statistics
  const fetchOverviewStats = async () => {
    if (!isAuthenticated) {
      console.error("User not authenticated");
      return;
    }
    
    try {
      // Fetch users to calculate overview stats
      const response = await axios.get(`${API}/users/paginated?page=1&page_size=1000`);
      const allUsers = response.data.users;
      
      const stats = {
        total_users: allUsers.length,
        cross_provider_admins: allUsers.filter(u => u.cross_provider_admin).length,
        escalation_risks: allUsers.filter(u => u.privilege_escalation_count > 0).length,
        high_risk_users: allUsers.filter(u => u.risk_level === 'high' || u.risk_level === 'critical').length,
        risk_distribution: {
          critical: allUsers.filter(u => u.risk_level === 'critical').length,
          high: allUsers.filter(u => u.risk_level === 'high').length,
          medium: allUsers.filter(u => u.risk_level === 'medium').length,
          low: allUsers.filter(u => u.risk_level === 'low').length,
        },
        provider_distribution: {
          aws: allUsers.filter(u => u.providers.includes('aws')).length,
          gcp: allUsers.filter(u => u.providers.includes('gcp')).length,
          azure: allUsers.filter(u => u.providers.includes('azure')).length,
          okta: allUsers.filter(u => u.providers.includes('okta')).length,
        }
      };
      
      setOverviewStats(stats);
      
      // Also set a subset for the main users display
      setUsers(allUsers.slice(0, 20));
      setPagination({
        page: 1,
        page_size: 20,
        total_users: allUsers.length,
        total_pages: Math.ceil(allUsers.length / 20),
        has_next: allUsers.length > 20,
        has_prev: false
      });
    } catch (error) {
      console.error("Error fetching overview stats:", error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.error("Authentication error - token may be invalid");
      }
    }
  };
  
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

  // Load data on component mount and view changes
  useEffect(() => {
    if (activeView === "overview") {
      fetchOverviewStats();
    } else if (activeView === "users") {
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
                <p className="text-2xl font-bold text-white">{overviewStats.total_users}</p>
                <p className="text-slate-300 text-sm">Total Users</p>
              </div>
              <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                <Shield className="w-8 h-8 text-orange-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-white">{overviewStats.cross_provider_admins}</p>
                <p className="text-slate-300 text-sm">Cross-Provider Admins</p>
              </div>
              <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-white">{overviewStats.escalation_risks}</p>
                <p className="text-slate-300 text-sm">Escalation Risks</p>
              </div>
              <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                <Activity className="w-8 h-8 text-green-400 mx-auto mb-2" />
                <p className="text-2xl font-bold text-white">{overviewStats.high_risk_users}</p>
                <p className="text-slate-300 text-sm">High Risk Users</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Risk Distribution */}
              <div className="bg-slate-700/30 rounded-lg p-6">
                <h4 className="text-lg font-semibold text-white mb-4">Risk Distribution</h4>
                <div className="space-y-3">
                  {['critical', 'high', 'medium', 'low'].map(level => {
                    const count = overviewStats.risk_distribution[level];
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
                    const count = overviewStats.provider_distribution[provider];
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

                {/* User Permissions Section */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-white mb-4">User Permissions</h4>
                  <div className="space-y-3">
                    {selectedUserRisk.resource_details ? (
                      selectedUserRisk.resource_details.map((resource, index) => (
                        <div key={index} className="bg-slate-800/50 rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                <span className="text-xl">{getProviderIcon(resource.provider)}</span>
                                <p className="text-white font-medium">{resource.provider.toUpperCase()} - {resource.service}</p>
                              </div>
                              <p className="text-slate-300 text-sm mb-2">{resource.resource_name}</p>
                              <div className="flex items-center space-x-2 mb-2">
                                <span className={`text-xs px-2 py-1 rounded border ${
                                  resource.access_type === 'admin' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                                  resource.access_type === 'write' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
                                  'bg-blue-500/20 text-blue-400 border-blue-500/30'
                                }`}>
                                  {resource.access_type.charAt(0).toUpperCase() + resource.access_type.slice(1)} Access
                                </span>
                                {resource.is_privileged && (
                                  <span className="text-xs bg-orange-500/20 text-orange-400 px-2 py-1 rounded border border-orange-500/30">
                                    Privileged
                                  </span>
                                )}
                                {!resource.mfa_required && (
                                  <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded border border-red-500/30">
                                    No MFA
                                  </span>
                                )}
                              </div>
                              {resource.account_id && (
                                <p className="text-slate-400 text-xs">Account: {resource.account_id}</p>
                              )}
                              {resource.last_used && (
                                <p className="text-slate-400 text-xs">Last used: {new Date(resource.last_used).toLocaleDateString()}</p>
                              )}
                            </div>
                            <div className="ml-4">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium border ${
                                resource.access_type === 'admin' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                                resource.is_privileged ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' :
                                'bg-green-500/20 text-green-400 border-green-500/30'
                              }`}>
                                {resource.access_type === 'admin' ? 'High Risk' : 
                                 resource.is_privileged ? 'Medium Risk' : 'Low Risk'}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      // Fallback to services if resource_details not available
                      selectedUserRisk.services_with_access.map((service, index) => (
                        <div key={index} className="bg-slate-800/50 rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-white font-medium">{service}</p>
                              <div className="mt-2 space-y-1">
                                <div className="flex items-center space-x-2">
                                  <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded border border-blue-500/30">
                                    Read Access
                                  </span>
                                  <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded border border-yellow-500/30">
                                    Write Access
                                  </span>
                                  {selectedUserRisk.admin_access_count > 0 && (
                                    <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded border border-red-500/30">
                                      Admin Access
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="ml-4">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium border ${
                                selectedUserRisk.admin_access_count > 0 ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                                'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
                              }`}>
                                {selectedUserRisk.admin_access_count > 0 ? 'High Privilege' : 'Standard Access'}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Impact Analysis Section */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-white mb-4">Potential Impact Analysis</h4>
                  <div className="space-y-4">
                    
                    {/* Data Access Impact */}
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <div className="flex items-start space-x-3">
                        <Database className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-white font-medium">Data Access Impact</p>
                          <p className="text-slate-300 text-sm mt-1">
                            With {selectedUserRisk.total_resources} resource access grants, this user can potentially:
                          </p>
                          <ul className="text-slate-400 text-sm mt-2 space-y-1">
                            <li>• Read sensitive data from {selectedUserRisk.providers_with_access.length} cloud provider(s)</li>
                            <li>• Access customer information and business data</li>
                            {selectedUserRisk.admin_access_count > 0 && (
                              <li>• Modify or delete critical business data</li>
                            )}
                          </ul>
                        </div>
                      </div>
                    </div>

                    {/* System Control Impact */}
                    {selectedUserRisk.admin_access_count > 0 && (
                      <div className="bg-slate-800/50 rounded-lg p-4">
                        <div className="flex items-start space-x-3">
                          <Settings className="w-5 h-5 text-orange-400 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-white font-medium">System Control Impact</p>
                            <p className="text-slate-300 text-sm mt-1">
                              With {selectedUserRisk.admin_access_count} administrative access grant(s):
                            </p>
                            <ul className="text-slate-400 text-sm mt-2 space-y-1">
                              <li>• Create, modify, or delete user accounts and permissions</li>
                              <li>• Change system configurations and security settings</li>
                              <li>• Access administrative logs and monitoring data</li>
                              <li>• Deploy or modify applications and services</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Cross-Provider Risk */}
                    {selectedUserRisk.providers_with_access.length > 1 && (
                      <div className="bg-slate-800/50 rounded-lg p-4">
                        <div className="flex items-start space-x-3">
                          <Cloud className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-white font-medium">Cross-Provider Risk</p>
                            <p className="text-slate-300 text-sm mt-1">
                              Access across {selectedUserRisk.providers_with_access.length} providers ({selectedUserRisk.providers_with_access.join(', ')}):
                            </p>
                            <ul className="text-slate-400 text-sm mt-2 space-y-1">
                              <li>• Potential for lateral movement between cloud environments</li>
                              <li>• Increased attack surface across multiple platforms</li>
                              <li>• Complex permission interactions and dependencies</li>
                              {selectedUserRisk.cross_provider_admin && (
                                <li>• <span className="text-red-400 font-medium">Critical:</span> Administrative access across multiple clouds</li>
                              )}
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Privilege Escalation Impact */}
                    {selectedUserRisk.privilege_escalation_paths.length > 0 && (
                      <div className="bg-slate-800/50 rounded-lg p-4">
                        <div className="flex items-start space-x-3">
                          <TrendingUp className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-white font-medium">Privilege Escalation Impact</p>
                            <p className="text-slate-300 text-sm mt-1">
                              {selectedUserRisk.privilege_escalation_paths.length} escalation path(s) detected:
                            </p>
                            <ul className="text-slate-400 text-sm mt-2 space-y-1">
                              <li>• Can potentially gain higher privileges than initially granted</li>
                              <li>• May bypass intended access controls and restrictions</li>
                              <li>• Could lead to unauthorized administrative access</li>
                              <li>• Risk of permanent privilege elevation through configuration changes</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Business Impact Summary */}
                    <div className="bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/30 rounded-lg p-4">
                      <div className="flex items-start space-x-3">
                        <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-white font-medium">Overall Business Impact</p>
                          <p className="text-slate-300 text-sm mt-1">
                            Risk Level: <span className={`font-bold ${
                              selectedUserRisk.risk_level === 'critical' ? 'text-red-400' :
                              selectedUserRisk.risk_level === 'high' ? 'text-orange-400' :
                              selectedUserRisk.risk_level === 'medium' ? 'text-yellow-400' : 'text-green-400'
                            }`}>
                              {selectedUserRisk.risk_level.toUpperCase()}
                            </span>
                          </p>
                          <div className="mt-2">
                            <p className="text-slate-400 text-sm">
                              {selectedUserRisk.risk_level === 'critical' && 
                                "Immediate action required. This user poses significant risk to data security and system integrity."
                              }
                              {selectedUserRisk.risk_level === 'high' && 
                                "High priority for review. User has elevated privileges that could impact business operations."
                              }
                              {selectedUserRisk.risk_level === 'medium' && 
                                "Moderate risk. Regular monitoring and periodic access review recommended."
                              }
                              {selectedUserRisk.risk_level === 'low' && 
                                "Low risk profile. Standard security monitoring sufficient."
                              }
                            </p>
                          </div>
                        </div>
                      </div>
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