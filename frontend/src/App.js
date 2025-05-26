import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import CytoscapeComponent from "react-cytoscapejs";
import cytoscape from "cytoscape";
import coseBilkent from "cytoscape-cose-bilkent";
import { Search, Users, Shield, BarChart3, Cloud, Server, Database, Key, Download, RefreshCw, Filter, Eye, Settings } from "lucide-react";

// Register the layout extension
cytoscape.use(coseBilkent);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CloudAccessVisualizer = () => {
  const [searchEmail, setSearchEmail] = useState("");
  const [searchResource, setSearchResource] = useState("");
  const [searchType, setSearchType] = useState("user"); // user, resource
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
  const [activeTab, setActiveTab] = useState("search"); // search, import, analytics, export
  const [importFile, setImportFile] = useState(null);
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

  const cytoscapeLayout = {
    name: graphLayout,
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
  };

  // Alternative layouts
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
        boundingBox: undefined,
        avoidOverlap: true,
        nodeDimensionsIncludeLabels: false,
        spacingFactor: undefined,
        radius: undefined,
        startAngle: 3 / 2 * Math.PI,
        sweep: undefined,
        clockwise: true,
        sort: undefined,
        animate: true,
        animationDuration: 500
      },
      'grid': {
        name: 'grid',
        fit: true,
        padding: 30,
        boundingBox: undefined,
        avoidOverlap: true,
        avoidOverlapPadding: 10,
        nodeDimensionsIncludeLabels: false,
        spacingFactor: undefined,
        condense: false,
        rows: undefined,
        cols: undefined,
        position: function(node) {},
        sort: undefined,
        animate: true,
        animationDuration: 500
      },
      'breadthfirst': {
        name: 'breadthfirst',
        fit: true,
        directed: false,
        padding: 30,
        circle: false,
        grid: false,
        spacingFactor: 1.75,
        boundingBox: undefined,
        avoidOverlap: true,
        nodeDimensionsIncludeLabels: false,
        roots: undefined,
        maximal: false,
        animate: true,
        animationDuration: 500
      }
    };
    
    return layouts[layoutName] || layouts['cose-bilkent'];
  };

  // Filter graph data based on selected filters
  const getFilteredGraphData = () => {
    if (!userInfo) return { nodes: [], edges: [] };

    let filteredNodes = [...graphData.nodes];
    let filteredEdges = [...graphData.edges];

    // Filter by provider
    if (selectedProvider !== "all") {
      const allowedNodeIds = new Set();
      
      // Always include user node
      const userNode = filteredNodes.find(node => node.data.type === "user");
      if (userNode) allowedNodeIds.add(userNode.data.id);
      
      // Include selected provider and its children
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
      
      // Always include user, provider, and service nodes
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

  // Export graph as PNG
  const exportGraphPNG = () => {
    if (cyRef.current) {
      const png64 = cyRef.current.png();
      const link = document.createElement('a');
      link.download = `cloud-access-${searchEmail}-${Date.now()}.png`;
      link.href = png64;
      link.click();
    }
  };

  // Reset graph view
  const resetGraphView = () => {
    if (cyRef.current) {
      cyRef.current.fit();
      cyRef.current.center();
    }
  };

  // Change graph layout
  const changeLayout = (layoutName) => {
    setGraphLayout(layoutName);
    if (cyRef.current) {
      const layout = cyRef.current.layout(getLayoutConfig(layoutName));
      layout.run();
    }
  };

  // Fetch statistics on component mount
  useEffect(() => {
    fetchStatistics();
    fetchAllUsers();
    fetchAnalytics();
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
        // Transform the graph data for cytoscape
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



  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleUserSelect = (email) => {
    setSearchEmail(email);
    handleSearch();
  };

  // Provider icons mapping
  const getProviderIcon = (provider) => {
    switch (provider) {
      case 'aws': return '☁️';
      case 'gcp': return '🌩️';
      case 'azure': return '⭐';
      case 'okta': return '🔐';
      default: return '🌐';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="bg-slate-800/80 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">Cloud Access Visualizer</h1>
            </div>
            <div className="text-sm text-slate-300">
              Security & IT Teams Portal
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-8 mb-8 border border-slate-700">
          <div className="text-center mb-6">
            <h2 className="text-3xl font-bold text-white mb-2">
              Who has access to what?
            </h2>
            <p className="text-slate-300 text-lg">
              Search for any user to visualize their access across AWS, GCP, Azure, and Okta
            </p>
          </div>
          
          <div className="max-w-2xl mx-auto">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-slate-400" />
              </div>
              <input
                type="email"
                value={searchEmail}
                onChange={(e) => setSearchEmail(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Enter user email (e.g., alice@company.com)"
                className="block w-full pl-10 pr-20 py-4 text-lg border border-slate-600 rounded-lg bg-slate-700/50 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
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
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
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
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 mb-8 border border-slate-700">
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
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700 mb-6">
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
                        console.log('Node clicked:', data);
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
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700 mt-6">
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
      </div>
    </div>
  );
};

export default CloudAccessVisualizer;