# Cloud Access Visualizer - Quick Start Guide

## 🚀 Quick Deployment

### Prerequisites
- Docker Desktop installed
- Git installed
- 4GB+ RAM available

### 1. Clone Repository
```bash
git clone https://github.com/your-username/cloud-access-visualizer.git
cd cloud-access-visualizer
```

### 2. Quick Start (Development)
```bash
# Automatic deployment
./scripts/deploy.sh development

# Manual deployment
cp .env.example .env
docker-compose up -d
```

### 3. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

### 4. Default Login
- **Email**: `adminn@iamsharan.com`
- **Password**: `Testing@123`

### 5. Import Sample Data
1. Go to "Import Data" tab
2. Select provider (AWS/GCP/Azure/Okta)
3. Upload sample files from `sample-data/` folder
4. Explore the visualizations!

## 🏭 Production Deployment

### 1. Configure Environment
```bash
cp .env.example .env
nano .env  # Update with production values
```

### 2. Deploy Production Stack
```bash
./scripts/deploy.sh production
```

### 3. Setup SSL (Optional)
```bash
# Generate Let's Encrypt certificates
certbot --nginx -d yourdomain.com
```

## 🔧 Management Commands

### View Logs
```bash
docker-compose logs -f
```

### Backup Data
```bash
./scripts/backup.sh
```

### Restore Data
```bash
./scripts/restore.sh backup_20241219_120000.tar.gz
```

### Stop Services
```bash
docker-compose down
```

## 📞 Support
- Issues: GitHub Issues
- Documentation: README.md
- Email: support@cloudaccessvisualizer.com