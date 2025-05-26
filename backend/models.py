from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid

# Enhanced models for real cloud data integration

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

# Integration Configuration
class IntegrationConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: CloudProvider
    config_name: str
    credentials: Dict[str, str]  # Encrypted storage
    is_active: bool = True
    last_sync: Optional[datetime] = None
    sync_status: str = "pending"  # pending, success, failed
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# JSON Import Schema
class JsonImportSchema(BaseModel):
    users: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    import_timestamp: datetime = Field(default_factory=datetime.utcnow)

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

# Export Models
class ExportRequest(BaseModel):
    format: str  # csv, xlsx, json
    filters: Optional[SearchFilter] = None
    include_risk_analysis: bool = True
    include_metadata: bool = False

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