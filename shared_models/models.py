# shared_models/models.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field
from uuid import UUID, uuid4
from pydantic import BaseModel, field_validator
import re

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email address")
        return v 

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class TaskStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    retrying = "retrying"
    cancelling = "cancelling"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class SEOAnalysisStatus(BaseModel):
    task_id: str  # or UUID if task_id is a UUID
    status: TaskStatus  # the enum used for task status
    progress_message: str = ""
    recommendations: List[Any] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TopicRequest(BaseModel):
    user_token: str
    website_url: str
    force_regenerate: bool = False  # 👈 new flag (default = False)

class SEODeployRequest(BaseModel):
    deployment_plan: Dict[str, Any]
    website_url: str
    user_id: str
    site_id: str
    task_id: str


# --- Enums ---
class SEOIssueLevel(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class AuditStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class OptimizationLevel(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"
    AGGRESSIVE = "aggressive"


class AgentType(str, Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    SCHEMA = "schema"
    COMPETITOR = "competitor"
    PERFORMANCE = "performance"
    STRATEGY = "strategy"
    WRITING = "writing"
    REVIEW = "review"
    MEDIA = "media"
    FAQ = "faq"


# class AgentRun(BaseModel):
#     id: str = Field(default_factory=lambda: str(uuid4()))
#     task_id: Optional[str] = None  # FK to seo_tasks.id
#     agent_type: AgentType
#     service_type: str = "seo"  # new column
#     attempt: int
#     status: str
#     error_message: Optional[str] = None
#     created_at: datetime = Field(default_factory=datetime.now)
#     url_id: Optional[str] = None  # FK to page_seo_data.id


# SEO agent run
class SEOAgentRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str  # FK to seo_tasks.id
    agent_type: AgentType
    attempt: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    url_id: str  # FK to page_seo_data.id


# Blog agent run
class BlogAgentRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str  # FK to blog_tasks.id
    agent_type: AgentType
    attempt: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    url_id: Optional[str] = None  # if needed

 

# ---------- Core Data Classes ----------
# ✅ KEEP ONLY ONE DEFINITION OF EACH CLASS


class SEOIssue(BaseModel):
    type: str
    level: SEOIssueLevel
    message: str
    element: Optional[str] = None
    recommendation: str = ""
    weight: float = 1.0
    fixable: bool = True
    auto_fix_available: bool = False
    agent_type: Optional[AgentType] = None


class MetaTag(BaseModel):
    name: Optional[str] = None
    property: Optional[str] = None
    content: Optional[str] = None
    http_equiv: Optional[str] = None
    charset: Optional[str] = None
    original_position: Optional[int] = None
    suggested_content: Optional[str] = None
    is_optimal: bool = False


class ImageTag(BaseModel):
    src: str
    alt: str = ""
    title: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    loading: Optional[str] = None
    srcset: Optional[str] = None
    needs_optimization: bool = False
    suggested_alt: Optional[str] = None
    optimized_src: Optional[str] = None


class LinkTag(BaseModel):
    url: str
    text: str = ""
    anchor_text: str = ""
    nofollow: bool = False
    title: str = ""
    is_internal: bool = False
    is_broken: bool = False
    suggested_anchor: Optional[str] = None
    link_equity: float = 1.0
    rel: List[str] = Field(default_factory=list)


class ContentMetrics(BaseModel):
    word_count: int = 0
    sentence_count: int = 0
    avg_words_per_sentence: float = 0.0
    unique_words: int = 0
    char_count: int = 0
    readability_score: float = 0.0
    keyword_density: Dict[str, float] = Field(default_factory=dict)
    content_quality_score: float = 0.0
    semantic_relevance: Dict[str, float] = Field(default_factory=dict)
    image_count: int = 0  # ✅ existing
    # New optional fields for AI recommender
    primary_keyword: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None


class SchemaMarkup(BaseModel):
    type: str
    data: Dict[str, Any]
    suggested_markup: Optional[Dict[str, Any]] = None
    schema_type: Optional[str] = None
    validation_errors: List[str] = Field(default_factory=list)


class HeadingStructure(BaseModel):
    h1: List[str] = Field(default_factory=list)
    h2: List[str] = Field(default_factory=list)
    h3: List[str] = Field(default_factory=list)
    h4: List[str] = Field(default_factory=list)
    h5: List[str] = Field(default_factory=list)
    h6: List[str] = Field(default_factory=list)
    hierarchy_issues: List[str] = Field(default_factory=list)
    suggested_improvements: Dict[str, List[str]] = Field(default_factory=dict)
    semantic_structure: Dict[str, List[str]] = Field(default_factory=dict)


# ---------- Updated Core Classes ----------


class PagePerformance(BaseModel):
    load_time: float
    page_size: int
    requests_count: int
    dom_size: int
    performance_score: float
    core_web_vitals: Dict[str, float]


class MobileReadiness(BaseModel):
    viewport_configured: bool
    tap_targets_size: bool
    font_sizes: bool
    responsive_images: bool
    mobile_score: float
    mobile_usability_issues: List[str]


class SecurityMetrics(BaseModel):
    https: bool
    secure_cookies: bool
    xss_protection: bool
    content_security_policy: bool
    security_score: float
    security_headers: Dict[str, str]


class PageSEOData(BaseModel):
    url: str
    url_id: Optional[str] = None
    title: str
    meta_tags: List[MetaTag]
    headings: HeadingStructure
    images: List[ImageTag]
    links: List[LinkTag]
    schema_markup: List[SchemaMarkup]
    content_metrics: ContentMetrics
    content_text: str
    extracted_keywords: List[str]
    canonical_url: Optional[str] = None
    language: Optional[str] = None
    charset: Optional[str] = None
    viewport: Optional[str] = None
    performance: Optional[PagePerformance] = None
    mobile: Optional[MobileReadiness] = None
    security: Optional[SecurityMetrics] = None
    robots_directives: Dict[str, str] = Field(default_factory=dict)
    social_media_tags: Dict[str, str] = Field(default_factory=dict)
    id: Optional[UUID] = None  # ✅ ADD: matches page_seo_data.id (primary key)
    task_id: Optional[UUID] = None  # ✅ ADD: matches page_seo_data.task_id
    created_at: Optional[datetime] = None  # ✅ ADD
    updated_at: Optional[datetime] = None  # ✅ ADD


class SEOAuditResult(BaseModel):
    url: Optional[str] = None
    url_id: Optional[str] = None
    overall_score: float = 0.0
    audit_version: str = "1.0"
    page_data: Optional[PageSEOData] = None
    metrics: Optional[ContentMetrics] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    category_scores: Dict[str, float] = Field(default_factory=dict)
    issues: List[SEOIssue] = Field(default_factory=list)
    warnings: List[SEOIssue] = Field(default_factory=list)
    recommendations: List[SEOIssue] = Field(default_factory=list)
    passed_checks: List[str] = Field(default_factory=list)
    analyzer_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    ai_triggers: List[str] = Field(
        default_factory=list
    )  # e.g. ["content_quality", "schema_missing"],
    ai_agents_used: list[str] = []  # <-- add this
    extracted_keywords: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    task_id: Optional[UUID] = None  # ✅ ADD: matches seo_audit_results.task_id
    id: Optional[UUID] = None  # ✅ ADD: matches seo_audit_results.id (primary key)
    created_at: Optional[datetime] = None  # ✅ ADD
    updated_at: Optional[datetime] = None  # ✅ ADD


class SEOTask(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    website_id: Optional[UUID] = None
    status: str = "pending"
    progress_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class AIRecommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: Optional[str] = None
    url_id: Optional[str] = (
        None  # NEW: corresponds to ai_recommendations.url_id → page_seo_data.id
    )
    type: str
    original: str
    suggested: str
    confidence_score: float
    reasoning: str
    impact_score: float
    agent_type: AgentType
    implementation_complexity: str
    estimated_time: int
    created_at: datetime = Field(default_factory=datetime.now)


# --- SEO Pixel Models ---

class PixelGenerationRequest(BaseModel):
    user_id: str
    website_id: str
    options: Optional[Dict[str, Any]] = None  # Optional configuration

class PixelResponse(BaseModel):
    pixel_id: str
    script_code: str
    installation_instructions: Optional[str] = None

class PixelDeploymentRequest(BaseModel):
    pixel_id: str
    url: str

class PixelRollbackRequest(BaseModel):
    website_id: str
    url: str
    version_id: str

class PixelStatusResponse(BaseModel):
    pixel_id: str
    website_id: str
    is_active: bool
    deployed_versions: List[str] = []
    last_updated: Optional[datetime] = None


class PixelDeploymentPlan(BaseModel):
    url_id: str
    pixel_id: str
    page_url: str
    optimizations: Dict[str, Any]
    rollback_strategy: Dict[str, Any]
    estimated_impact: float
    risk_level: str
    dependencies: List[Dict[str, str]]
    required_approval: bool
    deployment_order: List[str]
    validation_rules: List[Dict[str, Any]]
    created_at: datetime = Field(default_factory=datetime.now)


class DeploymentResult(BaseModel):
    deployment_id: str
    status: DeploymentStatus
    applied_changes: List[Dict[str, Any]]
    failed_changes: List[Dict[str, Any]]
    rollback_actions: List[Dict[str, Any]]
    performance_impact: Dict[str, float]
    deployment_time: datetime
    deployed_by: Optional[str] = None


class MonitoringData(BaseModel):
    audit_id: str
    timestamp: datetime
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    improvement_rate: float
    google_search_console_data: Optional[Dict[str, Any]] = None
    google_analytics_data: Optional[Dict[str, Any]] = None
    rank_tracking: Optional[Dict[str, Any]] = None
    traffic_analysis: Optional[Dict[str, Any]] = None
    conversion_metrics: Optional[Dict[str, Any]] = None





class WebsiteInfo(BaseModel):
    title: str
    description: str
    user_id: str
    website_url: str
    task_id: str


class User(BaseModel):
    id: UUID
    name: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class UserSettings(BaseModel):
    user_id: str
    website_configs: Optional[Dict[str, "WebsiteConfig"]] = None
    default_optimization_level: Optional["OptimizationLevel"] = None
    email_notifications: bool = False
    dashboard_preferences: Dict[str, Any] = {}
    api_access: bool = False
    data_retention_days: int = 30
    export_preferences: Dict[str, Any] = {}

    # --- AI Blog Writer (MediaAgent) ---
    allow_ai_images: Optional[bool] = True
    include_youtube_videos: Optional[bool] = True
    max_youtube_videos_per_post: Optional[int] = 1
    image_style: Optional[str] = "photorealistic"
    custom_image_prompt: Optional[str] = None
    preferred_youtube_channels: Optional[List[str]] = None

    # --- OnPageSEO ---
    include_schema_markup: Optional[bool] = True
    track_core_web_vitals: Optional[bool] = True
    auto_fix_minor_issues: Optional[bool] = False



class TopicSuggestionRequest(BaseModel):
    website_info: WebsiteInfo
    count: int = 10  # New field

class AgentResult(BaseModel):
    agent_type: AgentType
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    processing_time: float
    confidence_score: float
    cost_estimate: float
    tokens_used: Optional[int] = None


class BatchProcessingResult(BaseModel):
    batch_id: str
    processed_urls: int
    successful_urls: int
    failed_urls: int
    total_issues_found: int
    average_score: float
    processing_time: float
    ai_calls_made: int
    total_cost: float


# ---------- Pydantic Models for API ----------
class SEOAnalysisRequest(BaseModel):
    url: Optional[HttpUrl] = None
    html: Optional[str] = None
    include_recommendations: bool = True
    deep_analysis: bool = False
    include_performance: bool = False
    include_security: bool = False
    include_mobile: bool = False
    optimization_level: OptimizationLevel = OptimizationLevel.STANDARD
    enable_ai_agents: bool = True
    agent_config: Dict[AgentType, bool] = Field(
        default_factory=lambda: {
            AgentType.KEYWORD: True,
            AgentType.SEMANTIC: True,
            AgentType.SCHEMA: True,
        }
    )
    user_id: Optional[UUID] = None
    task_id: Optional[UUID] = None   # ✅ add this
    website_id: Optional[UUID] = None
    force_refresh: bool = False


class SEOAnalysisResponse(BaseModel):
    audit_id: str
    url: Optional[str] = None
    url_id: Optional[UUID] = None  # ✅ ADD: needed for database relationships
    status: AuditStatus
    score: float
    issues: List[SEOIssue]
    issues_count: int
    warnings: List[SEOIssue] = Field(default_factory=list)  # ✅ include full warnings
    warnings_count: int
    recommendations: Optional[List[AIRecommendation]] = None
    task_id: Optional[UUID] = None  # ✅ ADD: needed for task tracking
    estimated_completion_time: Optional[datetime] = None

    # --- NEW FIELDS from SEOAuditResult ---
    ai_agents_used: List[str] = Field(default_factory=list)  # ✅ map ai_triggers
    metrics: Optional[ContentMetrics] = None  # ✅ word count, density, etc.
    page_data: Optional[PageSEOData] = None  # ✅ full parsed page data
    analyzer_context: Optional[Dict[str, Any]] = None  # ✅ headings, schema, keywords
    extracted_keywords: List[str] = Field(default_factory=list)
    industry: Optional[str] = None

    # --- SYSTEM FIELDS ---
    cached: bool = False
    generated_at: datetime = Field(default_factory=datetime.now)


class DeploymentRequest(BaseModel):
    audit_id: str
    changes_to_apply: List[str]
    confirmation_required: bool = True
    optimization_level: OptimizationLevel = OptimizationLevel.STANDARD
    deployment_strategy: str = "conservative"
    scheduled_time: Optional[datetime] = None
    user_id: UUID


class DeploymentResponse(BaseModel):
    deployment_id: str
    status: DeploymentStatus
    applied_changes: List[str]
    requires_confirmation: bool = False
    scheduled_time: Optional[datetime] = None
    estimated_impact: float = 0.0
    deployed_at: Optional[datetime] = None


class MonitoringRequest(BaseModel):
    website_url: HttpUrl
    timeframe_days: int = 30
    include_gsc: bool = True
    include_ga: bool = True
    include_rank_tracking: bool = True
    include_traffic: bool = True
    include_conversion: bool = False


class MonitoringResponse(BaseModel):
    audit_id: str
    website_url: HttpUrl
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    improvement_rate: float
    google_search_console_data: Optional[Dict[str, Any]] = None
    google_analytics_data: Optional[Dict[str, Any]] = None
    rank_tracking: Optional[Dict[str, Any]] = None
    traffic_analysis: Optional[Dict[str, Any]] = None
    conversion_metrics: Optional[Dict[str, Any]] = None
    timestamp: datetime


class BatchAuditRequest(BaseModel):
    urls: List[HttpUrl]


LANGUAGES_SUPPORTED = [
    "en",
    "es",
    "fr",
    "de",
    "hi",
    "zh",
    "ar",
    "pt",
    "ru",
    "ja",
    "ko",
    "it",
    "tr",
    "nl",
    "sv",
    "fi",
    "no",
    "da",
    "pl",
    "cs",
    "el",
    "he",
    "id",
    "ms",
    "th",
    "vi",
    "bn",
    "ta",
    "te",
    "mr",
    "gu",
    "kn",
    "pa",
    "ur",
    "fa",
    "ro",
    "hu",
    "uk",
    "sr",
    "sk",
    "sl",
    "hr",
    "bg",
    "lt",
    "lv",
    "et",
    "mt",
    "is",
    "cy",
    "sq",
    "sw",
]


class BatchAuditResponse(BaseModel):
    batch_id: str
    total_urls: int
    processed_urls: int
    successful_urls: int
    failed_urls: int
    total_issues_found: int
    average_score: float
    status: AuditStatus
    started_at: datetime
    completed_at: Optional[datetime] = None


class AIRecommendationRequest(BaseModel):
    url: HttpUrl
    agent_type: AgentType
    content: Optional[str] = None
    meta_tags: Optional[List[MetaTag]] = None
    headings: Optional[HeadingStructure] = None
    images: Optional[List[ImageTag]] = None
    links: Optional[List[LinkTag]] = None
    schema_markup: Optional[List[SchemaMarkup]] = None
    optimization_level: OptimizationLevel = OptimizationLevel.STANDARD
    audit_result: Optional[SEOAuditResult] = None


class AIRecommendationResponse(BaseModel):
    recommendations: List[AIRecommendation]
    confidence_avg: float
    processing_time: float
    agent_type: AgentType
    audit_id: Optional[str] = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None





class OrchestrationRequest(BaseModel):
    user_token: str
    website_url: str
    target_language: Optional[str] = "en"
    generate_article: Optional[bool] = True
    run_seo_audit: Optional[bool] = True
    article_preferences: Optional[dict] = None


class WebsiteAnalysisRequest(BaseModel):
    user_token: str
    website_url: str
    analysis_type: Optional[str] = "comprehensive"


class OrchestrationResponse(BaseModel):
    article_id: Optional[str] = None
    seo_report: Optional[dict] = None
    message: str
    task_id: Optional[str] = None


class WebsiteAnalysisResponse(BaseModel):
    task_id: str
    message: str
    analysis_type: str


class PublishingStatusResponse(BaseModel):
    job_id: str
    status: str
    article_id: str
    cms_platform: str
    cms_url: Optional[str] = None
    error_message: Optional[str] = None
    links_added: Optional[int] = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)



class CMSPlatform(str, Enum):
    WORDPRESS = "wordpress"
    WEBFLOW = "webflow"
    SHOPIFY = "shopify"
    HUBSPOT = "hubspot"
    NOTION = "notion"
    WIX = "wix"
    GHOST = "ghost"
    FRAMER = "framer"
    MEDIUM = "medium"
    BLOGGER = "blogger"
    SUBSTACK = "substack"
    BITSANDBYTES = "bitsandbytes"


class CMSCredentials(BaseModel):
    cms_platform: CMSPlatform
    # Generic optional fields; only some CMS need these
    url: Optional[HttpUrl] = None
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    admin_api_key: Optional[str] = None
    content_api_key: Optional[str] = None
    blog_id: Optional[str] = None
    base_url: Optional[HttpUrl] = None
    publication_id: Optional[str] = None

    @field_validator("url", mode="before")
    def validate_url(cls, v, values):
        platform = values.get("cms_platform")
        if platform == CMSPlatform.wordpress and not v:
            raise ValueError("WordPress credentials require a 'url'.")
        return v

    @field_validator("api_key", mode="before")
    def validate_api_key(cls, v, values):
        platform = values.get("cms_platform")
        if platform in {CMSPlatform.webflow, CMSPlatform.notion, CMSPlatform.wix,
                        CMSPlatform.substack, CMSPlatform.bits_and_bytes} and not v:
            raise ValueError(f"{platform.value} credentials require an 'api_key'.")
        return v

    @field_validator("access_token", mode="before")
    def validate_access_token(cls, v, values):
        platform = values.get("cms_platform")
        if platform in {CMSPlatform.shopify, CMSPlatform.hubspot, CMSPlatform.medium} and not v:
            raise ValueError(f"{platform.value} credentials require an 'access_token'.")
        return v

    @field_validator("admin_api_key", mode="before")
    def validate_ghost_keys(cls, v, values):
        platform = values.get("cms_platform")
        content_api_key = values.get("content_api_key")
        if platform == CMSPlatform.ghost and not (v or content_api_key):
            raise ValueError("Ghost credentials require 'admin_api_key' or 'content_api_key'.")
        return v



# --- CMS Credential Models ---
@dataclass
class WordPressCredentials:
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    application_password: Optional[str] = None

@dataclass  
class WebflowCredentials:
    api_key: str
    site_id: Optional[str] = None
    collection_id: Optional[str] = None

@dataclass
class ShopifyCredentials:
    shop_name: str
    access_token: str
    blog_id: Optional[str] = None

@dataclass
class HubSpotCredentials:
    access_token: str

@dataclass
class NotionCredentials:
    api_key: str
    database_id: Optional[str] = None

@dataclass
class WixCredentials:
    api_key: str
    instance_id: Optional[str] = None

@dataclass
class GhostCredentials:
    url: str
    admin_api_key: Optional[str] = None
    content_api_key: Optional[str] = None

@dataclass
class FramerCredentials:
    api_key: str

@dataclass
class MediumCredentials:
    access_token: str
    user_id: Optional[str] = None
    publication_id: Optional[str] = None

@dataclass
class BloggerCredentials:
    blog_id: str
    access_token: Optional[str] = None
    api_key: Optional[str] = None

@dataclass
class SubstackCredentials:
    api_key: str

@dataclass
class BitsAndBytesCredentials:
    api_key: str

@dataclass
class CustomRestAPICredentials:
    base_url: str
    auth_type: str  # "bearer", "basic", "api_key", "none"
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None
    endpoint: Optional[str] = None
    test_endpoint: Optional[str] = None
 
    
    

# Keep, but cms_credentials should be typed to correct dataclass union WebsiteConfig MODIFY
class WebsiteConfig(BaseModel):
    url: str
    auto_optimize: bool
    optimization_level: OptimizationLevel
    allowed_domains: List[str]
    excluded_paths: List[str]
    crawl_depth: int
    schedule: str
    notification_settings: Dict[str, bool]
    ai_agent_settings: Dict[AgentType, bool]
    deployment_preferences: Dict[str, Any]
    monitoring_settings: Dict[str, Any]
    cms_credentials: Optional[
    Union[
        WordPressCredentials,
        WebflowCredentials,
        ShopifyCredentials,
        HubSpotCredentials,
        NotionCredentials,
        WixCredentials,
        GhostCredentials,
        FramerCredentials,
        MediumCredentials,
        BloggerCredentials,
        SubstackCredentials,
        BitsAndBytesCredentials,
        CustomRestAPICredentials,
    ]
] = None


# ---------- CMS Integration Models ----------
class CMSContentUpdate(BaseModel):
    platform: CMSPlatform
    content_id: str
    changes: Dict[str, Any]
    credentials: Union[
        WordPressCredentials, WebflowCredentials, ShopifyCredentials, 
        HubSpotCredentials, NotionCredentials, WixCredentials, GhostCredentials,
        FramerCredentials, MediumCredentials, BloggerCredentials, 
        SubstackCredentials, BitsAndBytesCredentials, CustomRestAPICredentials
    ]

class CMSContentResponse(BaseModel):
    success: bool
    content_id: str
    platform: CMSPlatform
    updated_fields: List[str]
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchAnalysisRequest(BaseModel):
    website_id: UUID
    max_pages: int = 10
    analysis_type: str = "standard"

class BatchAnalysisResponse(BaseModel):
    task_id: str
    status: str  # e.g., "pending", "processing", "completed", "failed"
    message: Optional[str] = None

class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    service_type: str  # e.g., "seo", "blog", "cms", "deployment"
    status: TaskStatus = TaskStatus.PENDING
    user_id: Optional[UUID] = None
    target_id: Optional[UUID] = None  # e.g., page_id, article_id, deployment_id
    progress_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None  # generic result container

class TaskCreate(BaseModel):
    service_type: str
    user_id: Optional[UUID] = None
    target_id: Optional[UUID] = None
    initial_data: Optional[Dict[str, Any]] = None


# ---------- Blog/Article Models ----------
class ArticleStatus(str, Enum):
    DRAFT = "draft"
    WRITING = "writing"
    REVIEW = "review"
    PUBLISHED = "published"
    FAILED = "failed"

class Article(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    title: str
    content: str
    status: ArticleStatus = ArticleStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class ArticleCreate(BaseModel):
    user_id: Optional[UUID] = None
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[ArticleStatus] = None
    metadata: Optional[Dict[str, Any]] = None
    
    
#   check if these are already preesent as something else   
# # ---------- User Models ----------
# class User(BaseModel):
#     id: UUID
#     email: EmailStr
#     username: str
#     hashed_password: str
#     role: str = "free"   # free, premium, admin
#     profile_image_url: Optional[str] = None
#     created_at: datetime
#     updated_at: datetime

# class UserCreate(BaseModel):
#     email: EmailStr
#     username: str
#     password: str
#     role: str = "free"
#     profile_image_url: Optional[str] = None

# class UserUpdate(BaseModel):
#     username: Optional[str] = None
#     password: Optional[str] = None
#     role: Optional[str] = None
#     profile_image_url: Optional[str] = None
