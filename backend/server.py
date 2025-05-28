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
    full_name: str
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
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours = 1440 minutes

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

# Enhanced Risk Analysis Models
class RiskFactor(BaseModel):
    factor_type: str
    description: str
    weight: float
    severity: str  # low, medium, high, critical
    justification: str

class RiskAnalysisResult(BaseModel):
    overall_score: float
    risk_level: str
    risk_factors: List[RiskFactor]
    recommendations: List[str]
    confidence_score: float

class SensitiveResource(BaseModel):
    provider: str
    service: str
    resource_patterns: List[str]
    sensitivity_level: str  # low, medium, high, critical
    description: str

# Audit Logging Models
class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    user_email: str
    target_user: Optional[str] = None
    action: str
    details: Dict[str, Any]
    risk_score_before: Optional[float] = None
    risk_score_after: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

# Enhanced Risk Analysis Functions

# Define sensitive resources patterns
SENSITIVE_RESOURCES = {
    "aws": [
        SensitiveResource(
            provider="aws",
            service="S3",
            resource_patterns=["prod", "production", "backup", "finance", "hr", "security", "admin"],
            sensitivity_level="high",
            description="Production and sensitive data buckets"
        ),
        SensitiveResource(
            provider="aws",
            service="IAM",
            resource_patterns=["admin", "root", "master", "security"],
            sensitivity_level="critical",
            description="Administrative IAM resources"
        ),
        SensitiveResource(
            provider="aws",
            service="RDS",
            resource_patterns=["prod", "production", "master", "primary"],
            sensitivity_level="high",
            description="Production databases"
        ),
        SensitiveResource(
            provider="aws",
            service="Lambda",
            resource_patterns=["admin", "security", "payment", "finance"],
            sensitivity_level="medium",
            description="Critical business functions"
        )
    ],
    "gcp": [
        SensitiveResource(
            provider="gcp",
            service="Cloud Storage",
            resource_patterns=["prod", "production", "backup", "finance", "hr"],
            sensitivity_level="high",
            description="Production storage buckets"
        ),
        SensitiveResource(
            provider="gcp",
            service="Cloud IAM",
            resource_patterns=["admin", "owner", "editor"],
            sensitivity_level="critical",
            description="High-privilege IAM roles"
        ),
        SensitiveResource(
            provider="gcp",
            service="BigQuery",
            resource_patterns=["prod", "production", "analytics", "customer"],
            sensitivity_level="high",
            description="Production data warehouses"
        )
    ],
    "azure": [
        SensitiveResource(
            provider="azure",
            service="Storage",
            resource_patterns=["prod", "production", "backup", "finance"],
            sensitivity_level="high",
            description="Production storage accounts"
        ),
        SensitiveResource(
            provider="azure",
            service="Active Directory",
            resource_patterns=["admin", "global", "security"],
            sensitivity_level="critical",
            description="Directory administration"
        ),
        SensitiveResource(
            provider="azure",
            service="Key Vault",
            resource_patterns=["prod", "production", "master"],
            sensitivity_level="critical",
            description="Production secrets and keys"
        )
    ],
    "okta": [
        SensitiveResource(
            provider="okta",
            service="Admin",
            resource_patterns=["admin", "super", "security"],
            sensitivity_level="critical",
            description="Administrative access to identity management"
        ),
        SensitiveResource(
            provider="okta",
            service="Salesforce",
            resource_patterns=["admin", "system"],
            sensitivity_level="high",
            description="CRM administrative access"
        ),
        SensitiveResource(
            provider="okta",
            service="AWS SSO",
            resource_patterns=["admin", "power", "dev"],
            sensitivity_level="high",
            description="Cloud platform access"
        )
    ]
}

def is_sensitive_resource(resource: CloudResource) -> tuple[bool, str, str]:
    """Check if a resource is considered sensitive"""
    provider_patterns = SENSITIVE_RESOURCES.get(resource.provider, [])
    
    for sensitive in provider_patterns:
        if sensitive.service.lower() == resource.service.lower():
            for pattern in sensitive.resource_patterns:
                if pattern.lower() in resource.resource_name.lower():
                    return True, sensitive.sensitivity_level, sensitive.description
    
    return False, "low", "Standard resource"

