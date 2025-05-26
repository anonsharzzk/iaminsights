#!/bin/bash

# Cloud Access Visualizer - Complete End-to-End Testing & Deployment Script
# Usage: ./scripts/deploy-and-test.sh [cleanup]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="cloud-access-visualizer"
FRONTEND_PORT=3000
BACKEND_PORT=8001
MONGODB_PORT=27017

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within expected time"
    return 1
}

# Function to test API endpoint
test_api_endpoint() {
    local method=$1
    local url=$2
    local expected_status=$3
    local description=$4
    local data=${5:-""}
    local auth_header=${6:-""}

    print_status "Testing: $description"
    
    local curl_cmd="curl -s -w '%{http_code}' -o /tmp/api_response"
    
    if [ -n "$auth_header" ]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $auth_header'"
    fi
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        curl_cmd="$curl_cmd -X POST -H 'Content-Type: application/json' -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '$url'"
    
    local status_code=$(eval $curl_cmd)
    
    if [ "$status_code" = "$expected_status" ]; then
        print_success "✓ $description (Status: $status_code)"
        return 0
    else
        print_error "✗ $description (Expected: $expected_status, Got: $status_code)"
        if [ -f /tmp/api_response ]; then
            echo "Response: $(cat /tmp/api_response)"
        fi
        return 1
    fi
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up previous deployment..."
    
    # Stop and remove containers
    docker-compose down -v --remove-orphans 2>/dev/null || true
    
    # Remove images
    docker rmi $(docker images "${PROJECT_NAME}*" -q) 2>/dev/null || true
    
    # Clean up temporary files
    rm -f /tmp/api_response /tmp/auth_token
    
    print_success "Cleanup completed"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=0
    
    if ! command_exists docker; then
        print_error "Docker is not installed"
        missing_deps=1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed"
        missing_deps=1
    fi
    
    if ! command_exists curl; then
        print_error "curl is not installed"
        missing_deps=1
    fi
    
    if ! command_exists jq; then
        print_warning "jq is not installed (optional, for better JSON parsing)"
    fi
    
    if [ $missing_deps -eq 1 ]; then
        print_error "Please install missing dependencies and try again"
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        
        # Generate a secure JWT secret
        if command_exists openssl; then
            JWT_SECRET=$(openssl rand -hex 32)
            sed -i "s/your-super-secure-jwt-secret-key-change-in-production.*/$JWT_SECRET/" .env
            print_success "Generated secure JWT secret"
        fi
    fi
    
    # Create necessary directories
    mkdir -p logs backups data/mongodb
    
    print_success "Environment setup completed"
}

# Function to build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Build and start all services
    docker-compose up -d --build
    
    print_success "Services started"
}

# Function to verify service health
verify_services() {
    print_status "Verifying service health..."
    
    # Wait for MongoDB
    wait_for_service "MongoDB" "http://localhost:$MONGODB_PORT" || {
        print_error "MongoDB health check failed"
        docker-compose logs mongodb
        exit 1
    }
    
    # Wait for Backend
    wait_for_service "Backend API" "http://localhost:$BACKEND_PORT/api/" || {
        print_error "Backend health check failed"
        docker-compose logs backend
        exit 1
    }
    
    # Wait for Frontend
    wait_for_service "Frontend" "http://localhost:$FRONTEND_PORT" || {
        print_error "Frontend health check failed"
        docker-compose logs frontend
        exit 1
    }
    
    print_success "All services are healthy"
}

# Function to test authentication
test_authentication() {
    print_status "Testing authentication system..."
    
    local test_count=0
    local success_count=0
    
    # Test 1: Health check endpoint
    test_count=$((test_count + 1))
    if test_api_endpoint "GET" "http://localhost:$BACKEND_PORT/api/" "200" "API Health Check"; then
        success_count=$((success_count + 1))
    fi
    
    # Test 2: Login with default admin credentials
    test_count=$((test_count + 1))
    local login_data='{"email":"adminn@iamsharan.com","password":"Testing@123"}'
    if test_api_endpoint "POST" "http://localhost:$BACKEND_PORT/api/auth/login" "200" "Admin Login" "$login_data"; then
        success_count=$((success_count + 1))
        
        # Extract token for subsequent tests
        if command_exists jq; then
            AUTH_TOKEN=$(cat /tmp/api_response | jq -r '.access_token')
            echo "$AUTH_TOKEN" > /tmp/auth_token
            print_success "Authentication token obtained"
        fi
    fi
    
    # Test 3: Access protected endpoint without auth (should fail)
    test_count=$((test_count + 1))
    if test_api_endpoint "GET" "http://localhost:$BACKEND_PORT/api/users" "401" "Protected Endpoint Without Auth"; then
        success_count=$((success_count + 1))
    fi
    
    # Test 4: Access protected endpoint with auth (should succeed)
    if [ -f /tmp/auth_token ]; then
        test_count=$((test_count + 1))
        local token=$(cat /tmp/auth_token)
        if test_api_endpoint "GET" "http://localhost:$BACKEND_PORT/api/users" "200" "Protected Endpoint With Auth" "" "$token"; then
            success_count=$((success_count + 1))
        fi
    fi
    
    print_status "Authentication tests: $success_count/$test_count passed"
    return $((test_count - success_count))
}

