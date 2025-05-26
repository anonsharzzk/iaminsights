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
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [userInfo, setUserInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statistics, setStatistics] = useState(null);
  const [allUsers, setAllUsers] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState("all");
  const [selectedAccessType, setSelectedAccessType] = useState("all");
  const [showLegend, setShowLegend] = useState(true);
  const [graphLayout, setGraphLayout] = useState("cose-bilkent");
  const [selectedNode, setSelectedNode] = useState(null);
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
  };

  // Fetch statistics on component mount
  useEffect(() => {
    fetchStatistics();
    fetchAllUsers();
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

  const handleSearch = async () => {
    if (!searchEmail.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/search/${encodeURIComponent(searchEmail)}`);
      const data = response.data;
      
      if (data.user) {
        setUserInfo(data.user);
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

            {/* Graph Visualization */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                <BarChart3 className="w-5 h-5 mr-2" />
                Access Graph Visualization
              </h3>
              
              {graphData.nodes.length > 0 ? (
                <div className="bg-slate-900 rounded-lg border border-slate-600" style={{ height: '600px' }}>
                  <CytoscapeComponent
                    elements={[...graphData.nodes, ...graphData.edges]}
                    style={{ width: '100%', height: '100%' }}
                    stylesheet={cytoscapeStylesheet}
                    layout={cytoscapeLayout}
                    cy={(cy) => {
                      cyRef.current = cy;
                      
                      // Add click event to show node info
                      cy.on('tap', 'node', function(evt) {
                        const node = evt.target;
                        const data = node.data();
                        console.log('Node clicked:', data);
                      });
                    }}
                  />
                </div>
              ) : (
                <div className="bg-slate-900 rounded-lg border border-slate-600 h-96 flex items-center justify-center">
                  <div className="text-center text-slate-400">
                    <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>No graph data available</p>
                  </div>
                </div>
              )}
            </div>

            {/* Legend */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Graph Legend</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="w-8 h-8 bg-blue-600 rounded mx-auto mb-2"></div>
                  <p className="text-white text-sm font-medium">User</p>
                  <p className="text-slate-400 text-xs">Central node</p>
                </div>
                <div className="text-center">
                  <div className="w-8 h-8 bg-orange-500 rounded mx-auto mb-2"></div>
                  <p className="text-white text-sm font-medium">Providers</p>
                  <p className="text-slate-400 text-xs">AWS, GCP, Azure, Okta</p>
                </div>
                <div className="text-center">
                  <div className="w-8 h-8 bg-green-600 rounded mx-auto mb-2"></div>
                  <p className="text-white text-sm font-medium">Read Access</p>
                  <p className="text-slate-400 text-xs">View permissions</p>
                </div>
                <div className="text-center">
                  <div className="w-8 h-8 bg-red-600 rounded mx-auto mb-2"></div>
                  <p className="text-white text-sm font-medium">Admin Access</p>
                  <p className="text-slate-400 text-xs">Full control</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CloudAccessVisualizer;