import React from 'react';
import { Shield, Search, BarChart3, Users, Cloud, ArrowRight, CheckCircle, Eye, Download, Filter } from 'lucide-react';

const LandingPage = ({ onLoginClick }) => {
  const features = [
    {
      icon: <Search className="w-8 h-8 text-blue-400" />,
      title: "Instant User Search",
      description: "Search any user by email and instantly visualize their access across AWS, GCP, Azure, and Okta in an interactive graph."
    },
    {
      icon: <BarChart3 className="w-8 h-8 text-green-400" />,
      title: "Risk Analysis",
      description: "Automated risk scoring, privilege escalation detection, and security insights for every user and resource."
    },
    {
      icon: <Cloud className="w-8 h-8 text-purple-400" />,
      title: "Multi-Cloud Support",
      description: "Unified visibility across AWS, Google Cloud Platform, Microsoft Azure, and Okta identity management."
    },
    {
      icon: <Filter className="w-8 h-8 text-orange-400" />,
      title: "Advanced Filtering",
      description: "Filter by provider, access type, risk level, and more. Export data in CSV, JSON, or Excel formats."
    },
    {
      icon: <Eye className="w-8 h-8 text-cyan-400" />,
      title: "Interactive Visualization",
      description: "Beautiful, interactive graphs with multiple layout options, hover effects, and detailed node information."
    },
    {
      icon: <Download className="w-8 h-8 text-indigo-400" />,
      title: "Enterprise Export",
      description: "Export access reports for compliance, generate audit trails, and create executive summaries."
    }
  ];

  const benefits = [
    "Instant visibility into who has access to what across all cloud providers",
    "Automated risk analysis and privilege escalation detection",
    "Beautiful interactive graphs that make complex data easy to understand",
    "Enterprise-grade security with role-based access control",
    "JSON import for easy data integration from existing systems",
    "Comprehensive export capabilities for compliance and auditing"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="bg-slate-800/80 backdrop-blur-sm border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">Cloud Access Visualizer</h1>
            </div>
            <button
              onClick={onLoginClick}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center space-x-2"
            >
              <span>Login</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Visualize Cloud Access
            <span className="block text-blue-400">Like Never Before</span>
          </h1>
          <p className="text-xl text-slate-300 mb-8 max-w-3xl mx-auto">
            Get instant, interactive insights into user access across AWS, GCP, Azure, and Okta. 
            Make security auditing effortless with beautiful graph visualizations and comprehensive risk analysis.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={onLoginClick}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg font-semibold text-lg transition-colors duration-200 flex items-center justify-center space-x-2"
            >
              <span>Get Started</span>
              <ArrowRight className="w-5 h-5" />
            </button>
            <button className="border border-slate-600 hover:bg-slate-800 text-white px-8 py-4 rounded-lg font-semibold text-lg transition-colors duration-200">
              View Demo
            </button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-800/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">
              Everything You Need for Cloud Security
            </h2>
            <p className="text-xl text-slate-300 max-w-2xl mx-auto">
              Powerful features designed for security teams, IT administrators, and compliance professionals.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700 hover:border-slate-600 transition-colors duration-200"
              >
                <div className="flex items-center mb-4">
                  {feature.icon}
                  <h3 className="text-xl font-semibold text-white ml-3">{feature.title}</h3>
                </div>
                <p className="text-slate-300">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl font-bold text-white mb-6">
                Why Security Teams Love Our Platform
              </h2>
              <p className="text-lg text-slate-300 mb-8">
                Transform complex cloud access data into clear, actionable insights. 
                Our platform makes it easy to understand who has access to what, 
                identify security risks, and maintain compliance.
              </p>
              
              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <CheckCircle className="w-6 h-6 text-green-400 mt-0.5 flex-shrink-0" />
                    <span className="text-slate-300">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-8 border border-slate-700">
              <div className="text-center">
                <Users className="w-16 h-16 text-blue-400 mx-auto mb-4" />
                <h3 className="text-2xl font-bold text-white mb-4">Ready to Get Started?</h3>
                <p className="text-slate-300 mb-6">
                  Join security teams who trust our platform to visualize and secure their cloud access.
                </p>
                <button
                  onClick={onLoginClick}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold transition-colors duration-200"
                >
                  Access Dashboard
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-800/50 backdrop-blur-sm border-t border-slate-700 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="w-6 h-6 text-blue-400" />
              <span className="text-white font-semibold">Cloud Access Visualizer</span>
            </div>
            <div className="text-slate-400 text-sm">
              © 2024 Cloud Access Visualizer. Secure by design.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;