def calculate_cross_account_risk(user_access: UserAccess) -> float:
    """Calculate risk from cross-account access patterns"""
    accounts = set()
    risk_score = 0.0
    
    for resource in user_access.resources:
        if resource.account_id:
            accounts.add(resource.account_id)
    
    # Multiple accounts increase risk exponentially
    if len(accounts) > 1:
        risk_score = len(accounts) * 15.0  # 15 points per additional account
        if len(accounts) > 3:
            risk_score += 20.0  # Bonus risk for many accounts
    
    return min(risk_score, 50.0)  # Cap at 50 points

def calculate_sensitive_resource_risk(user_access: UserAccess) -> tuple[float, List[RiskFactor]]:
    """Calculate risk from access to sensitive resources"""
    risk_score = 0.0
    risk_factors = []
    
    sensitive_count = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    
    for resource in user_access.resources:
        is_sensitive, level, description = is_sensitive_resource(resource)
        if is_sensitive:
            sensitive_count[level] += 1
            
            # Score based on sensitivity and access type
            base_score = {"low": 2, "medium": 5, "high": 10, "critical": 20}[level]
            access_multiplier = {"read": 1.0, "write": 1.5, "admin": 2.5, "owner": 3.0}.get(resource.access_type, 1.0)
            
            resource_risk = base_score * access_multiplier
            risk_score += resource_risk
            
            if resource_risk > 10:  # Only add significant risks to factors
                risk_factors.append(RiskFactor(
                    factor_type="sensitive_resource_access",
                    description=f"{resource.access_type.title()} access to {resource.provider.upper()} {resource.service} ({resource.resource_name})",
                    weight=resource_risk,
                    severity=level,
                    justification=f"Access to {description} with {resource.access_type} permissions"
                ))
    
    # Add summary risk factor if multiple sensitive resources
    total_sensitive = sum(sensitive_count.values())
    if total_sensitive > 5:
        risk_factors.append(RiskFactor(
            factor_type="excessive_sensitive_access",
            description=f"Access to {total_sensitive} sensitive resources",
            weight=total_sensitive * 2.0,
            severity="high" if total_sensitive > 10 else "medium",
            justification=f"Excessive access breadth across sensitive systems"
        ))
        risk_score += total_sensitive * 2.0
    
    return min(risk_score, 60.0), risk_factors

def calculate_unused_privilege_risk(user_access: UserAccess) -> tuple[float, List[RiskFactor]]:
    """Calculate risk from unused privileges"""
    risk_score = 0.0
    risk_factors = []
    
    unused_count = 0
    unused_admin_count = 0
    
    for resource in user_access.resources:
        if resource.last_used:
            days_unused = (datetime.utcnow() - resource.last_used).days
            if days_unused > 90:  # Unused for more than 90 days
                unused_count += 1
                if resource.access_type == AccessType.ADMIN:
                    unused_admin_count += 1
                    risk_score += 8.0  # Higher risk for unused admin access
                else:
                    risk_score += 3.0
    
    if unused_count > 0:
        risk_factors.append(RiskFactor(
            factor_type="unused_privileges",
            description=f"{unused_count} unused privileges ({unused_admin_count} admin)",
            weight=risk_score,
            severity="high" if unused_admin_count > 0 else "medium",
            justification=f"Privileges not used in 90+ days indicate over-provisioning"
        ))
    
    return min(risk_score, 40.0), risk_factors

