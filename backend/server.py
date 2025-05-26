from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Cloud Access Visualization API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums for cloud providers and access types
class CloudProvider(str, Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    OKTA = "okta"

class AccessType(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"
    USER = "user"
    EXECUTE = "execute"
    DELETE = "delete"

# Database Models
class CloudResource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: CloudProvider
    service: str  # e.g., "S3", "IAM", "Compute Engine", "Salesforce"
    resource_name: str  # e.g., "bucket-name", "vm-instance-1"
    access_type: AccessType
    description: Optional[str] = None

class UserAccess(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str
    user_name: str
    resources: List[CloudResource]
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "user", "provider", "service", "resource"
    provider: Optional[str] = None
    access_type: Optional[str] = None
    color: Optional[str] = None

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class SearchResponse(BaseModel):
    user: Optional[UserAccess]
    graph_data: GraphData

# Sample data initialization
async def init_sample_data():
    """Initialize the database with realistic sample data"""
    # Check if data already exists
    existing_users = await db.user_access.count_documents({})
    if existing_users > 0:
        return
    
    # Sample users with realistic cloud access patterns
    sample_users = [
        {
            "user_email": "alice@company.com",
            "user_name": "Alice Johnson",
            "resources": [
                # AWS Resources
                {"provider": "aws", "service": "S3", "resource_name": "production-data-bucket", "access_type": "read", "description": "Read access to production data"},
                {"provider": "aws", "service": "S3", "resource_name": "backup-bucket", "access_type": "write", "description": "Write access for backups"},
                {"provider": "aws", "service": "EC2", "resource_name": "web-server-01", "access_type": "admin", "description": "Full admin access to web servers"},
                {"provider": "aws", "service": "IAM", "resource_name": "developer-role", "access_type": "read", "description": "Read IAM policies"},
                {"provider": "aws", "service": "RDS", "resource_name": "prod-database", "access_type": "read", "description": "Read access to production database"},
                
                # GCP Resources
                {"provider": "gcp", "service": "Compute Engine", "resource_name": "analytics-vm", "access_type": "admin", "description": "Admin access to analytics VM"},
                {"provider": "gcp", "service": "Cloud Storage", "resource_name": "ml-models-bucket", "access_type": "write", "description": "Upload ML models"},
                {"provider": "gcp", "service": "BigQuery", "resource_name": "analytics-dataset", "access_type": "read", "description": "Query analytics data"},
                
                # Azure Resources
                {"provider": "azure", "service": "Storage", "resource_name": "logs-storage", "access_type": "read", "description": "Read application logs"},
                {"provider": "azure", "service": "Virtual Machines", "resource_name": "test-vm", "access_type": "write", "description": "Manage test environments"},
                
                # Okta Applications
                {"provider": "okta", "service": "Salesforce", "resource_name": "CRM System", "access_type": "user", "description": "Standard user access"},
                {"provider": "okta", "service": "Slack", "resource_name": "Team Communication", "access_type": "admin", "description": "Slack workspace admin"},
                {"provider": "okta", "service": "GitHub", "resource_name": "Code Repository", "access_type": "admin", "description": "Repository admin access"},
            ]
        },
        {
            "user_email": "bob@company.com",
            "user_name": "Bob Smith",
            "resources": [
                # AWS Resources
                {"provider": "aws", "service": "S3", "resource_name": "development-bucket", "access_type": "admin", "description": "Full access to dev environment"},
                {"provider": "aws", "service": "Lambda", "resource_name": "api-functions", "access_type": "write", "description": "Deploy serverless functions"},
                {"provider": "aws", "service": "CloudWatch", "resource_name": "monitoring", "access_type": "read", "description": "Monitor application metrics"},
                
                # GCP Resources
                {"provider": "gcp", "service": "Cloud Functions", "resource_name": "data-processing", "access_type": "admin", "description": "Manage data processing functions"},
                {"provider": "gcp", "service": "Pub/Sub", "resource_name": "event-streaming", "access_type": "write", "description": "Publish events"},
                
                # Azure Resources
                {"provider": "azure", "service": "App Service", "resource_name": "web-application", "access_type": "admin", "description": "Deploy web applications"},
                {"provider": "azure", "service": "Key Vault", "resource_name": "secrets-vault", "access_type": "read", "description": "Access application secrets"},
                
                # Okta Applications
                {"provider": "okta", "service": "JIRA", "resource_name": "Project Management", "access_type": "user", "description": "Track project issues"},
                {"provider": "okta", "service": "Confluence", "resource_name": "Documentation", "access_type": "admin", "description": "Manage team documentation"},
            ]
        },
        {
            "user_email": "carol@company.com",
            "user_name": "Carol Davis",
            "resources": [
                # AWS Resources (Security focused)
                {"provider": "aws", "service": "IAM", "resource_name": "security-policies", "access_type": "admin", "description": "Manage security policies"},
                {"provider": "aws", "service": "CloudTrail", "resource_name": "audit-logs", "access_type": "read", "description": "Review audit trails"},
                {"provider": "aws", "service": "GuardDuty", "resource_name": "threat-detection", "access_type": "admin", "description": "Manage threat detection"},
                
                # GCP Resources
                {"provider": "gcp", "service": "Security Center", "resource_name": "vulnerability-scan", "access_type": "admin", "description": "Security monitoring"},
                {"provider": "gcp", "service": "Cloud IAM", "resource_name": "access-control", "access_type": "admin", "description": "Manage access policies"},
                
                # Azure Resources
                {"provider": "azure", "service": "Security Center", "resource_name": "compliance-monitoring", "access_type": "admin", "description": "Monitor compliance"},
                {"provider": "azure", "service": "Active Directory", "resource_name": "user-management", "access_type": "admin", "description": "Manage user accounts"},
                
                # Okta Applications
                {"provider": "okta", "service": "Okta Admin", "resource_name": "Identity Management", "access_type": "admin", "description": "Manage identity and access"},
                {"provider": "okta", "service": "OneLogin", "resource_name": "SSO Portal", "access_type": "admin", "description": "Single sign-on management"},
            ]
        }
    ]
    
    # Insert sample data
    for user_data in sample_users:
        user_access = UserAccess(**user_data)
        await db.user_access.insert_one(user_access.dict())
    
    logging.info("Sample data initialized successfully")

# Helper function to generate graph data
def generate_graph_data(user_access: UserAccess) -> GraphData:
    """Generate graph nodes and edges for visualization"""
    nodes = []
    edges = []
    
    # Provider colors
    provider_colors = {
        "aws": "#FF9900",
        "gcp": "#4285F4", 
        "azure": "#0078D4",
        "okta": "#007DC1"
    }
    
    # Access type colors
    access_colors = {
        "read": "#28A745",
        "write": "#FFC107",
        "admin": "#DC3545",
        "owner": "#6F42C1",
        "user": "#17A2B8",
        "execute": "#FD7E14",
        "delete": "#E83E8C"
    }
    
    # User node (center)
    user_node = GraphNode(
        id=f"user-{user_access.user_email}",
        label=user_access.user_email,
        type="user",
        color="#6C757D"
    )
    nodes.append(user_node)
    
    # Group resources by provider
    provider_resources = {}
    for resource in user_access.resources:
        if resource.provider not in provider_resources:
            provider_resources[resource.provider] = []
        provider_resources[resource.provider].append(resource)
    
    # Create provider nodes and connections
    for provider, resources in provider_resources.items():
        provider_node_id = f"provider-{provider}"
        provider_node = GraphNode(
            id=provider_node_id,
            label=provider.upper(),
            type="provider",
            provider=provider,
            color=provider_colors.get(provider, "#6C757D")
        )
        nodes.append(provider_node)
        
        # Edge from user to provider
        provider_edge = GraphEdge(
            id=f"edge-user-{provider}",
            source=user_node.id,
            target=provider_node_id,
            label="has access"
        )
        edges.append(provider_edge)
        
        # Group resources by service within each provider
        service_resources = {}
        for resource in resources:
            if resource.service not in service_resources:
                service_resources[resource.service] = []
            service_resources[resource.service].append(resource)
        
        # Create service nodes
        for service, service_resources_list in service_resources.items():
            service_node_id = f"service-{provider}-{service.replace(' ', '-').lower()}"
            service_node = GraphNode(
                id=service_node_id,
                label=service,
                type="service",
                provider=provider,
                color=provider_colors.get(provider, "#6C757D")
            )
            nodes.append(service_node)
            
            # Edge from provider to service
            service_edge = GraphEdge(
                id=f"edge-{provider}-{service}",
                source=provider_node_id,
                target=service_node_id,
                label="provides"
            )
            edges.append(service_edge)
            
            # Create resource/access nodes
            for resource in service_resources_list:
                resource_node_id = f"resource-{resource.id}"
                resource_label = f"{resource.resource_name}\n({resource.access_type})"
                
                resource_node = GraphNode(
                    id=resource_node_id,
                    label=resource_label,
                    type="resource",
                    provider=provider,
                    access_type=resource.access_type,
                    color=access_colors.get(resource.access_type, "#6C757D")
                )
                nodes.append(resource_node)
                
                # Edge from service to resource
                resource_edge = GraphEdge(
                    id=f"edge-{service}-{resource.id}",
                    source=service_node_id,
                    target=resource_node_id,
                    label=resource.access_type
                )
                edges.append(resource_edge)
    
    return GraphData(nodes=nodes, edges=edges)

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Cloud Access Visualization API", "version": "1.0.0"}

@api_router.get("/search/{user_email}", response_model=SearchResponse)
async def search_user_access(user_email: str):
    """Search for user access across all cloud providers"""
    try:
        # Find user in database
        user_doc = await db.user_access.find_one({"user_email": user_email})
        
        if not user_doc:
            # Return empty graph if user not found
            return SearchResponse(
                user=None,
                graph_data=GraphData(nodes=[], edges=[])
            )
        
        user_access = UserAccess(**user_doc)
        graph_data = generate_graph_data(user_access)
        
        return SearchResponse(
            user=user_access,
            graph_data=graph_data
        )
    
    except Exception as e:
        logging.error(f"Error searching for user {user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching user access: {str(e)}")

@api_router.get("/users", response_model=List[UserAccess])
async def get_all_users():
    """Get all users in the system"""
    try:
        users = await db.user_access.find().to_list(1000)
        return [UserAccess(**user) for user in users]
    except Exception as e:
        logging.error(f"Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving users")

@api_router.get("/users/{user_email}/resources", response_model=List[CloudResource])
async def get_user_resources(user_email: str):
    """Get all resources for a specific user"""
    try:
        user_doc = await db.user_access.find_one({"user_email": user_email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_access = UserAccess(**user_doc)
        return user_access.resources
    except Exception as e:
        logging.error(f"Error getting resources for user {user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving user resources")

@api_router.get("/providers", response_model=Dict[str, Any])
async def get_provider_statistics():
    """Get statistics about all cloud providers"""
    try:
        users = await db.user_access.find().to_list(1000)
        stats = {
            "total_users": len(users),
            "providers": {
                "aws": {"users": 0, "resources": 0},
                "gcp": {"users": 0, "resources": 0},
                "azure": {"users": 0, "resources": 0},
                "okta": {"users": 0, "resources": 0}
            }
        }
        
        for user_doc in users:
            user_access = UserAccess(**user_doc)
            user_providers = set()
            
            for resource in user_access.resources:
                provider = resource.provider
                if provider not in user_providers:
                    stats["providers"][provider]["users"] += 1
                    user_providers.add(provider)
                stats["providers"][provider]["resources"] += 1
        
        return stats
    except Exception as e:
        logging.error(f"Error getting provider statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving statistics")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    await init_sample_data()
    logging.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()