import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import CytoscapeComponent from "react-cytoscapejs";
import cytoscape from "cytoscape";
import coseBilkent from "cytoscape-cose-bilkent";
import { 
  Search, Users, Shield, BarChart3, Cloud, Server, Database, Key, 
  Download, RefreshCw, Filter, Eye, Settings, Upload, 
  FileText, AlertTriangle, CheckCircle, User, Home
} from "lucide-react";

// Register the layout extension
cytoscape.use(coseBilkent);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CloudAccessVisualizer = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [searchEmail, setSearchEmail] = useState("");
  const [searchResource, setSearchResource] = useState("");
  const [searchType, setSearchType] = useState("user");
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [userInfo, setUserInfo] = useState(null);
  const [resourceResults, setResourceResults] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statistics, setStatistics] = useState(null);
  const [allUsers, setAllUsers] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState("all");
  const [selectedAccessType, setSelectedAccessType] = useState("all");
  const [showLegend, setShowLegend] = useState(true);
  const [graphLayout, setGraphLayout] = useState("cose-bilkent");
  const [selectedNode, setSelectedNode] = useState(null);
  const [importFile, setImportFile] = useState(null);
  const [selectedImportProvider, setSelectedImportProvider] = useState("aws");
  const [providerSamples, setProviderSamples] = useState({});
  const [importResult, setImportResult] = useState(null);
  const cyRef = useRef();

  // Cytoscape layout and styling
  const cytoscapeStylesheet = [
    {
      selector: 'node',
      style: {
        'background-color': 'data(color)',
        'label': 'data(label)',
        'color': '#fff',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '12px',
        'font-weight': 'bold',
        'text-outline-width': 2,
        'text-outline-color': '#000',
        'text-wrap': 'wrap',
        'text-max-width': '120px',
        'width': 'mapData(type, user, resource, 80, 60)',
        'height': 'mapData(type, user, resource, 80, 60)',
        'border-width': 2,
        'border-color': '#333'
      }
    },
    {
      selector: 'node[type="user"]',
      style: {
        'shape': 'round-rectangle',
        'width': 120,
        'height': 80,
        'background-color': '#2563eb',
        'border-color': '#1d4ed8'
      }
    },
    {
      selector: 'node[type="provider"]',
      style: {
        'shape': 'round-rectangle',
        'width': 100,
        'height': 70,
        'font-size': '14px',
        'border-color': '#374151'
      }
    },
    {
      selector: 'node[type="service"]',
      style: {
        'shape': 'ellipse',
        'width': 80,
        'height': 60,
        'font-size': '11px'
      }
    },
    {
      selector: 'node[type="resource"]',
      style: {
        'shape': 'round-rectangle',
        'width': 70,
        'height': 50,
        'font-size': '10px'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 3,
        'line-color': '#6b7280',
        'target-arrow-color': '#6b7280',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'arrow-scale': 1.2,
        'label': 'data(label)',
        'font-size': '10px',
        'color': '#374151',
        'text-rotation': 'autorotate',
        'text-margin-y': -10
      }
    },
    {
      selector: ':selected',
      style: {
        'border-width': 4,
        'border-color': '#fbbf24'
      }
    }
  ];

  const getLayoutConfig = (layoutName) => {
    const layouts = {
      'cose-bilkent': {
        name: 'cose-bilkent',
        quality: 'default',
        nodeDimensionsIncludeLabels: true,
        fit: true,
        padding: 20,
        randomize: false,
        nodeRepulsion: 4500,
        idealEdgeLength: 100,
        edgeElasticity: 0.45,
        nestingFactor: 0.1,
        gravity: 0.25,
        numIter: 2500,
        tile: false,
        animate: 'end',
        animationDuration: 1000
      },
      'circle': {
        name: 'circle',
        fit: true,
        padding: 30,
        avoidOverlap: true,
        animate: true,
        animationDuration: 500
      },
      'grid': {
        name: 'grid',
        fit: true,
        padding: 30,
        avoidOverlap: true,
        animate: true,
        animationDuration: 500
      },
      'breadthfirst': {
        name: 'breadthfirst',
        fit: true,
        directed: false,
        padding: 30,
        spacingFactor: 1.75,
        avoidOverlap: true,
        animate: true,
        animationDuration: 500
      }
    };
    
    return layouts[layoutName] || layouts['cose-bilkent'];
  };

  // Fetch data on component mount
  useEffect(() => {
    fetchStatistics();
    fetchAllUsers();
    fetchAnalytics();
    fetchProviderSamples();
  }, []);

  const fetchStatistics = async () => {
    try {
      const response = await axios.get(`${API}/providers`);
      setStatistics(response.data);
    } catch (error) {
      console.error("Error fetching statistics:", error);
    }
  };

  const fetchAllUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setAllUsers(response.data);
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics`);
      setAnalytics(response.data);
    } catch (error) {
      console.error("Error fetching analytics:", error);
    }
  };

  const fetchProviderSamples = async () => {
    try {
      const response = await axios.get(`${API}/providers/samples`);
      setProviderSamples(response.data);
    } catch (error) {
      console.error("Error fetching provider samples:", error);
    }
  };

  // Filter graph data based on selected filters
  const getFilteredGraphData = () => {
    if (!userInfo) return { nodes: [], edges: [] };

    let filteredNodes = [...graphData.nodes];
    let filteredEdges = [...graphData.edges];

    // Filter by provider
    if (selectedProvider !== "all") {
      const allowedNodeIds = new Set();
      
      const userNode = filteredNodes.find(node => node.data.type === "user");
      if (userNode) allowedNodeIds.add(userNode.data.id);
      
      filteredNodes.forEach(node => {
        const data = node.data;
        if (data.provider === selectedProvider || data.type === "user") {
          allowedNodeIds.add(data.id);
        }
      });
      
      filteredNodes = filteredNodes.filter(node => allowedNodeIds.has(node.data.id));
      filteredEdges = filteredEdges.filter(edge => 
        allowedNodeIds.has(edge.data.source) && allowedNodeIds.has(edge.data.target)
      );
    }

    // Filter by access type
    if (selectedAccessType !== "all") {
      const allowedNodeIds = new Set();
      
      filteredNodes.forEach(node => {
        const data = node.data;
        if (data.type === "user" || data.type === "provider" || data.type === "service") {
          allowedNodeIds.add(data.id);
        } else if (data.type === "resource" && data.access_type === selectedAccessType) {
          allowedNodeIds.add(data.id);
        }
      });
      
      filteredNodes = filteredNodes.filter(node => allowedNodeIds.has(node.data.id));
      filteredEdges = filteredEdges.filter(edge => 
        allowedNodeIds.has(edge.data.source) && allowedNodeIds.has(edge.data.target)
      );
    }

    return { nodes: filteredNodes, edges: filteredEdges };
  };

  const handleSearch = async () => {
    if (searchType === "user") {
      await handleUserSearch();
    } else {
      await handleResourceSearch();
    }
  };

  const handleUserSearch = async () => {
    if (!searchEmail.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/search/${encodeURIComponent(searchEmail)}`);
      const data = response.data;
      
      if (data.user) {
        setUserInfo(data.user);
        setResourceResults([]);
        const nodes = data.graph_data.nodes.map(node => ({
          data: { 
            id: node.id, 
            label: node.label, 
            type: node.type,
            provider: node.provider,
            access_type: node.access_type,
            color: node.color 
          }
        }));
        
        const edges = data.graph_data.edges.map(edge => ({
          data: { 
            id: edge.id, 
            source: edge.source, 
            target: edge.target, 
            label: edge.label 
          }
        }));
        
        setGraphData({ nodes, edges });
      } else {
        setUserInfo(null);
        setGraphData({ nodes: [], edges: [] });
        alert("User not found in the system");
      }
    } catch (error) {
      console.error("Error searching user:", error);
      alert("Error searching for user access data");
    } finally {
      setLoading(false);
    }
  };

  const handleResourceSearch = async () => {
    if (!searchResource.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/search/resource/${encodeURIComponent(searchResource)}`);
      setResourceResults(response.data);
      setUserInfo(null);
      setGraphData({ nodes: [], edges: [] });
    } catch (error) {
      console.error("Error searching resource:", error);
      alert("Error searching for resource access data");
    } finally {
      setLoading(false);
    }
  };

  const handleFileImport = async () => {
    if (!importFile) return;
    
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', importFile);
      
      const response = await axios.post(`${API}/import/json`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setImportResult(response.data);
      setImportFile(null);
      
      // Refresh data
      await fetchAllUsers();
      await fetchStatistics();
      await fetchAnalytics();
      
      alert(`Successfully imported ${response.data.imported_users} users!`);
    } catch (error) {
      console.error("Error importing file:", error);
      alert("Error importing file: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const params = new URLSearchParams();
      if (selectedProvider !== "all") params.append('provider', selectedProvider);
      if (selectedAccessType !== "all") params.append('access_type', selectedAccessType);
      
      const url = `${API}/export/${format}?${params.toString()}`;
      window.open(url, '_blank');
    } catch (error) {
      console.error("Error exporting data:", error);
      alert("Error exporting data");
    }
  };

  const resetGraphView = () => {
    if (cyRef.current) {
      cyRef.current.fit();
      cyRef.current.center();
    }
  };

  const changeLayout = (layoutName) => {
    setGraphLayout(layoutName);
    if (cyRef.current) {
      const layout = cyRef.current.layout(getLayoutConfig(layoutName));
      layout.run();
    }
  };

  const exportGraphPNG = () => {
    if (cyRef.current) {
      const png64 = cyRef.current.png();
      const link = document.createElement('a');
      link.download = `cloud-access-${searchEmail}-${Date.now()}.png`;
      link.href = png64;
      link.click();
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

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleUserSelect = (email) => {
    setSearchEmail(email);
    handleUserSearch();
  };

  return (
    <div className="space-y-8">
      {/* Tabs */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700">
        <div className="flex space-x-1 p-1">
          {[
            { id: 'dashboard', label: 'Search & Visualize', icon: Search },
            { id: 'import', label: 'Import Data', icon: Upload },
            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
            { id: 'export', label: 'Export', icon: Download }
          ].map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-200 ${
                  activeTab === tab.id 
                    ? 'bg-blue-600 text-white' 
                    : 'text-slate-300 hover:bg-slate-700/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && (
        <div className="space-y-8">
          {/* Search Section */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-8 border border-slate-700">
            <div className="text-center mb-6">
              <h2 className="text-3xl font-bold text-white mb-2">
                Cloud Access Search & Visualization
              </h2>
              <p className="text-slate-300 text-lg">
                Search for users or resources to visualize access across AWS, GCP, Azure, and Okta
              </p>
            </div>
            
            {/* Search Type Toggle */}
            <div className="flex justify-center mb-6">
              <div className="bg-slate-700/50 rounded-lg p-1 flex">
                <button
                  onClick={() => setSearchType("user")}
                  className={`px-4 py-2 rounded transition-colors duration-200 ${
                    searchType === "user" 
                      ? 'bg-blue-600 text-white' 
                      : 'text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  Search by User
                </button>
                <button
                  onClick={() => setSearchType("resource")}
                  className={`px-4 py-2 rounded transition-colors duration-200 ${
                    searchType === "resource" 
                      ? 'bg-blue-600 text-white' 
                      : 'text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  Search by Resource
                </button>
              </div>
            </div>
            
            <div className="max-w-2xl mx-auto">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-slate-400" />
                </div>
                {searchType === "user" ? (
                  <input
                    type="email"
                    value={searchEmail}
                    onChange={(e) => setSearchEmail(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Enter user email (e.g., alice@company.com)"
                    className="block w-full pl-10 pr-20 py-4 text-lg border border-slate-600 rounded-lg bg-slate-700/50 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                ) : (
                  <input
                    type="text"
                    value={searchResource}
                    onChange={(e) => setSearchResource(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Enter resource name (e.g., production-bucket, S3)"
                    className="block w-full pl-10 pr-20 py-4 text-lg border border-slate-600 rounded-lg bg-slate-700/50 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                )}
                <div className="absolute inset-y-0 right-0 flex items-center">
                  <button
                    onClick={handleSearch}
                    disabled={loading}
                    className="mr-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white px-6 py-2 rounded-md font-medium transition-colors duration-200"
                  >
                    {loading ? "Searching..." : "Search"}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Statistics Cards */}
          {statistics && (
            <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 border border-slate-700">
                <div className="flex items-center">
                  <Users className="w-8 h-8 text-blue-400 mr-3" />
                  <div>
                    <p className="text-slate-300 text-sm">Total Users</p>
                    <p className="text-2xl font-bold text-white">{statistics.total_users}</p>
                  </div>
                </div>
              </div>
              
              {Object.entries(statistics.providers).map(([provider, data]) => (
                <div key={provider} className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 border border-slate-700">
                  <div className="flex items-center">
                    <div className="text-2xl mr-3">{getProviderIcon(provider)}</div>
                    <div>
                      <p className="text-slate-300 text-sm">{provider.toUpperCase()}</p>
                      <p className="text-xl font-bold text-white">{data.users} users</p>
                      <p className="text-slate-400 text-xs">{data.resources} resources</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Quick Access - Sample Users */}
          {allUsers.length > 0 && !userInfo && (
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                <Users className="w-5 h-5 mr-2" />
                Quick Access - Sample Users
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {allUsers.slice(0, 3).map((user) => (
                  <button
                    key={user.user_email}
                    onClick={() => handleUserSelect(user.user_email)}
                    className="text-left p-4 bg-slate-700/50 hover:bg-slate-700 rounded-lg border border-slate-600 transition-colors duration-200"
                  >
                    <p className="text-white font-medium">{user.user_name}</p>
                    <p className="text-blue-400 text-sm">{user.user_email}</p>
                    <p className="text-slate-400 text-xs mt-1">{user.resources.length} resources</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* User Info & Graph */}
          {userInfo && (
            <div className="space-y-8">
              {/* User Info Panel */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-white">{userInfo.user_name}</h3>
                    <p className="text-blue-400 text-lg">{userInfo.user_email}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-slate-300 text-sm">Total Access Points</p>
                    <p className="text-3xl font-bold text-white">{userInfo.resources.length}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(
                    userInfo.resources.reduce((acc, resource) => {
                      acc[resource.provider] = (acc[resource.provider] || 0) + 1;
                      return acc;
                    }, {})
                  ).map(([provider, count]) => (
                    <div key={provider} className="bg-slate-700/50 rounded-lg p-3 text-center">
                      <div className="text-2xl mb-1">{getProviderIcon(provider)}</div>
                      <p className="text-white font-medium">{provider.toUpperCase()}</p>
                      <p className="text-slate-400 text-sm">{count} resources</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Graph Controls & Filters */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center space-x-4">
                    <h3 className="text-lg font-semibold text-white flex items-center">
                      <Settings className="w-5 h-5 mr-2" />
                      Graph Controls
                    </h3>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-4">
                    {/* Provider Filter */}
                    <div className="flex items-center space-x-2">
                      <Filter className="w-4 h-4 text-slate-400" />
                      <label className="text-slate-300 text-sm">Provider:</label>
                      <select
                        value={selectedProvider}
                        onChange={(e) => setSelectedProvider(e.target.value)}
                        className="bg-slate-700 text-white text-sm rounded px-3 py-1 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="all">All Providers</option>
                        <option value="aws">AWS</option>
                        <option value="gcp">GCP</option>
                        <option value="azure">Azure</option>
                        <option value="okta">Okta</option>
                      </select>
                    </div>

                    {/* Access Type Filter */}
                    <div className="flex items-center space-x-2">
                      <Key className="w-4 h-4 text-slate-400" />
                      <label className="text-slate-300 text-sm">Access:</label>
                      <select
                        value={selectedAccessType}
                        onChange={(e) => setSelectedAccessType(e.target.value)}
                        className="bg-slate-700 text-white text-sm rounded px-3 py-1 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="all">All Access Types</option>
                        <option value="read">Read</option>
                        <option value="write">Write</option>
                        <option value="admin">Admin</option>
                        <option value="owner">Owner</option>
                        <option value="user">User</option>
                        <option value="execute">Execute</option>
                      </select>
                    </div>

                    {/* Layout Selector */}
                    <div className="flex items-center space-x-2">
                      <BarChart3 className="w-4 h-4 text-slate-400" />
                      <label className="text-slate-300 text-sm">Layout:</label>
                      <select
                        value={graphLayout}
                        onChange={(e) => changeLayout(e.target.value)}
                        className="bg-slate-700 text-white text-sm rounded px-3 py-1 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="cose-bilkent">Smart Layout</option>
                        <option value="circle">Circle</option>
                        <option value="grid">Grid</option>
                        <option value="breadthfirst">Hierarchy</option>
                      </select>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={resetGraphView}
                        className="bg-slate-700 hover:bg-slate-600 text-white px-3 py-1 rounded text-sm flex items-center space-x-1"
                        title="Reset View"
                      >
                        <RefreshCw className="w-4 h-4" />
                        <span>Reset</span>
                      </button>
                      
                      <button
                        onClick={exportGraphPNG}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm flex items-center space-x-1"
                        title="Export as PNG"
                      >
                        <Download className="w-4 h-4" />
                        <span>Export</span>
                      </button>

                      <button
                        onClick={() => setShowLegend(!showLegend)}
                        className="bg-slate-700 hover:bg-slate-600 text-white px-3 py-1 rounded text-sm flex items-center space-x-1"
                        title="Toggle Legend"
                      >
                        <Eye className="w-4 h-4" />
                        <span>Legend</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Graph Visualization */}
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold text-white flex items-center">
                    <BarChart3 className="w-5 h-5 mr-2" />
                    Access Graph Visualization
                  </h3>
                  {selectedNode && (
                    <div className="bg-slate-700/50 rounded-lg p-3 max-w-md">
                      <p className="text-white text-sm font-medium">Selected: {selectedNode.label}</p>
                      <p className="text-slate-400 text-xs">
                        Type: {selectedNode.type} 
                        {selectedNode.provider && ` • Provider: ${selectedNode.provider}`}
                        {selectedNode.access_type && ` • Access: ${selectedNode.access_type}`}
                      </p>
                    </div>
                  )}
                </div>
                
                {graphData.nodes.length > 0 ? (
                  <div className="bg-slate-900 rounded-lg border border-slate-600" style={{ height: '700px' }}>
                    <CytoscapeComponent
                      elements={[...getFilteredGraphData().nodes, ...getFilteredGraphData().edges]}
                      style={{ width: '100%', height: '100%' }}
                      stylesheet={cytoscapeStylesheet}
                      layout={getLayoutConfig(graphLayout)}
                      cy={(cy) => {
                        cyRef.current = cy;
                        
                        // Add click event to show node info
                        cy.on('tap', 'node', function(evt) {
                          const node = evt.target;
                          const data = node.data();
                          setSelectedNode(data);
                        });

                        // Add hover effects
                        cy.on('mouseover', 'node', function(evt) {
                          const node = evt.target;
                          node.style('border-width', '4px');
                        });

                        cy.on('mouseout', 'node', function(evt) {
                          const node = evt.target;
                          if (!node.selected()) {
                            node.style('border-width', '2px');
                          }
                        });

                        // Clear selection on background click
                        cy.on('tap', function(evt) {
                          if (evt.target === cy) {
                            setSelectedNode(null);
                            cy.nodes().unselect();
                          }
                        });
                      }}
                    />
                  </div>
                ) : (
                  <div className="bg-slate-900 rounded-lg border border-slate-600 h-96 flex items-center justify-center">
                    <div className="text-center text-slate-400">
                      <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p>No graph data available</p>
                      <p className="text-sm mt-2">Search for a user to see their access visualization</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Enhanced Legend */}
              {showLegend && (
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Graph Legend & Guide</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Node Types */}
                    <div>
                      <h4 className="text-white font-medium mb-3">Node Types</h4>
                      <div className="space-y-3">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                            <Users className="w-4 h-4 text-white" />
                          </div>
                          <div>
                            <p className="text-white text-sm font-medium">User</p>
                            <p className="text-slate-400 text-xs">Central identity node</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                            <Cloud className="w-4 h-4 text-white" />
                          </div>
                          <div>
                            <p className="text-white text-sm font-medium">Cloud Providers</p>
                            <p className="text-slate-400 text-xs">AWS, GCP, Azure, Okta</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center">
                            <Server className="w-4 h-4 text-white" />
                          </div>
                          <div>
                            <p className="text-white text-sm font-medium">Services</p>
                            <p className="text-slate-400 text-xs">S3, IAM, Compute, etc.</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-slate-500 rounded-lg flex items-center justify-center">
                            <Database className="w-4 h-4 text-white" />
                          </div>
                          <div>
                            <p className="text-white text-sm font-medium">Resources</p>
                            <p className="text-slate-400 text-xs">Specific access points</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Access Types */}
                    <div>
                      <h4 className="text-white font-medium mb-3">Access Types</h4>
                      <div className="space-y-2">
                        <div className="flex items-center space-x-3">
                          <div className="w-4 h-4 bg-green-500 rounded"></div>
                          <span className="text-green-400 text-sm font-medium">Read</span>
                          <span className="text-slate-400 text-xs">View permissions</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-4 h-4 bg-yellow-500 rounded"></div>
                          <span className="text-yellow-400 text-sm font-medium">Write</span>
                          <span className="text-slate-400 text-xs">Modify permissions</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-4 h-4 bg-red-500 rounded"></div>
                          <span className="text-red-400 text-sm font-medium">Admin</span>
                          <span className="text-slate-400 text-xs">Full control</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-4 h-4 bg-purple-500 rounded"></div>
                          <span className="text-purple-400 text-sm font-medium">Owner</span>
                          <span className="text-slate-400 text-xs">Resource owner</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-4 h-4 bg-blue-500 rounded"></div>
                          <span className="text-blue-400 text-sm font-medium">User</span>
                          <span className="text-slate-400 text-xs">Standard access</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="w-4 h-4 bg-orange-500 rounded"></div>
                          <span className="text-orange-400 text-sm font-medium">Execute</span>
                          <span className="text-slate-400 text-xs">Run permissions</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-slate-700/30 rounded-lg">
                    <h4 className="text-white font-medium mb-2">💡 Tips</h4>
                    <ul className="text-slate-300 text-sm space-y-1">
                      <li>• Click any node to see detailed information</li>
                      <li>• Use filters to focus on specific providers or access types</li>
                      <li>• Try different layouts to find the best visualization</li>
                      <li>• Export the graph as PNG for reports and documentation</li>
                      <li>• Hover over nodes for quick visual feedback</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Resource Search Results */}
          {resourceResults.length > 0 && (
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
              <h3 className="text-xl font-semibold text-white mb-4">Resource Search Results</h3>
              <div className="space-y-4">
                {resourceResults.map((result, index) => (
                  <div key={index} className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-white font-medium">{result.resource.resource_name}</h4>
                      <span className="text-slate-400 text-sm">{result.total_users} users have access</span>
                    </div>
                    <div className="text-slate-300 text-sm">
                      <p>Provider: {result.resource.provider.toUpperCase()} | Service: {result.resource.service}</p>
                      <p>Access Type: {result.resource.access_type} | Risk Level: {result.resource.risk_level}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Import Tab */}
      {activeTab === 'import' && (
        <div className="space-y-6">
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
            <h3 className="text-2xl font-bold text-white mb-4 flex items-center">
              <Upload className="w-6 h-6 mr-3" />
              Import Cloud Access Data
            </h3>
            
            {/* Provider Selection */}
            <div className="mb-6">
              <label className="block text-slate-300 font-medium mb-3">Select Provider for Sample Format:</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {['aws', 'gcp', 'azure', 'okta'].map(provider => (
                  <button
                    key={provider}
                    onClick={() => setSelectedImportProvider(provider)}
                    className={`p-3 rounded-lg border transition-colors duration-200 ${
                      selectedImportProvider === provider
                        ? 'border-blue-500 bg-blue-600/20 text-white'
                        : 'border-slate-600 bg-slate-700/30 text-slate-300 hover:bg-slate-700/50'
                    }`}
                  >
                    <div className="text-2xl mb-1">{getProviderIcon(provider)}</div>
                    <div className="text-sm font-medium">{provider.toUpperCase()}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* File Upload */}
            <div className="mb-6">
              <label className="block text-slate-300 font-medium mb-3">Upload JSON File:</label>
              <div className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center">
                <Upload className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                <input
                  type="file"
                  accept=".json"
                  onChange={(e) => setImportFile(e.target.files[0])}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer text-blue-400 hover:text-blue-300"
                >
                  Click to select JSON file
                </label>
                <p className="text-slate-400 text-sm mt-1">or drag and drop</p>
                {importFile && (
                  <div className="mt-3 text-green-400 text-sm">
                    Selected: {importFile.name}
                  </div>
                )}
              </div>
            </div>

            {/* Upload Button */}
            <button
              onClick={handleFileImport}
              disabled={!importFile || loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white py-3 rounded-lg font-semibold transition-colors duration-200 mb-6"
            >
              {loading ? 'Importing...' : 'Import Data'}
            </button>

            {/* Sample Format Display */}
            {providerSamples[selectedImportProvider] && (
              <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                <h4 className="text-white font-medium mb-3">Sample {selectedImportProvider.toUpperCase()} Format:</h4>
                <pre className="text-slate-300 text-xs overflow-x-auto bg-slate-900 p-3 rounded">
                  {JSON.stringify(providerSamples[selectedImportProvider].sample_format, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <EnhancedAnalytics />
      )}

      {/* Export Tab */}
      {activeTab === 'export' && (
        <div className="space-y-6">
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
            <h3 className="text-2xl font-bold text-white mb-6 flex items-center">
              <Download className="w-6 h-6 mr-3" />
              Export Data
            </h3>
            
            {/* Export Filters */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div>
                <label className="block text-slate-300 font-medium mb-2">Provider Filter:</label>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Providers</option>
                  <option value="aws">AWS</option>
                  <option value="gcp">GCP</option>
                  <option value="azure">Azure</option>
                  <option value="okta">Okta</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-300 font-medium mb-2">Access Type Filter:</label>
                <select
                  value={selectedAccessType}
                  onChange={(e) => setSelectedAccessType(e.target.value)}
                  className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Access Types</option>
                  <option value="read">Read</option>
                  <option value="write">Write</option>
                  <option value="admin">Admin</option>
                  <option value="owner">Owner</option>
                  <option value="user">User</option>
                  <option value="execute">Execute</option>
                </select>
              </div>
            </div>

            {/* Export Buttons */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => handleExport('csv')}
                className="bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-semibold transition-colors duration-200 flex items-center justify-center space-x-2"
              >
                <FileText className="w-5 h-5" />
                <span>Export CSV</span>
              </button>
              <button
                onClick={() => handleExport('xlsx')}
                className="bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold transition-colors duration-200 flex items-center justify-center space-x-2"
              >
                <FileText className="w-5 h-5" />
                <span>Export Excel</span>
              </button>
              <button
                onClick={() => handleExport('json')}
                className="bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg font-semibold transition-colors duration-200 flex items-center justify-center space-x-2"
              >
                <FileText className="w-5 h-5" />
                <span>Export JSON</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CloudAccessVisualizer;