def calculate_privilege_escalation_risk(user_access: UserAccess) -> tuple[float, List[RiskFactor], List[PrivilegeEscalationPath]]:
    """Enhanced privilege escalation detection"""
    risk_score = 0.0
    risk_factors = []
    escalation_paths = []
    
    # Group resources by provider-service
    services_access = {}
    for resource in user_access.resources:
        key = f"{resource.provider}-{resource.service}"
        if key not in services_access:
            services_access[key] = []
        services_access[key].append(resource)
    
    for service_key, resources in services_access.items():
        access_types = set(r.access_type for r in resources)
        
        # Check for escalation patterns
        escalation_risk = 0.0
        
        # Pattern 1: Read + Write + Admin in same service
        if {AccessType.READ, AccessType.WRITE, AccessType.ADMIN}.issubset(access_types):
            escalation_risk += 30.0
            escalation_paths.append(PrivilegeEscalationPath(
                user_email=user_access.user_email,
                start_privilege="read",
                end_privilege="admin",
                path_steps=[
                    {"step": 1, "action": "exploit_read_access", "service": service_key},
                    {"step": 2, "action": "escalate_via_write", "service": service_key},
                    {"step": 3, "action": "achieve_admin_access", "service": service_key}
                ],
                risk_score=30.0
            ))
        
        # Pattern 2: Read + Admin (bypassing write)
        elif {AccessType.READ, AccessType.ADMIN}.issubset(access_types):
            escalation_risk += 20.0
            escalation_paths.append(PrivilegeEscalationPath(
                user_email=user_access.user_email,
                start_privilege="read",
                end_privilege="admin",
                path_steps=[
                    {"step": 1, "action": "exploit_read_access", "service": service_key},
                    {"step": 2, "action": "escalate_to_admin", "service": service_key}
                ],
                risk_score=20.0
            ))
        
        # Pattern 3: Write + Admin
        elif {AccessType.WRITE, AccessType.ADMIN}.issubset(access_types):
            escalation_risk += 15.0
            escalation_paths.append(PrivilegeEscalationPath(
                user_email=user_access.user_email,
                start_privilege="write",
                end_privilege="admin",
                path_steps=[
                    {"step": 1, "action": "exploit_write_access", "service": service_key},
                    {"step": 2, "action": "escalate_to_admin", "service": service_key}
                ],
                risk_score=15.0
            ))
        
        risk_score += escalation_risk
        
        if escalation_risk > 0:
            risk_factors.append(RiskFactor(
                factor_type="privilege_escalation",
                description=f"Potential escalation path in {service_key}",
                weight=escalation_risk,
                severity="high" if escalation_risk >= 25 else "medium",
                justification=f"Multiple access levels in same service enable privilege escalation"
            ))
    
    return min(risk_score, 50.0), risk_factors, escalation_paths