# Function to test core functionality
test_core_functionality() {
    print_status "Testing core functionality..."
    
    local test_count=0
    local success_count=0
    local token=""
    
    if [ -f /tmp/auth_token ]; then
        token=$(cat /tmp/auth_token)
    else
        print_warning "No auth token available, skipping authenticated tests"
        return 0
    fi
    
    # Test 1: Get provider statistics
    test_count=$((test_count + 1))
    if test_api_endpoint "GET" "http://localhost:$BACKEND_PORT/api/providers" "200" "Provider Statistics" "" "$token"; then
        success_count=$((success_count + 1))
    fi
    
    # Test 2: Search for user
    test_count=$((test_count + 1))
    if test_api_endpoint "GET" "http://localhost:$BACKEND_PORT/api/search/alice@company.com" "200" "User Search" "" "$token"; then
        success_count=$((success_count + 1))
    fi
    
    # Test 3: Get analytics
    test_count=$((test_count + 1))
    if test_api_endpoint "GET" "http://localhost:$BACKEND_PORT/api/analytics" "200" "Analytics Dashboard" "" "$token"; then
        success_count=$((success_count + 1))
    fi
    
    # Test 4: Search for non-existent user
    test_count=$((test_count + 1))
    if test_api_endpoint "GET" "http://localhost:$BACKEND_PORT/api/search/nonexistent@example.com" "200" "Non-existent User Search" "" "$token"; then
        success_count=$((success_count + 1))
    fi
    
    print_status "Core functionality tests: $success_count/$test_count passed"
    return $((test_count - success_count))
}

# Function to test frontend accessibility
test_frontend() {
    print_status "Testing frontend accessibility..."
    
    local test_count=0
    local success_count=0
    
    # Test 1: Frontend loads
    test_count=$((test_count + 1))
    if curl -f -s "http://localhost:$FRONTEND_PORT" >/dev/null; then
        print_success "✓ Frontend is accessible"
        success_count=$((success_count + 1))
    else
        print_error "✗ Frontend is not accessible"
    fi
    
    # Test 2: Static assets load
    test_count=$((test_count + 1))
    if curl -f -s "http://localhost:$FRONTEND_PORT/static/js" >/dev/null 2>&1 || curl -f -s "http://localhost:$FRONTEND_PORT" | grep -q "react"; then
        print_success "✓ Frontend React app is loaded"
        success_count=$((success_count + 1))
    else
        print_error "✗ Frontend React app failed to load"
    fi
    
    print_status "Frontend tests: $success_count/$test_count passed"
    return $((test_count - success_count))
}

# Function to load sample data
load_sample_data() {
    print_status "Loading sample data..."
    
    local token=""
    if [ -f /tmp/auth_token ]; then
        token=$(cat /tmp/auth_token)
    else
        print_warning "No auth token available, skipping sample data loading"
        return 0
    fi
    
    local loaded_count=0
    
    # Load each sample file
    for sample_file in sample-data/*.json; do
        if [ -f "$sample_file" ]; then
            local filename=$(basename "$sample_file")
            print_status "Loading $filename..."
            
            if curl -f -s -X POST \
                -H "Authorization: Bearer $token" \
                -F "file=@$sample_file" \
                "http://localhost:$BACKEND_PORT/api/import/json" >/dev/null; then
                print_success "✓ Loaded $filename"
                loaded_count=$((loaded_count + 1))
            else
                print_warning "✗ Failed to load $filename"
            fi
        fi
    done
    
    print_success "Loaded $loaded_count sample data files"
}

# Function to display service information
display_service_info() {
    print_status "Deployment completed successfully!"
    echo ""
    echo "🌐 Service URLs:"
    echo "   Frontend:  http://localhost:$FRONTEND_PORT"
    echo "   Backend:   http://localhost:$BACKEND_PORT"
    echo "   API Docs:  http://localhost:$BACKEND_PORT/docs"
    echo "   MongoDB:   mongodb://localhost:$MONGODB_PORT"
    echo ""
    echo "🔐 Default Admin Credentials:"
    echo "   Email:     adminn@iamsharan.com"
    echo "   Password:  Testing@123"
    echo ""
    echo "📊 Sample Data:"
    echo "   - Comprehensive multi-cloud sample"
    echo "   - AWS IAM sample"
    echo "   - GCP IAM sample"
    echo "   - Azure RBAC sample"
    echo "   - Okta access sample"
    echo ""
    echo "🛠️  Management Commands:"
    echo "   View logs:     docker-compose logs -f"
    echo "   Stop services: docker-compose down"
    echo "   Backup data:   ./scripts/backup.sh"
    echo "   Cleanup:       $0 cleanup"
    echo ""
    print_success "🎉 Cloud Access Visualizer is ready to use!"
}

# Function to run comprehensive tests
run_tests() {
    print_status "Running comprehensive test suite..."
    
    local total_failures=0
    
    # Test authentication
    test_authentication
    total_failures=$((total_failures + $?))
    
    # Test core functionality
    test_core_functionality
    total_failures=$((total_failures + $?))
    
    # Test frontend
    test_frontend
    total_failures=$((total_failures + $?))
    
    # Load sample data
    load_sample_data
    
    if [ $total_failures -eq 0 ]; then
        print_success "🎉 All tests passed!"
        return 0
    else
        print_warning "⚠️  Some tests failed ($total_failures failures)"
        return 1
    fi
}

# Main execution
main() {
    echo "🚀 Cloud Access Visualizer - End-to-End Deployment & Testing"
    echo "============================================================"
    
    # Handle cleanup argument
    if [ "$1" = "cleanup" ]; then
        cleanup
        exit 0
    fi
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # Start services
    start_services
    
    # Verify services are healthy
    verify_services
    
    # Run comprehensive tests
    run_tests
    
    # Display service information
    display_service_info
    
    print_success "Deployment and testing completed successfully!"
}

# Trap to cleanup on exit
trap cleanup EXIT

# Execute main function
main "$@"