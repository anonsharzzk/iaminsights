from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Query, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import io
import csv
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional
import pandas as pd
import uuid
import jwt
import bcrypt
from jose import JWTError

# Import enhanced models inline

# Authentication Models
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    hashed_password: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None  # Admin who created the user

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

class CloudProvider(str, Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    OKTA = "okta"

# Provider Sample Data Models
class ProviderSample(BaseModel):
    provider: CloudProvider
    sample_format: Dict[str, Any]
    description: str
    required_fields: List[str]

class AccessType(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"
    USER = "user"
    EXECUTE = "execute"
    DELETE = "delete"
    LIST = "list"
    CREATE = "create"
    UPDATE = "update"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Enhanced Cloud Resource Model
class CloudResource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: CloudProvider
    service: str  # S3, IAM, Compute Engine, etc.
    resource_type: str  # bucket, instance, database, application
    resource_name: str
    resource_arn: Optional[str] = None  # For AWS resources
    access_type: AccessType
    permission_details: Optional[Dict[str, Any]] = None  # Store raw permission data
    description: Optional[str] = None
    region: Optional[str] = None
    account_id: Optional[str] = None
    
    # Risk and analysis fields
    risk_level: RiskLevel = RiskLevel.LOW
    is_privileged: bool = False
    last_used: Optional[datetime] = None
    mfa_required: bool = True
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Enhanced User Access Model
class UserAccess(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str
    user_name: str
    user_id: Optional[str] = None  # External user ID
    
    # User attributes
    department: Optional[str] = None
    job_title: Optional[str] = None
    manager: Optional[str] = None
    is_service_account: bool = False
    
    # Access data
    resources: List[CloudResource]
    groups: List[str] = []  # Group memberships
    roles: List[str] = []   # Role assignments
    
    # Risk analysis
    overall_risk_score: float = 0.0
    privilege_escalation_paths: List[Dict[str, Any]] = []
    unused_privileges: List[str] = []
    cross_provider_admin: bool = False
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    data_source: str = "manual"  # manual, aws, gcp, azure, okta, json_import

# Search Models
class SearchFilter(BaseModel):
    provider: Optional[str] = None
    access_type: Optional[str] = None
    risk_level: Optional[str] = None
    resource_type: Optional[str] = None
    service: Optional[str] = None
    department: Optional[str] = None

class ResourceSearchResult(BaseModel):
    resource: CloudResource
    users_with_access: List[str]
    total_users: int
    risk_summary: Dict[str, int]

# Analytics Models
class PrivilegeEscalationPath(BaseModel):
    user_email: str
    start_privilege: str
    end_privilege: str
    path_steps: List[Dict[str, str]]
    risk_score: float

class AccessAnalytics(BaseModel):
    total_users: int
    total_resources: int
    risk_distribution: Dict[str, int]
    top_privileged_users: List[Dict[str, Any]]
    unused_privileges_count: int
    cross_provider_admins: int
    privilege_escalation_risks: List[PrivilegeEscalationPath]
    provider_stats: Dict[str, Dict[str, int]]

# Graph Visualization Models
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production-urgently-this-is-not-secure')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
security = HTTPBearer()

# Password hashing utilities
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user_doc = await db.users.find_one({"email": token_data.email})
    if user_doc is None:
        raise credentials_exception
    
    user = User(**user_doc)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user

async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """Ensure current user is an admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Create the main app without a prefix
app = FastAPI(title="Cloud Access Visualization API", version="3.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")



# Provider sample data
PROVIDER_SAMPLES = {
    "aws": {
        "provider": "aws",
        "description": "AWS IAM access data format with services like S3, EC2, IAM, RDS, Lambda",
        "required_fields": ["provider", "service", "resource_type", "resource_name", "access_type"],
        "sample_format": {
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
                            "resource_arn": "arn:aws:s3:::production-data-bucket",
                            "access_type": "read",
                            "region": "us-east-1",
                            "account_id": "123456789012",
                            "risk_level": "medium",
                            "is_privileged": False,
                            "mfa_required": True,
                            "description": "Read access to production data"
                        }
                    ]
                }
            ]
        }
    },
    "gcp": {
        "provider": "gcp",
        "description": "Google Cloud Platform IAM access data with services like Compute Engine, Cloud Storage, BigQuery",
        "required_fields": ["provider", "service", "resource_type", "resource_name", "access_type"],
        "sample_format": {
            "metadata": {
                "import_date": "2024-12-19T10:30:00Z",
                "source": "gcp_iam_audit",
                "description": "GCP IAM access audit data"
            },
            "users": [
                {
                    "user_email": "user@company.com",
                    "user_name": "Jane Smith",
                    "department": "Data Analytics",
                    "job_title": "Data Engineer",
                    "resources": [
                        {
                            "provider": "gcp",
                            "service": "Compute Engine",
                            "resource_type": "instance",
                            "resource_name": "analytics-vm-001",
                            "access_type": "write",
                            "region": "us-central1",
                            "account_id": "company-analytics-proj",
                            "risk_level": "medium",
                            "is_privileged": False,
                            "mfa_required": True,
                            "description": "Manage analytics compute instances"
                        }
                    ]
                }
            ]
        }
    },
    "azure": {
        "provider": "azure",
        "description": "Microsoft Azure access data with services like Storage, Virtual Machines, Key Vault",
        "required_fields": ["provider", "service", "resource_type", "resource_name", "access_type"],
        "sample_format": {
            "metadata": {
                "import_date": "2024-12-19T10:30:00Z",
                "source": "azure_rbac_audit",
                "description": "Azure RBAC access audit data"
            },
            "users": [
                {
                    "user_email": "user@company.com",
                    "user_name": "Mike Johnson",
                    "department": "Infrastructure",
                    "job_title": "Cloud Architect",
                    "resources": [
                        {
                            "provider": "azure",
                            "service": "Storage",
                            "resource_type": "storage",
                            "resource_name": "companydata001",
                            "access_type": "admin",
                            "region": "East US",
                            "account_id": "subscription-12345678",
                            "risk_level": "high",
                            "is_privileged": True,
                            "mfa_required": True,
                            "description": "Full access to company storage account"
                        }
                    ]
                }
            ]
        }
    },
    "okta": {
        "provider": "okta",
        "description": "Okta application access data with SSO applications and user permissions",
        "required_fields": ["provider", "service", "resource_type", "resource_name", "access_type"],
        "sample_format": {
            "metadata": {
                "import_date": "2024-12-19T10:30:00Z",
                "source": "okta_audit",
                "description": "Okta application access audit data"
            },
            "users": [
                {
                    "user_email": "user@company.com",
                    "user_name": "Sarah Wilson",
                    "department": "Sales",
                    "job_title": "Sales Manager",
                    "resources": [
                        {
                            "provider": "okta",
                            "service": "Salesforce",
                            "resource_type": "application",
                            "resource_name": "Sales CRM",
                            "access_type": "admin",
                            "risk_level": "medium",
                            "is_privileged": True,
                            "mfa_required": True,
                            "description": "Admin access to Salesforce CRM"
                        }
                    ]
                }
            ]
        }
    }
}

# Initialize default admin user
async def init_default_admin():
    """Initialize default admin user if no users exist"""
    user_count = await db.users.count_documents({})
    if user_count == 0:
        # Create primary admin user
        primary_admin = User(
            email="self@iamsharn.com",
            hashed_password=hash_password("Testing@123"),
            role=UserRole.ADMIN,
            created_at=datetime.utcnow()
        )
        await db.users.insert_one(primary_admin.dict())
        logging.info("Primary admin user created: self@iamsharn.com")
        
        # Create secondary admin user for backward compatibility
        secondary_admin = User(
            email="adminn@iamsharan.com",
            hashed_password=hash_password("Testing@123"),
            role=UserRole.ADMIN,
            created_at=datetime.utcnow()
        )
        await db.users.insert_one(secondary_admin.dict())
        logging.info("Secondary admin user created: adminn@iamsharan.com")

# Risk Analysis Functions
def calculate_risk_score(user_access: UserAccess) -> float:
    """Calculate overall risk score for a user based on their access patterns"""
    risk_score = 0.0
    
    # Base risk factors
    admin_count = sum(1 for resource in user_access.resources if resource.access_type == AccessType.ADMIN)
    privileged_count = sum(1 for resource in user_access.resources if resource.is_privileged)
    providers = set(resource.provider for resource in user_access.resources)
    
    # Risk scoring logic
    risk_score += admin_count * 10  # Admin access adds significant risk
    risk_score += privileged_count * 5  # Privileged access adds moderate risk
    risk_score += len(providers) * 3  # Cross-provider access adds risk
    
    # Service account risk adjustment
    if user_access.is_service_account:
        risk_score *= 1.5  # Service accounts are higher risk
    
    # Cross-provider admin bonus risk
    if admin_count > 0 and len(providers) > 2:
        risk_score += 20
        user_access.cross_provider_admin = True
    
    return min(risk_score, 100.0)  # Cap at 100

def detect_privilege_escalation_paths(user_access: UserAccess) -> List[PrivilegeEscalationPath]:
    """Detect potential privilege escalation paths for a user"""
    paths = []
    
    # Simple escalation detection: read -> write -> admin within same service
    services_access = {}
    for resource in user_access.resources:
        key = f"{resource.provider}-{resource.service}"
        if key not in services_access:
            services_access[key] = []
        services_access[key].append(resource.access_type)
    
    for service, access_types in services_access.items():
        access_set = set(access_types)
        if AccessType.READ in access_set and AccessType.ADMIN in access_set:
            paths.append(PrivilegeEscalationPath(
                user_email=user_access.user_email,
                start_privilege="read",
                end_privilege="admin",
                path_steps=[
                    {"step": 1, "action": "exploit_read_access", "service": service},
                    {"step": 2, "action": "escalate_to_admin", "service": service}
                ],
                risk_score=calculate_escalation_risk(access_set)
            ))
    
    return paths

def calculate_escalation_risk(access_types: set) -> float:
    """Calculate risk score for privilege escalation"""
    base_risk = 30.0
    if AccessType.WRITE in access_types:
        base_risk += 20.0
    if AccessType.ADMIN in access_types:
        base_risk += 30.0
    return min(base_risk, 100.0)

def analyze_user_access(user_access: UserAccess) -> UserAccess:
    """Perform comprehensive risk analysis on user access"""
    user_access.overall_risk_score = calculate_risk_score(user_access)
    user_access.privilege_escalation_paths = detect_privilege_escalation_paths(user_access)
    
    # Detect unused privileges (simulate - in real implementation, this would use last_used data)
    user_access.unused_privileges = [
        f"{resource.provider}-{resource.service}"
        for resource in user_access.resources
        if resource.last_used and (datetime.utcnow() - resource.last_used).days > 90
    ]
    
    return user_access

# JSON Import Functions
async def process_json_import(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process imported JSON data and save to database"""
    try:
        # Validate JSON structure
        users_data = json_data.get("users", [])
        metadata = json_data.get("metadata", {})
        
        processed_users = []
        for user_data in users_data:
            # Convert resources to CloudResource objects
            resources = []
            for resource_data in user_data.get("resources", []):
                # Handle datetime parsing for last_used field
                if "last_used" in resource_data and resource_data["last_used"]:
                    try:
                        # Parse ISO datetime string and convert to naive datetime
                        from dateutil import parser
                        dt = parser.parse(resource_data["last_used"])
                        # Convert to naive datetime (remove timezone info)
                        resource_data["last_used"] = dt.replace(tzinfo=None)
                    except Exception as e:
                        logging.warning(f"Could not parse last_used datetime: {e}")
                        resource_data["last_used"] = None
                
                resource = CloudResource(**resource_data)
                resources.append(resource)
            
            # Create UserAccess object
            user_access = UserAccess(
                user_email=user_data["user_email"],
                user_name=user_data["user_name"],
                user_id=user_data.get("user_id"),
                department=user_data.get("department"),
                job_title=user_data.get("job_title"),
                manager=user_data.get("manager"),
                is_service_account=user_data.get("is_service_account", False),
                resources=resources,
                groups=user_data.get("groups", []),
                roles=user_data.get("roles", []),
                data_source="json_import"
            )
            
            # Perform risk analysis
            user_access = analyze_user_access(user_access)
            processed_users.append(user_access)
        
        # Save to database
        for user_access in processed_users:
            # Check if user already exists
            existing_user = await db.user_access.find_one({"user_email": user_access.user_email})
            if existing_user:
                # Update existing user
                await db.user_access.replace_one(
                    {"user_email": user_access.user_email},
                    user_access.dict()
                )
            else:
                # Insert new user
                await db.user_access.insert_one(user_access.dict())
        
        return {
            "status": "success",
            "imported_users": len(processed_users),
            "metadata": metadata
        }
    
    except Exception as e:
        logging.error(f"Error processing JSON import: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing JSON: {str(e)}")

# Enhanced sample data initialization
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
                {"provider": "aws", "service": "S3", "resource_type": "bucket", "resource_name": "production-data-bucket", "access_type": "read", "description": "Read access to production data"},
                {"provider": "aws", "service": "S3", "resource_type": "bucket", "resource_name": "backup-bucket", "access_type": "write", "description": "Write access for backups"},
                {"provider": "aws", "service": "EC2", "resource_type": "instance", "resource_name": "web-server-01", "access_type": "admin", "description": "Full admin access to web servers"},
                {"provider": "aws", "service": "IAM", "resource_type": "role", "resource_name": "developer-role", "access_type": "read", "description": "Read IAM policies"},
                {"provider": "aws", "service": "RDS", "resource_type": "database", "resource_name": "prod-database", "access_type": "read", "description": "Read access to production database"},
                
                # GCP Resources
                {"provider": "gcp", "service": "Compute Engine", "resource_type": "instance", "resource_name": "analytics-vm", "access_type": "admin", "description": "Admin access to analytics VM"},
                {"provider": "gcp", "service": "Cloud Storage", "resource_type": "bucket", "resource_name": "ml-models-bucket", "access_type": "write", "description": "Upload ML models"},
                {"provider": "gcp", "service": "BigQuery", "resource_type": "dataset", "resource_name": "analytics-dataset", "access_type": "read", "description": "Query analytics data"},
                
                # Azure Resources
                {"provider": "azure", "service": "Storage", "resource_type": "storage", "resource_name": "logs-storage", "access_type": "read", "description": "Read application logs"},
                {"provider": "azure", "service": "Virtual Machines", "resource_type": "instance", "resource_name": "test-vm", "access_type": "write", "description": "Manage test environments"},
                
                # Okta Applications
                {"provider": "okta", "service": "Salesforce", "resource_type": "application", "resource_name": "CRM System", "access_type": "user", "description": "Standard user access"},
                {"provider": "okta", "service": "Slack", "resource_type": "application", "resource_name": "Team Communication", "access_type": "admin", "description": "Slack workspace admin"},
                {"provider": "okta", "service": "GitHub", "resource_type": "application", "resource_name": "Code Repository", "access_type": "admin", "description": "Repository admin access"},
            ]
        },
        {
            "user_email": "bob@company.com",
            "user_name": "Bob Smith",
            "resources": [
                # AWS Resources
                {"provider": "aws", "service": "S3", "resource_type": "bucket", "resource_name": "development-bucket", "access_type": "admin", "description": "Full access to dev environment"},
                {"provider": "aws", "service": "Lambda", "resource_type": "function", "resource_name": "api-functions", "access_type": "write", "description": "Deploy serverless functions"},
                {"provider": "aws", "service": "CloudWatch", "resource_type": "logs", "resource_name": "monitoring", "access_type": "read", "description": "Monitor application metrics"},
                
                # GCP Resources
                {"provider": "gcp", "service": "Cloud Functions", "resource_type": "function", "resource_name": "data-processing", "access_type": "admin", "description": "Manage data processing functions"},
                {"provider": "gcp", "service": "Pub/Sub", "resource_type": "topic", "resource_name": "event-streaming", "access_type": "write", "description": "Publish events"},
                
                # Azure Resources
                {"provider": "azure", "service": "App Service", "resource_type": "webapp", "resource_name": "web-application", "access_type": "admin", "description": "Deploy web applications"},
                {"provider": "azure", "service": "Key Vault", "resource_type": "vault", "resource_name": "secrets-vault", "access_type": "read", "description": "Access application secrets"},
                
                # Okta Applications
                {"provider": "okta", "service": "JIRA", "resource_type": "application", "resource_name": "Project Management", "access_type": "user", "description": "Track project issues"},
                {"provider": "okta", "service": "Confluence", "resource_type": "application", "resource_name": "Documentation", "access_type": "admin", "description": "Manage team documentation"},
            ]
        },
        {
            "user_email": "carol@company.com",
            "user_name": "Carol Davis",
            "resources": [
                # AWS Resources (Security focused)
                {"provider": "aws", "service": "IAM", "resource_type": "policy", "resource_name": "security-policies", "access_type": "admin", "description": "Manage security policies"},
                {"provider": "aws", "service": "CloudTrail", "resource_type": "logs", "resource_name": "audit-logs", "access_type": "read", "description": "Review audit trails"},
                {"provider": "aws", "service": "GuardDuty", "resource_type": "detector", "resource_name": "threat-detection", "access_type": "admin", "description": "Manage threat detection"},
                
                # GCP Resources
                {"provider": "gcp", "service": "Security Center", "resource_type": "scanner", "resource_name": "vulnerability-scan", "access_type": "admin", "description": "Security monitoring"},
                {"provider": "gcp", "service": "Cloud IAM", "resource_type": "policy", "resource_name": "access-control", "access_type": "admin", "description": "Manage access policies"},
                
                # Azure Resources
                {"provider": "azure", "service": "Security Center", "resource_type": "compliance", "resource_name": "compliance-monitoring", "access_type": "admin", "description": "Monitor compliance"},
                {"provider": "azure", "service": "Active Directory", "resource_type": "directory", "resource_name": "user-management", "access_type": "admin", "description": "Manage user accounts"},
                
                # Okta Applications
                {"provider": "okta", "service": "Okta Admin", "resource_type": "application", "resource_name": "Identity Management", "access_type": "admin", "description": "Manage identity and access"},
                {"provider": "okta", "service": "OneLogin", "resource_type": "application", "resource_name": "SSO Portal", "access_type": "admin", "description": "Single sign-on management"},
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

# Authentication Endpoints
@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Authenticate user and return JWT token"""
    try:
        user_doc = await db.users.find_one({"email": user_credentials.email})
        if not user_doc or not verify_password(user_credentials.password, user_doc["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = User(**user_doc)
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

# User Management Endpoints (Admin only)
@api_router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_admin: User = Depends(get_current_admin_user)
):
    """Create a new user (Admin only)"""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        new_user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
            created_by=current_admin.email
        )
        
        await db.users.insert_one(new_user.dict())
        
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating user")

@api_router.get("/users/all", response_model=List[UserResponse])
async def get_all_system_users(current_admin: User = Depends(get_current_admin_user)):
    """Get all system users (Admin only)"""
    try:
        users = await db.users.find().to_list(1000)
        return [
            UserResponse(
                id=user["id"],
                email=user["email"],
                role=user["role"],
                is_active=user["is_active"],
                created_at=user["created_at"]
            )
            for user in users
        ]
    except Exception as e:
        logging.error(f"Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving users")

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_admin: User = Depends(get_current_admin_user)
):
    """Update a user (Admin only)"""
    try:
        user_doc = await db.users.find_one({"id": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        update_data = {}
        if user_data.email:
            # Check if new email is already taken
            existing_user = await db.users.find_one({"email": user_data.email, "id": {"$ne": user_id}})
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")
            update_data["email"] = user_data.email
        
        if user_data.password:
            update_data["hashed_password"] = hash_password(user_data.password)
        
        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active
        
        update_data["updated_at"] = datetime.utcnow()
        
        await db.users.update_one({"id": user_id}, {"$set": update_data})
        
        # Get updated user
        updated_user_doc = await db.users.find_one({"id": user_id})
        updated_user = User(**updated_user_doc)
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            role=updated_user.role,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating user")

@api_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin_user)
):
    """Delete a user (Admin only)"""
    try:
        # Prevent admin from deleting themselves
        if current_admin.id == user_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        result = await db.users.delete_one({"id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting user")

@api_router.put("/auth/update-profile", response_model=UserResponse)
async def update_own_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user's own profile"""
    try:
        update_data = {}
        
        if user_data.email:
            # Check if new email is already taken
            existing_user = await db.users.find_one({"email": user_data.email, "id": {"$ne": current_user.id}})
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")
            update_data["email"] = user_data.email
        
        if user_data.password:
            update_data["hashed_password"] = hash_password(user_data.password)
        
        update_data["updated_at"] = datetime.utcnow()
        
        await db.users.update_one({"id": current_user.id}, {"$set": update_data})
        
        # Get updated user
        updated_user_doc = await db.users.find_one({"id": current_user.id})
        updated_user = User(**updated_user_doc)
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            role=updated_user.role,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating profile")

# Provider Sample Data Endpoints
@api_router.get("/providers/samples", response_model=Dict[str, Any])
async def get_provider_samples(current_user: User = Depends(get_current_user)):
    """Get sample data formats for all providers"""
    return PROVIDER_SAMPLES

@api_router.get("/providers/samples/{provider}", response_model=Dict[str, Any])
async def get_provider_sample(
    provider: CloudProvider,
    current_user: User = Depends(get_current_user)
):
    """Get sample data format for a specific provider"""
    if provider not in PROVIDER_SAMPLES:
        raise HTTPException(status_code=404, detail="Provider sample not found")
    return PROVIDER_SAMPLES[provider]

# Protected Cloud Access Data Endpoints (All require authentication)
@api_router.get("/")
async def root():
    return {"message": "Cloud Access Visualization API", "version": "3.0.0"}

@api_router.get("/search/{user_email}", response_model=SearchResponse)
async def search_user_access(
    user_email: str,
    current_user: User = Depends(get_current_user)
):
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
async def get_all_users(current_user: User = Depends(get_current_user)):
    """Get all users in the system"""
    try:
        users = await db.user_access.find().to_list(1000)
        return [UserAccess(**user) for user in users]
    except Exception as e:
        logging.error(f"Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving users")

@api_router.get("/users/{user_email}/resources", response_model=List[CloudResource])
async def get_user_resources(
    user_email: str,
    current_user: User = Depends(get_current_user)
):
    """Get all resources for a specific user"""
    try:
        user_doc = await db.user_access.find_one({"user_email": user_email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_access = UserAccess(**user_doc)
        return user_access.resources
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) without modification
        raise
    except Exception as e:
        logging.error(f"Error getting resources for user {user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving user resources")

@api_router.get("/providers", response_model=Dict[str, Any])
async def get_provider_statistics(current_user: User = Depends(get_current_user)):
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

# Enhanced API Endpoints

@api_router.post("/import/json")
async def import_json_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Import user access data from JSON file"""
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="File must be a JSON file")
        
        content = await file.read()
        json_data = json.loads(content.decode('utf-8'))
        
        result = await process_json_import(json_data)
        return result
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logging.error(f"Error importing JSON data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error importing data: {str(e)}")

@api_router.get("/search/resource/{resource_name}", response_model=List[ResourceSearchResult])
async def search_by_resource(
    resource_name: str,
    current_user: User = Depends(get_current_user)
):
    """Search for users who have access to a specific resource"""
    try:
        users = await db.user_access.find().to_list(1000)
        results = []
        
        for user_doc in users:
            user_access = UserAccess(**user_doc)
            matching_resources = [
                resource for resource in user_access.resources
                if resource_name.lower() in resource.resource_name.lower()
            ]
            
            if matching_resources:
                for resource in matching_resources:
                    # Count total users with access to this resource
                    total_users = 0
                    risk_summary = {"low": 0, "medium": 0, "high": 0, "critical": 0}
                    
                    for other_user_doc in users:
                        other_user = UserAccess(**other_user_doc)
                        if any(r.resource_name == resource.resource_name for r in other_user.resources):
                            total_users += 1
                            risk_level = resource.risk_level or "low"
                            risk_summary[risk_level] += 1
                    
                    results.append(ResourceSearchResult(
                        resource=resource,
                        users_with_access=[user_access.user_email],
                        total_users=total_users,
                        risk_summary=risk_summary
                    ))
        
        return results
    
    except Exception as e:
        logging.error(f"Error searching by resource {resource_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching by resource")

@api_router.get("/analytics", response_model=AccessAnalytics)
async def get_access_analytics(current_user: User = Depends(get_current_user)):
    """Get comprehensive access analytics and insights"""
    try:
        users = await db.user_access.find().to_list(1000)
        user_objects = [UserAccess(**user) for user in users]
        
        # Calculate analytics
        total_users = len(user_objects)
        total_resources = sum(len(user.resources) for user in user_objects)
        
        # Risk distribution
        risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        cross_provider_admins = 0
        unused_privileges_count = 0
        privilege_escalation_risks = []
        
        # Top privileged users
        top_privileged_users = []
        
        for user in user_objects:
            # Analyze user and calculate risk
            analyzed_user = analyze_user_access(user)
            
            # Update risk distribution
            if analyzed_user.overall_risk_score < 25:
                risk_distribution["low"] += 1
            elif analyzed_user.overall_risk_score < 50:
                risk_distribution["medium"] += 1
            elif analyzed_user.overall_risk_score < 75:
                risk_distribution["high"] += 1
            else:
                risk_distribution["critical"] += 1
            
            # Count cross-provider admins
            if analyzed_user.cross_provider_admin:
                cross_provider_admins += 1
            
            # Count unused privileges
            unused_privileges_count += len(analyzed_user.unused_privileges)
            
            # Collect privilege escalation risks
            privilege_escalation_risks.extend(analyzed_user.privilege_escalation_paths)
            
            # Add to top privileged users
            admin_count = sum(1 for r in user.resources if r.access_type == AccessType.ADMIN)
            if admin_count > 0:
                top_privileged_users.append({
                    "user_email": user.user_email,
                    "user_name": user.user_name,
                    "admin_access_count": admin_count,
                    "total_resources": len(user.resources),
                    "risk_score": analyzed_user.overall_risk_score,
                    "is_service_account": user.is_service_account
                })
        
        # Sort top privileged users by risk score
        top_privileged_users.sort(key=lambda x: x["risk_score"], reverse=True)
        top_privileged_users = top_privileged_users[:10]  # Top 10
        
        # Provider statistics
        provider_stats = {}
        for provider in ["aws", "gcp", "azure", "okta"]:
            users_with_provider = sum(
                1 for user in user_objects
                if any(r.provider == provider for r in user.resources)
            )
            resources_in_provider = sum(
                len([r for r in user.resources if r.provider == provider])
                for user in user_objects
            )
            provider_stats[provider] = {
                "users": users_with_provider,
                "resources": resources_in_provider
            }
        
        return AccessAnalytics(
            total_users=total_users,
            total_resources=total_resources,
            risk_distribution=risk_distribution,
            top_privileged_users=top_privileged_users,
            unused_privileges_count=unused_privileges_count,
            cross_provider_admins=cross_provider_admins,
            privilege_escalation_risks=privilege_escalation_risks,
            provider_stats=provider_stats
        )
    
    except Exception as e:
        logging.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving analytics")

@api_router.get("/export/{format}")
async def export_data(
    format: str,
    provider: Optional[str] = Query(None),
    access_type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None)
):
    """Export access data in various formats (CSV, XLSX, JSON)"""
    try:
        if format not in ["csv", "xlsx", "json"]:
            raise HTTPException(status_code=400, detail="Format must be csv, xlsx, or json")
        
        # Get all users
        users = await db.user_access.find().to_list(1000)
        user_objects = [UserAccess(**user) for user in users]
        
        # Apply filters
        filtered_data = []
        for user in user_objects:
            analyzed_user = analyze_user_access(user)
            for resource in user.resources:
                if provider and resource.provider != provider:
                    continue
                if access_type and resource.access_type != access_type:
                    continue
                if risk_level and resource.risk_level != risk_level:
                    continue
                
                filtered_data.append({
                    "user_email": user.user_email,
                    "user_name": user.user_name,
                    "department": user.department,
                    "job_title": user.job_title,
                    "is_service_account": user.is_service_account,
                    "provider": resource.provider,
                    "service": resource.service,
                    "resource_type": resource.resource_type,
                    "resource_name": resource.resource_name,
                    "access_type": resource.access_type,
                    "risk_level": resource.risk_level,
                    "is_privileged": resource.is_privileged,
                    "last_used": resource.last_used,
                    "mfa_required": resource.mfa_required,
                    "user_risk_score": analyzed_user.overall_risk_score,
                    "cross_provider_admin": analyzed_user.cross_provider_admin
                })
        
        if format == "json":
            output = json.dumps(filtered_data, default=str, indent=2)
            media_type = "application/json"
            filename = f"cloud_access_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        elif format == "csv":
            output = io.StringIO()
            if filtered_data:
                writer = csv.DictWriter(output, fieldnames=filtered_data[0].keys())
                writer.writeheader()
                writer.writerows(filtered_data)
            output = output.getvalue()
            media_type = "text/csv"
            filename = f"cloud_access_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        elif format == "xlsx":
            df = pd.DataFrame(filtered_data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Cloud Access Report')
            output = output.getvalue()
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"cloud_access_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output) if format == "xlsx" else io.StringIO(output),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        logging.error(f"Error exporting data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error exporting data")

@api_router.get("/risk-analysis/{user_email}")
async def get_user_risk_analysis(user_email: str):
    """Get detailed risk analysis for a specific user"""
    try:
        user_doc = await db.user_access.find_one({"user_email": user_email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_access = UserAccess(**user_doc)
        analyzed_user = analyze_user_access(user_access)
        
        return {
            "user_email": user_email,
            "overall_risk_score": analyzed_user.overall_risk_score,
            "risk_level": (
                "critical" if analyzed_user.overall_risk_score >= 75 else
                "high" if analyzed_user.overall_risk_score >= 50 else
                "medium" if analyzed_user.overall_risk_score >= 25 else
                "low"
            ),
            "cross_provider_admin": analyzed_user.cross_provider_admin,
            "privilege_escalation_paths": analyzed_user.privilege_escalation_paths,
            "unused_privileges": analyzed_user.unused_privileges,
            "admin_access_count": sum(1 for r in user_access.resources if r.access_type == AccessType.ADMIN),
            "privileged_access_count": sum(1 for r in user_access.resources if r.is_privileged),
            "providers_with_access": list(set(r.provider for r in user_access.resources)),
            "recommendations": [
                "Enable MFA on all privileged accounts" if any(not r.mfa_required and r.is_privileged for r in user_access.resources) else None,
                "Review unused privileges" if analyzed_user.unused_privileges else None,
                "Audit cross-provider admin access" if analyzed_user.cross_provider_admin else None,
                "Implement privilege escalation monitoring" if analyzed_user.privilege_escalation_paths else None
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting risk analysis for user {user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving risk analysis")

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
    await init_default_admin()
    await init_sample_data()
    logging.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()