def calculate_comprehensive_risk_score(user_access: UserAccess) -> RiskAnalysisResult:
    """Calculate comprehensive risk score with detailed breakdown"""
    total_risk = 0.0
    all_risk_factors = []
    all_recommendations = []
    
    # 1. Basic access pattern risks
    admin_count = sum(1 for r in user_access.resources if r.access_type == AccessType.ADMIN)
    privileged_count = sum(1 for r in user_access.resources if r.is_privileged)
    providers = set(r.provider for r in user_access.resources)
    
    # Admin access risk
    admin_risk = admin_count * 12.0
    if admin_count > 0:
        all_risk_factors.append(RiskFactor(
            factor_type="admin_access",
            description=f"{admin_count} administrative access grants",
            weight=admin_risk,
            severity="high" if admin_count > 3 else "medium",
            justification="Administrative access provides broad system control"
        ))
        total_risk += admin_risk
        
        if admin_count > 5:
            all_recommendations.append("Review necessity of multiple admin access grants")
    
    # Privileged access risk
    priv_risk = privileged_count * 5.0
    if privileged_count > admin_count:  # Don't double-count admin as privileged
        all_risk_factors.append(RiskFactor(
            factor_type="privileged_access",
            description=f"{privileged_count} privileged access grants",
            weight=priv_risk,
            severity="medium",
            justification="Privileged access increases attack surface"
        ))
        total_risk += priv_risk
    
    # Cross-provider risk
    cross_provider_risk = len(providers) * 8.0 if len(providers) > 1 else 0.0
    if len(providers) > 2:
        all_risk_factors.append(RiskFactor(
            factor_type="cross_provider_access",
            description=f"Access across {len(providers)} cloud providers",
            weight=cross_provider_risk,
            severity="high" if len(providers) > 3 else "medium",
            justification="Multi-cloud access increases complexity and risk"
        ))
        total_risk += cross_provider_risk
        
        # Cross-provider admin bonus
        if admin_count > 0 and len(providers) > 2:
            bonus_risk = 25.0
            all_risk_factors.append(RiskFactor(
                factor_type="cross_provider_admin",
                description="Admin access across multiple providers",
                weight=bonus_risk,
                severity="critical",
                justification="Cross-cloud administrative access creates superuser risk"
            ))
            total_risk += bonus_risk
            user_access.cross_provider_admin = True
            all_recommendations.append("Audit cross-provider administrative access immediately")
    
    # 2. Cross-account access risk
    cross_account_risk = calculate_cross_account_risk(user_access)
    if cross_account_risk > 0:
        all_risk_factors.append(RiskFactor(
            factor_type="cross_account_access",
            description="Access across multiple accounts",
            weight=cross_account_risk,
            severity="medium",
            justification="Cross-account access increases lateral movement risk"
        ))
        total_risk += cross_account_risk
        all_recommendations.append("Review cross-account access patterns")
    
    # 3. Sensitive resource access risk
    sensitive_risk, sensitive_factors = calculate_sensitive_resource_risk(user_access)
    total_risk += sensitive_risk
    all_risk_factors.extend(sensitive_factors)
    if sensitive_risk > 20:
        all_recommendations.append("Implement additional monitoring for sensitive resource access")
    
    # 4. Unused privilege risk
    unused_risk, unused_factors = calculate_unused_privilege_risk(user_access)
    total_risk += unused_risk
    all_risk_factors.extend(unused_factors)
    if unused_risk > 15:
        all_recommendations.append("Remove unused privileges to reduce attack surface")
    
    # 5. Privilege escalation risk
    escalation_risk, escalation_factors, escalation_paths = calculate_privilege_escalation_risk(user_access)
    total_risk += escalation_risk
    all_risk_factors.extend(escalation_factors)
    user_access.privilege_escalation_paths = escalation_paths
    if escalation_risk > 20:
        all_recommendations.append("Redesign access grants to eliminate escalation paths")
    
    # 6. Service account adjustments
    if user_access.is_service_account:
        service_multiplier = 1.3
        service_bonus = total_risk * 0.3
        all_risk_factors.append(RiskFactor(
            factor_type="service_account",
            description="Service account with elevated privileges",
            weight=service_bonus,
            severity="medium",
            justification="Service accounts typically have persistent, unmonitored access"
        ))
        total_risk *= service_multiplier
        all_recommendations.append("Implement service account rotation and monitoring")
    
    # Calculate confidence score based on data completeness
    confidence_score = 0.8  # Base confidence
    if any(r.last_used for r in user_access.resources):
        confidence_score += 0.1  # Have usage data
    if len(user_access.resources) > 5:
        confidence_score += 0.1  # Sufficient sample size
    
    # Determine risk level
    final_score = min(total_risk, 100.0)
    if final_score >= 80:
        risk_level = "critical"
    elif final_score >= 60:
        risk_level = "high"
    elif final_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    # Add general recommendations
    if not all_recommendations:
        all_recommendations.append("Maintain current access patterns with regular reviews")
    
    all_recommendations.append("Enable MFA for all privileged accounts")
    all_recommendations.append("Implement regular access reviews")
    
    return RiskAnalysisResult(
        overall_score=final_score,
        risk_level=risk_level,
        risk_factors=all_risk_factors,
        recommendations=list(set(all_recommendations)),  # Remove duplicates
        confidence_score=min(confidence_score, 1.0)
    )

def analyze_user_access(user_access: UserAccess) -> UserAccess:
    """Perform comprehensive risk analysis on user access"""
    # Run comprehensive risk analysis
    risk_result = calculate_comprehensive_risk_score(user_access)
    
    # Update user access with results
    user_access.overall_risk_score = risk_result.overall_score
    
    # Calculate privilege escalation paths separately to ensure they're set
    _, _, escalation_paths = calculate_privilege_escalation_risk(user_access)
    user_access.privilege_escalation_paths = escalation_paths
    
    # Detect unused privileges with 90-day threshold
    user_access.unused_privileges = [
        f"{resource.provider}-{resource.service}"
        for resource in user_access.resources
        if resource.last_used and (datetime.utcnow() - resource.last_used).days > 90
    ]
    
    return user_access

