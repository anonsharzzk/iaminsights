# 🛡️ Cloud Access Visualizer

> **Enterprise-grade platform for visualizing and analyzing user access across AWS, GCP, Azure, and Okta with interactive graph-based insights.**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![React](https://img.shields.io/badge/React-18.0-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green.svg)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Screenshots](#screenshots)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Options](#deployment-options)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## 🌟 Overview

Cloud Access Visualizer is a cutting-edge security platform that transforms complex cloud IAM data into clear, actionable insights. Built for security teams, IT administrators, and compliance professionals, it provides instant visibility into "who has access to what" across multiple cloud providers.

### 🎯 Problem Statement

Modern organizations struggle with:
- **Complex access management** across multiple cloud providers
- **Security risks** from privilege escalation and over-permissioning
- **Audit challenges** with scattered access data
- **Time-consuming manual reviews** of user permissions
- **Lack of cross-cloud visibility** into access patterns

### 💡 Solution

Our platform delivers:
- **Instant visual insights** through interactive graph visualization
- **Automated risk analysis** with privilege escalation detection
- **Unified cross-cloud view** of all user access
- **Professional reporting** for compliance and audits
- **Secure user management** with role-based access control

## ✨ Key Features

### 🔍 **Search & Visualization**
- **User Search**: Enter any email to instantly see their access across all cloud providers
- **Resource Search**: Find who has access to specific resources (e.g., "production-bucket")
- **Interactive Graphs**: Beautiful cytoscape.js visualizations with multiple layout options
- **Advanced Filtering**: Filter by provider, access type, risk level, and more

### 🛡️ **Security Analytics**
- **Risk Scoring**: Automated 0-100 risk assessment for every user
- **Privilege Escalation Detection**: Identify potential security paths
- **Cross-Provider Analysis**: Flag users with admin access across multiple clouds
- **Unused Privilege Detection**: Highlight stale access for cleanup

### 📊 **Enterprise Features**
- **Data Import**: JSON file upload with provider-specific templates
- **Export Capabilities**: CSV, Excel, and JSON exports for compliance
- **Analytics Dashboard**: Comprehensive security insights and metrics
- **Audit Trails**: Complete access history and change tracking

### 🔐 **Authentication & User Management**
- **Secure Authentication**: JWT-based login with bcrypt password hashing
- **Role-Based Access Control**: Admin and User role permissions
- **User Management**: Admin interface for creating, editing, and managing users
- **Profile Management**: Users can update their own credentials

### 🌐 **Multi-Cloud Support**
- **AWS**: IAM, S3, EC2, RDS, Lambda, and more
- **Google Cloud Platform**: Compute Engine, Cloud Storage, BigQuery
- **Microsoft Azure**: Storage, Virtual Machines, Key Vault
- **Okta**: SSO applications and identity management

## 📱 Screenshots

### Landing Page
![Landing Page](docs/images/landing-page.png)
*Professional landing page with clear value proposition*

### Interactive Graph Visualization
![Graph Visualization](docs/images/graph-visualization.png)
*Real-time interactive graph showing user access across cloud providers*

### Analytics Dashboard
![Analytics Dashboard](docs/images/analytics-dashboard.png)
*Comprehensive security analytics with risk insights*

### User Management
![User Management](docs/images/user-management.png)
*Admin interface for managing users and permissions*

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Database     │
│   (React.js)    │◄──►│   (FastAPI)     │◄──►│   (MongoDB)     │
│                 │    │                 │    │                 │
│ • Landing Page  │    │ • Authentication│    │ • User Data     │
│ • Login System  │    │ • User Mgmt     │    │ • Access Data   │
│ • Dashboard     │    │ • Search APIs   │    │ • Analytics     │
│ • Graph Viz     │    │ • Analytics     │    │ • Audit Logs    │
│ • User Mgmt     │    │ • Import/Export │    │                 │
│ • Settings      │    │ • Risk Analysis │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

**Frontend**:
- React.js 18+ with modern hooks
- Cytoscape.js for graph visualization
- Tailwind CSS for styling
- Axios for API communication
- Lucide React for icons

**Backend**:
- FastAPI for high-performance APIs
- MongoDB with Motor (async driver)
- JWT authentication with bcrypt
- Pandas for data processing
- Pydantic for data validation

**Infrastructure**:
- Docker & Docker Compose for containerization
- MongoDB 7.0 for data persistence
- nginx (optional) for reverse proxy
- SSL/TLS support for production

## 📋 Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows with WSL2
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 10GB free space
- **Network**: Internet access for container downloads

### Required Software

#### Option 1: Docker (Recommended)
```bash
# Docker Desktop (includes Docker Compose)
# Download from: https://www.docker.com/products/docker-desktop

# Verify installation
docker --version
docker-compose --version
```

#### Option 2: Manual Installation
```bash
# Node.js 18+ and Yarn
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g yarn

# Python 3.11+
sudo apt-get install python3.11 python3.11-pip python3.11-venv

# MongoDB 7.0
# Follow MongoDB installation guide for your OS
```

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/your-username/cloud-access-visualizer.git
cd cloud-access-visualizer
```

2. **Configure environment variables**
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional - defaults work for development)
nano .env
```

3. **Start the application**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

4. **Access the application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

5. **Default Admin Login**
- **Email**: `adminn@iamsharan.com`
- **Password**: `Testing@123`

### Manual Installation

<details>
<summary>Click to expand manual installation steps</summary>

1. **Setup MongoDB**
```bash
# Start MongoDB service
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Create database and user
mongo
> use cloud_access
> db.createUser({user: "admin", pwd: "cloudaccess123", roles: ["readWrite"]})
> exit
```

2. **Setup Backend**
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
echo "MONGO_URL=mongodb://admin:cloudaccess123@localhost:27017/cloud_access" > .env
echo "DB_NAME=cloud_access" >> .env
echo "JWT_SECRET_KEY=your-super-secure-secret-key" >> .env

# Start backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

3. **Setup Frontend**
```bash
cd frontend

# Install dependencies
yarn install

# Setup environment
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

# Start frontend
yarn start
```

</details>

## 🐳 Deployment Options

### Development Deployment
```bash
# Start with hot reload
docker-compose up

# Access services:
# Frontend: http://localhost:3000
# Backend: http://localhost:8001
# MongoDB: localhost:27017
```

### Production Deployment

1. **Update environment variables**
```bash
# Create production environment file
cp .env.example .env.production

# Edit with production values
nano .env.production
```

2. **Use production compose file**
```bash
# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Optional: Use nginx reverse proxy
docker-compose -f docker-compose.prod.yml -f docker-compose.nginx.yml up -d
```

3. **SSL/TLS Configuration**
```bash
# Using Let's Encrypt with certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Cloud Deployment

#### AWS ECS
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t cloud-access-visualizer .
docker tag cloud-access-visualizer:latest <account>.dkr.ecr.us-east-1.amazonaws.com/cloud-access-visualizer:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/cloud-access-visualizer:latest
```

#### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/cloud-access-visualizer
gcloud run deploy --image gcr.io/PROJECT-ID/cloud-access-visualizer --platform managed
```

#### Azure Container Instances
```bash
# Create resource group and deploy
az group create --name cloud-access-rg --location eastus
az container create --resource-group cloud-access-rg --name cloud-access-app --image your-registry/cloud-access-visualizer
```

## ⚙️ Configuration

### Environment Variables

#### Backend Configuration
```bash
# Database
MONGO_URL=mongodb://username:password@host:port/database
DB_NAME=cloud_access

# Security
JWT_SECRET_KEY=your-super-secure-secret-key-change-in-production

# Optional: Cloud Provider APIs (for real data integration)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
GCP_SERVICE_ACCOUNT_JSON=path-to-service-account.json
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
OKTA_DOMAIN=your-okta-domain
OKTA_API_TOKEN=your-okta-api-token
```

#### Frontend Configuration
```bash
# API Endpoints
REACT_APP_BACKEND_URL=http://localhost:8001

# Optional: Analytics
REACT_APP_GOOGLE_ANALYTICS_ID=GA-TRACKING-ID
REACT_APP_SENTRY_DSN=your-sentry-dsn
```

### Database Configuration

#### MongoDB Indexes (Automatic)
```javascript
// Performance indexes created automatically
db.users.createIndex({ "email": 1 }, { unique: true });
db.user_access.createIndex({ "user_email": 1 }, { unique: true });
db.user_access.createIndex({ "overall_risk_score": -1 });
```

#### Backup Configuration
```bash
# Automated MongoDB backups
docker exec cloud-access-mongodb mongodump --out /backup/$(date +%Y%m%d_%H%M%S)

# Restore from backup
docker exec cloud-access-mongodb mongorestore /backup/20231215_120000
```

## 📚 Usage Guide

### Getting Started

1. **Access the Platform**
   - Navigate to your deployment URL (e.g., http://localhost:3000)
   - View the landing page and platform overview

2. **Login**
   - Click "Login" to access the authentication page
   - Use default admin credentials or your assigned login

3. **First Steps**
   - Explore the dashboard and navigation
   - Try searching for sample users (alice@company.com, bob@company.com)
   - View the interactive graph visualization

### User Search & Visualization

#### Search by User Email
```
1. Go to "Access Visualizer" tab
2. Select "Search by User"
3. Enter email: alice@company.com
4. Click "Search"
5. Explore the interactive graph:
   - User (center) → Providers → Services → Resources
   - Color-coded by provider and access type
   - Click nodes for details
```

#### Search by Resource
```
1. Select "Search by Resource" 
2. Enter resource name: "production"
3. View all users with access to matching resources
4. Export results for reporting
```

### Data Import

#### JSON File Format
```json
{
  "metadata": {
    "import_date": "2024-12-19T10:30:00Z",
    "source": "aws_iam_audit",
    "description": "AWS IAM access audit data"
  },
  "users": [
    {
      "user_email": "user@company.com",
      "user_name": "John Doe",
      "department": "Engineering",
      "job_title": "DevOps Engineer",
      "resources": [
        {
          "provider": "aws",
          "service": "S3",
          "resource_type": "bucket",
          "resource_name": "production-data-bucket",
          "access_type": "read",
          "risk_level": "medium",
          "is_privileged": false,
          "mfa_required": true
        }
      ]
    }
  ]
}
```

#### Import Steps
```
1. Go to "Import Data" tab
2. Select provider (AWS, GCP, Azure, Okta)
3. View sample format for reference
4. Upload your JSON file
5. Review import results
6. Data automatically analyzed for risks
```

### Analytics & Reporting

#### Security Dashboard
- **Risk Distribution**: View user risk levels (Low/Medium/High/Critical)
- **Top Privileged Users**: Identify users with highest permissions
- **Cross-Provider Admins**: Users with admin access across multiple clouds
- **Privilege Escalation Risks**: Potential security paths

#### Export Options
- **CSV**: Spreadsheet-ready access reports
- **Excel**: Executive-formatted reports with charts
- **JSON**: API-compatible data format
- **PNG**: Graph visualizations for presentations

### User Management (Admin Only)

#### Creating Users
```
1. Go to "User Management" (admin only)
2. Click "Add User"
3. Enter email, password, and role
4. User can login with provided credentials
```

#### Managing Users
- **Edit**: Update email, reset password, activate/deactivate
- **Delete**: Remove users (admin cannot delete themselves)
- **Roles**: Assign Admin or User permissions

### Advanced Features

#### Graph Controls
- **Layouts**: Smart, Circle, Grid, Hierarchy visualizations
- **Filters**: Provider, access type, risk level filtering
- **Export**: PNG download for documentation
- **Legend**: Visual guide to node types and colors

#### Risk Analysis
- **Automated Scoring**: 0-100 risk score per user
- **Escalation Paths**: Multi-step privilege escalation detection
- **Recommendations**: Actionable security improvements
- **Compliance Reports**: Audit-ready documentation

## 📡 API Documentation

### Authentication Endpoints

#### POST /api/auth/login
```json
// Request
{
  "email": "admin@company.com",
  "password": "securepassword"
}

// Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "user-id",
    "email": "admin@company.com",
    "role": "admin"
  }
}
```

#### GET /api/auth/me
```json
// Headers: Authorization: Bearer <token>
// Response
{
  "id": "user-id",
  "email": "admin@company.com",
  "role": "admin",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Search Endpoints

#### GET /api/search/{email}
```json
// Response
{
  "user": {
    "user_email": "alice@company.com",
    "user_name": "Alice Johnson",
    "resources": [...],
    "overall_risk_score": 75.5
  },
  "graph_data": {
    "nodes": [...],
    "edges": [...]
  }
}
```

#### GET /api/search/resource/{resource_name}
```json
// Response
[
  {
    "resource": {
      "provider": "aws",
      "service": "S3",
      "resource_name": "production-bucket",
      "access_type": "admin"
    },
    "users_with_access": ["alice@company.com"],
    "total_users": 1
  }
]
```

### Analytics Endpoints

#### GET /api/analytics
```json
// Response
{
  "total_users": 150,
  "total_resources": 1250,
  "risk_distribution": {
    "low": 45,
    "medium": 60,
    "high": 35,
    "critical": 10
  },
  "top_privileged_users": [...],
  "cross_provider_admins": 15,
  "privilege_escalation_risks": [...]
}
```

### Data Management Endpoints

#### POST /api/import/json
```bash
# Upload JSON file
curl -X POST "http://localhost:8001/api/import/json" \
  -H "Authorization: Bearer <token>" \
  -F "file=@access_data.json"
```

#### GET /api/export/{format}
```bash
# Export data in various formats
curl -X GET "http://localhost:8001/api/export/csv?provider=aws" \
  -H "Authorization: Bearer <token>" \
  -o access_report.csv
```

### User Management Endpoints

#### POST /api/users
```json
// Request
{
  "email": "newuser@company.com",
  "password": "securepassword",
  "role": "user"
}

// Response
{
  "id": "new-user-id",
  "email": "newuser@company.com",
  "role": "user",
  "is_active": true
}
```

For complete API documentation, visit: http://localhost:8001/docs

## 🔒 Security

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication with configurable expiration
- **bcrypt Hashing**: Industry-standard password hashing with salt rounds
- **Role-Based Access**: Granular permissions for Admin and User roles
- **Protected Routes**: All API endpoints require valid authentication

### Data Security
- **Input Validation**: Comprehensive data validation using Pydantic models
- **SQL Injection Prevention**: MongoDB with parameterized queries
- **XSS Protection**: React's built-in XSS prevention and CSP headers
- **CSRF Protection**: SameSite cookies and CSRF tokens

### Infrastructure Security
- **Container Security**: Non-root users in Docker containers
- **Network Isolation**: Docker network segmentation
- **Secret Management**: Environment variables for sensitive data
- **Health Checks**: Container health monitoring and automatic restarts

### Compliance Features
- **Audit Logging**: Complete access and change history
- **Data Export**: Compliance reporting in multiple formats
- **Access Reviews**: Visual access reviews and certification
- **Risk Assessment**: Automated risk scoring and reporting

### Security Best Practices

#### Production Deployment
```bash
# Change default credentials
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
export ADMIN_EMAIL="admin@yourcompany.com"
export ADMIN_PASSWORD="$(openssl rand -base64 32)"

# Use TLS/SSL
# Enable firewall rules
# Regular security updates
# Monitor access logs
```

#### Database Security
```bash
# Enable MongoDB authentication
# Use strong passwords
# Enable encryption at rest
# Regular backups
# Network access restrictions
```

## 🤝 Contributing

We welcome contributions from the community! Please follow these guidelines:

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/your-username/cloud-access-visualizer.git
cd cloud-access-visualizer

# Create development branch
git checkout -b feature/your-feature-name

# Start development environment
docker-compose up

# Make changes and test
# Submit pull request
```

### Code Standards
- **Frontend**: ESLint + Prettier for React/JavaScript
- **Backend**: Black + isort for Python formatting
- **Testing**: Comprehensive test coverage required
- **Documentation**: Update README and API docs

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Update documentation
5. Submit pull request with clear description
6. Address code review feedback

### Reporting Issues
- Use GitHub Issues for bug reports
- Include reproduction steps
- Provide environment details
- Add relevant logs/screenshots

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Cloud Access Visualizer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🆘 Support

### Getting Help
- **Documentation**: Comprehensive guides and API reference
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and questions
- **Wiki**: Additional guides and tutorials

### Professional Support
For enterprise deployments, custom integrations, or professional support:
- Email: support@cloudaccessvisualizer.com
- Website: https://cloudaccessvisualizer.com
- Enterprise: Contact for SLA and priority support

### Community
- **GitHub**: https://github.com/your-username/cloud-access-visualizer
- **Discord**: Join our community server
- **Twitter**: @CloudAccessViz
- **LinkedIn**: Cloud Access Visualizer

---

**⭐ If this project helps you, please give it a star on GitHub! ⭐**

Built with ❤️ by the Cloud Access Visualizer team.