# Audit Logging Functions
async def log_audit_event(
    event_type: str,
    user_email: str,
    action: str,
    details: Dict[str, Any],
    target_user: Optional[str] = None,
    risk_score_before: Optional[float] = None,
    risk_score_after: Optional[float] = None
):
    """Log audit events for compliance and monitoring"""
    audit_event = AuditEvent(
        event_type=event_type,
        user_email=user_email,
        target_user=target_user,
        action=action,
        details=details,
        risk_score_before=risk_score_before,
        risk_score_after=risk_score_after
    )
    
    try:
        await db.audit_logs.insert_one(audit_event.dict())
        logging.info(f"Audit event logged: {event_type} by {user_email}")
    except Exception as e:
        logging.error(f"Failed to log audit event: {str(e)}")

# Enhanced Analytics Functions
async def get_provider_risk_analytics(provider: Optional[str] = None) -> Dict[str, Any]:
    """Get risk analytics for specific provider or all providers"""
    users = await db.user_access.find().to_list(1000)
    
    analytics = {
        "total_users": 0,
        "risk_distribution": {"low": 0, "medium": 0, "high": 0, "critical": 0},
        "top_risks": [],
        "sensitive_resource_access": {},
        "privilege_escalation_count": 0,
        "cross_account_users": 0,
        "service_breakdown": {}
    }
    
    for user_doc in users:
        user_access = UserAccess(**user_doc)
        
        # Filter by provider if specified
        if provider:
            user_resources = [r for r in user_access.resources if r.provider == provider]
            if not user_resources:
                continue
            user_access.resources = user_resources
        
        analytics["total_users"] += 1
        
        # Perform risk analysis
        analyzed_user = analyze_user_access(user_access)
        risk_result = calculate_comprehensive_risk_score(analyzed_user)
        
        # Update risk distribution
        analytics["risk_distribution"][risk_result.risk_level] += 1
        
        # Track top risks
        if risk_result.overall_score > 40:
            analytics["top_risks"].append({
                "user_email": user_access.user_email,
                "user_name": user_access.user_name,
                "risk_score": risk_result.overall_score,
                "risk_level": risk_result.risk_level,
                "primary_risks": [rf.factor_type for rf in risk_result.risk_factors[:3]]
            })
        
        # Count privilege escalations
        if analyzed_user.privilege_escalation_paths:
            analytics["privilege_escalation_count"] += 1
        
        # Count cross-account access
        accounts = set(r.account_id for r in user_access.resources if r.account_id)
        if len(accounts) > 1:
            analytics["cross_account_users"] += 1
        
        # Service breakdown
        for resource in user_access.resources:
            service_key = f"{resource.provider}-{resource.service}"
            if service_key not in analytics["service_breakdown"]:
                analytics["service_breakdown"][service_key] = {
                    "user_count": 0,
                    "total_access": 0,
                    "admin_access": 0,
                    "avg_risk": 0.0
                }
            
            analytics["service_breakdown"][service_key]["total_access"] += 1
            if resource.access_type == AccessType.ADMIN:
                analytics["service_breakdown"][service_key]["admin_access"] += 1
    
    # Sort top risks by score
    analytics["top_risks"].sort(key=lambda x: x["risk_score"], reverse=True)
    analytics["top_risks"] = analytics["top_risks"][:20]  # Top 20
    
    return analytics

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
# Authentication endpoints
@api_router.post("/auth/signup")
async def signup(user_data: dict):
    """Register a new user"""
    try:
        email = user_data.get("email", "").strip().lower()
        password = user_data.get("password", "")
        full_name = user_data.get("full_name", "").strip()
        
        # Validation
        if not email or not password or not full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email, password, and full name are required"
            )
        
        if len(password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(password)
        
        # Determine role (first user is admin, others are users)
        user_count = await db.users.count_documents({})
        role = UserRole.ADMIN if user_count == 0 else UserRole.USER
        
        new_user = User(
            id=user_id,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            is_active=True,
            created_at=datetime.utcnow(),
            last_login=None
        )
        
        # Insert user into database
        await db.users.insert_one(new_user.dict())
        
        # Log audit event
        await log_audit_event(
            event_type="user_registration",
            user_email=email,
            action="create_account",
            details={
                "user_email": email,
                "full_name": full_name,
                "role": role.value,
                "registration_method": "signup"
            }
        )
        
        logging.info(f"New user registered: {email} with role {role.value}")
        
        return {
            "message": "User registered successfully",
            "user": {
                "email": email,
                "full_name": full_name,
                "role": role.value
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user account"
        )

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

# Enhanced API Endpoints

@api_router.get("/users/paginated")
async def get_users_paginated(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    sort_by: str = Query("risk_score", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of users with search and filtering"""
    try:
        # Calculate skip value
        skip = (page - 1) * page_size
        
        # Get all users and apply filters in memory (for advanced filtering)
        all_users = await db.user_access.find().to_list(10000)
        filtered_users = []
        
        for user_doc in all_users:
            user_access = UserAccess(**user_doc)
            
            # Apply search filter
            if search and search.lower() not in user_access.user_email.lower():
                continue
            
            # Apply provider filter
            if provider:
                # Filter resources by provider first
                provider_resources = [r for r in user_access.resources if r.provider.lower() == provider.lower()]
                if not provider_resources:
                    continue
                # Create a copy of user_access with only provider resources for analysis
                user_access = UserAccess(
                    user_email=user_access.user_email,
                    user_name=user_access.user_name,
                    department=user_access.department,
                    job_title=user_access.job_title,
                    is_service_account=user_access.is_service_account,
                    last_updated=user_access.last_updated,
                    resources=provider_resources,
                    cross_provider_admin=False,
                    privilege_escalation_paths=[],
                    unused_privileges=[],
                    overall_risk_score=0.0
                )
            
            # Perform risk analysis
            analyzed_user = analyze_user_access(user_access)
            risk_result = calculate_comprehensive_risk_score(analyzed_user)
            
            # Apply risk level filter
            if risk_level and risk_result.risk_level != risk_level:
                continue
            
            # Prepare user data for response
            user_data = {
                "user_email": user_access.user_email,
                "user_name": user_access.user_name,
                "department": user_access.department,
                "job_title": user_access.job_title,
                "is_service_account": user_access.is_service_account,
                "risk_score": risk_result.overall_score,
                "risk_level": risk_result.risk_level,
                "confidence_score": risk_result.confidence_score,
                "total_resources": len(user_access.resources),
                "admin_access_count": sum(1 for r in user_access.resources if r.access_type == AccessType.ADMIN),
                "providers": list(set(r.provider for r in user_access.resources)),
                "services": list(set(f"{r.provider}-{r.service}" for r in user_access.resources)),
                "cross_provider_admin": analyzed_user.cross_provider_admin,
                "privilege_escalation_count": len(analyzed_user.privilege_escalation_paths),
                "unused_privileges_count": len(analyzed_user.unused_privileges),
                "top_risk_factors": [rf.factor_type for rf in risk_result.risk_factors[:3]],
                "last_updated": user_access.last_updated
            }
            
            filtered_users.append(user_data)
        
        # Sort users
        reverse_sort = sort_order.lower() == "desc"
        if sort_by == "risk_score":
            filtered_users.sort(key=lambda x: x["risk_score"], reverse=reverse_sort)
        elif sort_by == "user_email":
            filtered_users.sort(key=lambda x: x["user_email"], reverse=reverse_sort)
        elif sort_by == "last_updated":
            filtered_users.sort(key=lambda x: x["last_updated"], reverse=reverse_sort)
        elif sort_by == "total_resources":
            filtered_users.sort(key=lambda x: x["total_resources"], reverse=reverse_sort)
        
        # Apply pagination
        total_users = len(filtered_users)
        paginated_users = filtered_users[skip:skip + page_size]
        
        return {
            "users": paginated_users,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_users": total_users,
                "total_pages": (total_users + page_size - 1) // page_size,
                "has_next": skip + page_size < total_users,
                "has_prev": page > 1
            },
            "filters": {
                "search": search,
                "provider": provider,
                "risk_level": risk_level,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
    
    except Exception as e:
        logging.error(f"Error getting paginated users: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving users")

@api_router.get("/analytics/provider/{provider}")
async def get_provider_analytics(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """Get analytics for a specific provider"""
    try:
        analytics = await get_provider_risk_analytics(provider)
        return analytics
    except Exception as e:
        logging.error(f"Error getting provider analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving provider analytics")

@api_router.get("/analytics/dashboard/{provider}")
async def get_provider_dashboard(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """Get dashboard data for a specific provider"""
    try:
        # Get provider-specific analytics
        analytics = await get_provider_risk_analytics(provider)
        
        # Get top risky services for this provider
        users = await db.user_access.find().to_list(1000)
        service_risks = {}
        
        for user_doc in users:
            user_access = UserAccess(**user_doc)
            provider_resources = [r for r in user_access.resources if r.provider == provider]
            
            if not provider_resources:
                continue
                
            user_access.resources = provider_resources
            analyzed_user = analyze_user_access(user_access)
            
            for resource in provider_resources:
                service_key = resource.service
                if service_key not in service_risks:
                    service_risks[service_key] = {
                        "service": service_key,
                        "total_users": 0,
                        "admin_users": 0,
                        "avg_risk": 0.0,
                        "total_risk": 0.0,
                        "high_risk_users": []
                    }
                
                service_risks[service_key]["total_users"] += 1
                service_risks[service_key]["total_risk"] += analyzed_user.overall_risk_score
                
                if resource.access_type == AccessType.ADMIN:
                    service_risks[service_key]["admin_users"] += 1
                
                if analyzed_user.overall_risk_score > 60:
                    service_risks[service_key]["high_risk_users"].append({
                        "user_email": user_access.user_email,
                        "risk_score": analyzed_user.overall_risk_score
                    })
        
        # Calculate average risk per service
        for service_data in service_risks.values():
            if service_data["total_users"] > 0:
                service_data["avg_risk"] = service_data["total_risk"] / service_data["total_users"]
        
        # Sort services by average risk
        top_risky_services = sorted(
            service_risks.values(),
            key=lambda x: x["avg_risk"],
            reverse=True
        )[:10]
        
        return {
            "provider": provider,
            "summary": analytics,
            "top_risky_services": top_risky_services,
            "dashboard_widgets": [
                {
                    "type": "risk_distribution",
                    "title": f"{provider.upper()} Risk Distribution",
                    "data": analytics["risk_distribution"]
                },
                {
                    "type": "top_risks",
                    "title": f"Top {provider.upper()} Risks",
                    "data": analytics["top_risks"][:5]
                },
                {
                    "type": "service_breakdown",
                    "title": f"{provider.upper()} Service Breakdown",
                    "data": top_risky_services[:5]
                }
            ]
        }
    
    except Exception as e:
        logging.error(f"Error getting provider dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving dashboard data")

@api_router.get("/risk-analysis/{user_email}")
async def get_user_risk_analysis(
    user_email: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed risk analysis for a specific user"""
    try:
        user_doc = await db.user_access.find_one({"user_email": user_email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_access = UserAccess(**user_doc)
        analyzed_user = analyze_user_access(user_access)
        risk_result = calculate_comprehensive_risk_score(analyzed_user)
        
        return {
            "user_email": user_email,
            "user_name": user_access.user_name,
            "department": user_access.department,
            "job_title": user_access.job_title,
            "is_service_account": user_access.is_service_account,
            "overall_risk_score": risk_result.overall_score,
            "risk_level": risk_result.risk_level,
            "confidence_score": risk_result.confidence_score,
            "risk_factors": [rf.dict() for rf in risk_result.risk_factors],
            "recommendations": risk_result.recommendations,
            "cross_provider_admin": analyzed_user.cross_provider_admin,
            "privilege_escalation_paths": [path.dict() for path in analyzed_user.privilege_escalation_paths],
            "unused_privileges": analyzed_user.unused_privileges,
            "admin_access_count": sum(1 for r in user_access.resources if r.access_type == AccessType.ADMIN),
            "privileged_access_count": sum(1 for r in user_access.resources if r.is_privileged),
            "providers_with_access": list(set(r.provider for r in user_access.resources)),
            "services_with_access": list(set(f"{r.provider}-{r.service}" for r in user_access.resources)),
            "total_resources": len(user_access.resources),
            "last_updated": user_access.last_updated,
            "resource_details": [
                {
                    "provider": r.provider,
                    "service": r.service,
                    "resource_name": r.resource_name,
                    "access_type": r.access_type.value if hasattr(r.access_type, 'value') else str(r.access_type),
                    "is_privileged": r.is_privileged,
                    "account_id": r.account_id,
                    "last_used": r.last_used.isoformat() if r.last_used else None,
                    "mfa_required": r.mfa_required
                } for r in user_access.resources
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting risk analysis for user {user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving risk analysis")

@api_router.delete("/users/access/{user_email}")
async def delete_user_access(
    user_email: str,
    current_user: User = Depends(get_current_user)
):
    """Delete user access data (requires admin or self)"""
    try:
        # Check if user can delete this access data
        if current_user.role != UserRole.ADMIN and current_user.email != user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this user's access data"
            )
        
        # Get user data before deletion for audit
        user_doc = await db.user_access.find_one({"user_email": user_email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User access data not found")
        
        user_access = UserAccess(**user_doc)
        risk_score_before = analyze_user_access(user_access).overall_risk_score
        
        # Delete user access data
        result = await db.user_access.delete_one({"user_email": user_email})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User access data not found")
        
        # Log audit event
        await log_audit_event(
            event_type="user_access_deletion",
            user_email=current_user.email,
            target_user=user_email,
            action="delete_user_access",
            details={
                "deleted_user": user_email,
                "resource_count": len(user_access.resources),
                "providers": list(set(r.provider for r in user_access.resources))
            },
            risk_score_before=risk_score_before
        )
        
        return {"message": f"User access data for {user_email} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting user access for {user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting user access data")

@api_router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get audit logs (Admin only)"""
    try:
        skip = (page - 1) * page_size
        
        # Build query filter
        query_filter = {}
        if event_type:
            query_filter["event_type"] = event_type
        
        # Get total count
        total_logs = await db.audit_logs.count_documents(query_filter)
        
        # Get paginated logs
        logs = await db.audit_logs.find(query_filter)\
            .sort("timestamp", -1)\
            .skip(skip)\
            .limit(page_size)\
            .to_list(page_size)
        
        return {
            "logs": [AuditEvent(**log).dict() for log in logs],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_logs": total_logs,
                "total_pages": (total_logs + page_size - 1) // page_size,
                "has_next": skip + page_size < total_logs,
                "has_prev": page > 1
            }
        }
    
    except Exception as e:
        logging.error(f"Error getting audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving audit logs")

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

async def initialize_admin_users():
    """Create default admin users if they don't exist"""
    try:
        # Admin users to create
        admin_users = [
            {
                "email": "adminn@iamsharan.com",
                "full_name": "Admin User",
                "password": "Testing@123"
            },
            {
                "email": "self@iamsharan.com", 
                "full_name": "Self Admin",
                "password": "Testing@123"
            }
        ]
        
        for admin_data in admin_users:
            # Check if admin user already exists
            existing_admin = await db.users.find_one({"email": admin_data["email"]})
            if not existing_admin:
                # Create admin user
                admin_id = str(uuid.uuid4())
                hashed_password = hash_password(admin_data["password"])
                
                admin_user = User(
                    id=admin_id,
                    email=admin_data["email"],
                    full_name=admin_data["full_name"],
                    hashed_password=hashed_password,
                    role=UserRole.ADMIN,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    last_login=None
                )
                
                await db.users.insert_one(admin_user.dict())
                logging.info(f"Created admin user: {admin_data['email']}")
                
                # Log audit event
                await log_audit_event(
                    event_type="admin_creation",
                    user_email="system",
                    action="create_admin_user",
                    details={
                        "admin_email": admin_data["email"],
                        "full_name": admin_data["full_name"],
                        "creation_method": "system_initialization"
                    }
                )
    except Exception as e:
        logging.error(f"Error creating admin users: {str(e)}")

# Application startup
@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logging.info("Starting Cloud Access Visualizer API...")
    
    # Initialize admin users
    await initialize_admin_users()
    
    logging.info("Cloud Access Visualizer API started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()