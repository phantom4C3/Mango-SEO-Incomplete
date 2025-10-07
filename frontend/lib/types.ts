// frontend/lib/types.ts 
export type UUID = string;
import { Session } from "@supabase/supabase-js";

export type Nullable<T> = T | null | undefined; 
export type JSONPrimitive = string | number | boolean | null;
export type JSONValue = JSONPrimitive  | JSONObject; 
export interface JSONObject { [key: string]: JSONValue; }

export type DeepPartial<T> = { [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]; };

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type MakeRequired<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>;
  
export interface TopicRequest {
  website_url: string;
  force_regenerate?: boolean;  // default false
}

export interface BatchAnalysisRequest {
  website_id: string;
  max_pages?: number;
  analysis_type?: string;   // ✅ add this
}


export interface BatchAnalysisResponse {
  task_id: string;
  status: string;
  message?: string;
}

export interface SEOAnalysisResponse {
  task_id: string;
  status: string;  // e.g., "pending"
  message: string;
}

export interface SEOAnalysisRequest {
  user_id?: string;                      // REQUIRED by backend
  url?: string;
  html?: string;
  depth?: number;                        // REQUIRED by backend
  analysis_type?: string;                // REQUIRED by backend
  include_recommendations?: boolean;
  deep_analysis?: boolean;
  include_performance?: boolean;
  include_security?: boolean;
  include_mobile?: boolean;
  optimization_level?: string;
  enable_ai_agents?: boolean;
  agent_config?: Record<string, boolean>;
  website_id?: string;
  force_refresh?: boolean;
}


// Matches backend /seo/pixel/generate
export interface PixelGenerationRequest {
  website_id: string;               // UUID of the website
  options?: Record<string, any>;    // e.g., pixelType and other settings
}

// Matches backend /seo/pixel/rollback
export interface PixelRollbackRequest {
  website_id: string;   // UUID of the website
  url: string;          // page URL for rollback
  version_id?: string;  // optional version to rollback to
}

export interface OrchestrateWebsiteResponse {
  task_id: string;
  message: string;
}

export interface GenerateTopicsResponse {
  task_id: string;
  status: string;
  message?: string;
  topics?: any[];
  skipped_existing?: boolean;
}

export interface PixelResponse {
  pixel_id: string;
  script_code: string;
  installation_instructions: string;
}

export interface PixelDeploymentResponse {
  success: boolean;
  optimizations: Record<string, any>;
  timestamp?: string;
  error?: string;
}

export interface SEOAnalysisStatus {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress?: number; // optional progress percentage
  result_url?: string; // optional link to report
}


export interface PixelRollbackResponse {
  success: boolean;
  message: string;
}

export interface PixelStatusResponse {
  pixel_id: string;
  website_id: string;
  is_active: boolean;
  last_seen?: string;
  analytics?: Record<string, any>;
}

export interface TaskStatusResponse {
  id: string;
  status: string;
  progress: string;
  user_id: string;
  task_type: string;
  parameters: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface PublishArticleResponse {
  status: string;    // "processing"
  message: string;   // "Publishing started"
  task_id: string;   // UUID
}

export interface CancelOrchestrationResponse {
  message: string;
  task_id: string;
  status: string;
}

export interface ConversationState {
  // --------------------------
  // State
  // --------------------------
  answers: Record<string, "yes" | "no">;
  taskLogs: Record<string, TaskLog[]>; // optimistic logs only
  messages: Message[];
  isLoading: boolean;
  suggestedResponses: string[];
  context: {
    previousMessages: Message[];
  };

  // --------------------------
  // Actions
  // --------------------------
  submitAnswer: (promptId: string, answer: "yes" | "no") => void;
  submitWebsite: (websiteUrl: string) => Promise<void>;

  runSEOAnalysis: (data: SEOAnalysisRequest) => Promise<void>;
  batchSEOAnalysis: (data: BatchAnalysisRequest) => Promise<void>;

  generateTopics: (data: TopicRequest) => Promise<void>;
  publishArticle: (articleId: string) => Promise<void>;

  generateSEOPixel: (data: PixelGenerationRequest) => Promise<void>;
  rollbackSEOPixel: (data: PixelRollbackRequest) => Promise<void>;
  fetchPixelStatus: (pixelId: string) => Promise<PixelResponse | null>;

  // --------------------------
  // Task orchestration
  // --------------------------
  checkOrchestrationStatus: (
    taskId: string
  ) => Promise<OrchestrationStatus | null>;
  cancelOrchestrationTask: (taskId: string) => Promise<void>;

  // --------------------------
  // Publishing / Analysis status
  // --------------------------
  checkPublishingStatus: (
    articleId: string
  ) => Promise<"pending" | "done" | "failed" | null>;
  checkAnalysisStatus: (
    auditId: string
  ) => Promise<"pending" | "done" | "failed" | null>;
}



// ----------------------------
// Supabase types
// ----------------------------
export interface SupabaseContextType {
  supabase: any; // replace `any` with Database if you have DB types
  session: Session | null;
  isLoading: boolean;
  error: string | null;
}

export interface SupabaseProviderProps {
  children: React.ReactNode;
}

// ----------------------------
// User types
// ----------------------------


// ----------------------------
// Subscription types
// ----------------------------

export interface SubscriptionContextValue {
  subscription: Subscription | null;
  loading: boolean;
  refreshSubscription: () => Promise<void>;
}

export interface SubscriptionProviderProps {
  children: React.ReactNode;
}

/** Media item (images, videos, files) */
export interface Media {
  id: UUID;
  filename: string;
  url: string;
  mimeType?: string;
  size?: number; // bytes
  width?: number;
  height?: number;
  createdAt?: string; // ISO timestamp
  updatedAt?: string; // ISO timestamp
  metadata?: JSONObject;
}

/** Field value - supports common CMS primitive types */
export type FieldValue = string | number | boolean | null | string[] | JSONObject;

/** ContentField - single field in a content item schema */
export interface ContentField {
  name: string;
  label?: string;
  type: 'text' | 'richtext' | 'number' | 'boolean' | 'date' | 'media' | 'json' | 'reference';
  required?: boolean;
  multiple?: boolean;
  referenceTo?: string; // collection name or id for references
  widget?: string; // UI hints (e.g., 'textarea', 'dropdown')
  options?: JSONObject;
}

/** Collection / Content Type definition */
export interface CollectionSchema {
  id: UUID;
  name: string; // machine name
  displayName?: string; // human name
  description?: string;
  fields: ContentField[];
  createdAt?: string;
  updatedAt?: string;
}

/** Content item stored in a collection (e.g., blog post) */
export interface ContentItem {
  id: UUID;
  collectionId: UUID;
  slug?: string;
  title?: string;
  published?: boolean;
  publishedAt?: string;
  createdAt?: string;
  updatedAt?: string;
  authorId?: UUID;
  data: Record<string, FieldValue>;
  media?: Media[];
  metadata?: JSONObject;
}

/** BlogPost - specific content item for articles */
export interface BlogPost {
  id: string;
  title: string;
  status: 'pending' | 'researching' | 'writing' | 'enhancing' | 'ready' | 'published' | 'scheduled';
  content: string;
  wordCount: number;
  scheduledDate?: Date;
  publishedDate?: Date;
  links?: { min: number; max: number };
  source?: string;
  ready?: boolean;
  impressions?: number;
  clicks?: number;
  trend?: number;
}





/** User preferences */
export interface UserSettings {
  language: string;
  tone: string;
  writingStyle: string;
  defaultWordCount: number;
  preferredCms?: string;
  autoPublish: boolean;
  seoFocus: 'high' | 'medium' | 'low';
  factChecking: boolean;
  notifications: {
    email: boolean;
    push: boolean;
    desktop: boolean;
    autopilot?: boolean;
  };
}


/** User - minimal frontend-facing user data */
export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  createdAt: string;
  updatedAt?: string;
  subscriptionId?: string;
}

export interface Subscription {
  id: string;
  userId?: string;
  plan: 'starter' | 'beginner' | 'pro' | 'ultimate' | 'enterprise' | 'extra' | 'mega' | string;
  status: 'active' | 'canceled' | 'past_due' | 'trialing' | string;
  credits?: number;
  articlesThisMonth?: number;
  articlesTotal?: number;
  impressions?: number;
  clicks?: number;
  current_period_end?: string;
  renewsAt?: string;
  createdAt?: string;
  updatedAt?: string;
  [key: string]: unknown;
}

export interface UserStats {
  credits: number;
  articlesThisMonth: number;
  articlesTotal: number;
  impressions: number;
  clicks: number;
  tasks: number;
  clusters: number;
}

export interface Website {
  id: string;
  domain: string;
  created_at: string;
  seo_pixel_id?: string; // optional if not always present
}


export interface UserStoreState {
  user: User | null;
  subscription: Subscription | null;
  settings: UserSettings | null;
  websites: Website[];
  loading: boolean;
  error: string | null;

  // Main fetch
  fetchUserData: (forceRefresh?: boolean) => Promise<{
    user: User | null;
    subscription: Subscription | null;
    settings: UserSettings | null;
    websites: Website[];
  } | null>;

  // Lazy-load
  fetchBlogResults: (taskId: string) => Promise<any[]>;
  fetchAIRecommendations: (websiteId: string) => Promise<any[]>;
  fetchPageSEOData: (websiteId: string) => Promise<any[]>;
  fetchTasks: (websiteId: string) => Promise<{ blog_tasks: any[]; seo_tasks: any[] }>;
  getGeneratedArticle: (taskId: string) => Promise<any | null>;

  // Update / clear
  updateUserProfile: (data: Partial<User> & { user_settings?: Partial<UserSettings> }) => Promise<User | null>;
  clearStore: () => void;
    fetchWebsiteBlogPosts?: (websiteId: string) => Promise<BlogPost[]>;


  // ✅ Optional ContentQueue actions
  approvePost?: (postId: string) => Promise<void>;
  declinePost?: (postId: string) => Promise<void>;
  schedulePost?: (postId: string, date: Date) => Promise<void>;
}





/** Create content request */
export interface CreateContentRequest {
  collectionId: UUID;
  data: Record<string, FieldValue>;
  slug?: string;
  title?: string;
  publish?: boolean;
  authorId?: UUID;
}

/** Update content request */
export interface UpdateContentRequest {
  id: UUID;
  data?: Partial<Record<string, FieldValue>>;
  title?: string;
  slug?: string;
  publish?: boolean;
  revision?: number;
}

/** Query/filter options for content */
export interface ContentQueryOptions {
  collectionId?: UUID;
  slug?: string;
  q?: string; // search query
  filters?: Record<string, unknown>;
  sort?: string; // e.g., "publishedAt.desc"
  page?: number;
  pageSize?: number;
}

/** Paginated response for content queries */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

/** Canonical API error */
export interface ApiError {
  message: string;
  code?: string | number;
  details?: JSONObject;
  provider?: string; // e.g., 'lemonsqueezy', 'supabase'
}

export type ApiMethod = "GET" | "POST" | "PUT" | "DELETE";


/** API response wrapper */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  meta?: JSONObject;
}


/** SEO Blueprint for article optimization */
export interface SEOBlueprint {
  id: UUID;
  keyword: string;
  headings: string[];
  lsiTerms: string[];
  recommendedLength: number;
  questions: string[]; // People Also Ask
  sentiment: 'positive' | 'neutral' | 'negative';
  createdAt: string;
}

/** SEO Audit result */
export interface SEOAudit {
  id: UUID;
  websiteUrl: string;
  score: number;
  issues: {
    metaTags?: string[];
    brokenLinks?: string[];
    pageSpeed?: number;
    imageOptimization?: string[];
  };
  createdAt: string;
}

/** Keyword research result */
export interface KeywordResearch {
  id: UUID;
  keyword: string;
  volume: number;
  difficulty: number;
  relatedKeywords: string[];
  clusters: string[][];
  createdAt: string;
}

export interface QueueMetrics {
  links: number;
  source: string;
  ready: boolean;
  impressions: number;
  clicks: number;
  published: boolean;
  trend: number;
}

/** Settings data for user configuration */
export interface SettingsData {
  general: {
    name: string;
    type: string;
    summary: string;
    blogTheme: string;
    founders: string;
    features: string;
    pricing: string;
  };
  targetAudience: {
    country: string;
    language: string;
    summary: string;
    painPoints: string;
    usage: string;
  };
  competitors: {
    urls: string[];
    analysis: string;
  };
  images: {
    style: 'photorealistic' | 'illustrated' | 'minimal';
    source: 'google' | 'unsplash' | 'custom';
  };
  cta: {
    text: string;
    url: string;
    style: 'button' | 'link' | 'banner';
  };
  prompts: {
    customPrompts: string[];
    tone: 'formal' | 'casual' | 'technical';
  };
  backlinks: {
    targetSites: string[];
    strategy: string;
  };
  news: {
    sources: string[];
    frequency: 'daily' | 'weekly';
  };
  videos: {
    embedSources: string[];
    autoEmbed: boolean;
  };
  advanced: {
    apiKey?: string;
    customDomains: string[];
    factChecking: boolean;
  };
}



/** Toast notification for UI feedback */
export interface ToastNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

/** Modal component props */
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  children: React.ReactNode;
}

/** Pagination controls */
export interface PaginationControls {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
  onItemsPerPageChange?: (itemsPerPage: number) => void;
}

/** Form field configuration */
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'textarea' | 'select' | 'checkbox';
  required?: boolean;
  placeholder?: string;
  options?: SelectOption[];
  validation?: {
    pattern?: RegExp;
    minLength?: number;
    maxLength?: number;
    custom?: (value: any) => string | null;
  };
}

/** Select option for form fields */
export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

/** Form state */
export interface FormState<T = any> {
  values: T;
  errors: Partial<Record<keyof T, string>>;
  touched: Partial<Record<keyof T, boolean>>;
  isSubmitting: boolean;
  isValid: boolean;
}
   

/** Conversation context */
export interface ConversationContext {
  currentTopic?: string;
  targetKeyword?: string;
  articleStyle?: string;
  wordCount?: number;
  websiteUrl?: string;
  userInfo?: Record<string, any>; // optional
  previousMessages: string[];
}


/** Dashboard statistics */
export interface DashboardStats {
  totalArticles: number;
  articlesThisMonth: number;
  totalWords: number;
  averageSeoScore: number;
  cmsConnections: number;
  upcomingTasks: number;
}

/** Activity feed item */
export interface ActivityFeedItem {
  id: string;
  type: 'article_created' | 'article_published' | 'seo_audit' | 'cms_connected' | 'task_completed';
  title: string;
  description: string;
  timestamp: Date;
  metadata?: {
    articleId?: string;
    cmsType?: string;
    score?: number;
  };
}

// ---------------------------
// Core Task Types
// ---------------------------

/** Message stored in conversation */
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string; // ISO string
  type?: "text" | "suggestion" | "error" | "success";
  metadata?: {
    articleId?: string;
    taskId?: string;
    progress?: number;
  };
}


// ---------------------------
// Agent Subtasks
// ---------------------------
export type AgentStatus = TaskStatus;

export interface AgentSubtask {
  id: string;
  taskId: string;
  agentType: string; // e.g. "seo_keyword", "blog_writer"
  status: AgentStatus;
  attempt: number;
  errorMessage?: string | null;
  parameters?: Record<string, any>; // JSON payload
  createdAt: string;
  updatedAt?: string;
  completedAt?: string;
}

// Define a type for backend orchestration status
export interface OrchestrationStatus {
  status: TaskStatus;
  progress: string;
  updated_at?: string;
  completed_at?: string;
    article_id?: string;

}

export type TaskStatus =
  | "pending"
  | "processing"
  | "retrying"
  | "cancelling"
  | "completed"
  | "failed"
  | "cancelled"; // ✅ exactly matches TaskService + DB schema

export interface Task {
  id: string; // Supabase gives UUID as string
  userId: string;
  websiteId?: string;
  articleId?: string; // linked blog/article
  publishingJobId?: string; // from link_job()
  taskType?: "seo" | "blog"; // ✅ helpful discriminator
  name?: string; // frontend label only
  status: TaskStatus;
  progressMessage?: string | null; // maps to DB `progress_message`
  createdAt: string; // maps to `created_at`
  updatedAt?: string; // maps to `updated_at`
  completedAt?: string; // maps to `completed_at`
  error?: string | null;
}


/** Task log entry */
export interface TaskLog {
  timestamp: string; // ISO string
  message: string;
}

// ---------------------------
// State + Actions
// ---------------------------
export interface TaskState {
  tasks: Task[];
  currentTask: Task | null;
  subtasks: AgentSubtask[];
  isLoading: boolean;
  error: string | null;
}

export interface TaskActions {
  fetchTasks: (userId: string) => Promise<void>;
  fetchTaskById: (taskId: string) => Promise<void>;
  fetchSubtasks: (taskId: string) => Promise<void>;
  updateTaskStatus: (
    taskId: string,
    status: TaskStatus,
    result?: any
  ) => Promise<void>;
  createTask: (taskData: Partial<Task>) => Promise<void>;
  retryTask: (taskId: string) => Promise<void>;
  retrySubtask: (taskId: string, agentType: string) => Promise<void>;
  cancelTask: (taskId: string) => Promise<void>;
  clearError: () => void;
  initRealtimeSubscriptions: (userId: string) => () => void;
}




/** Collaboration session */
export interface CollaborationSession {
  id: string;
  articleId: string;
  participants: CollaborationParticipant[];
  changes: CollaborationChange[];
  createdAt: Date;
  updatedAt: Date;
}

/** Collaboration participant */
export interface CollaborationParticipant {
  userId: string;
  name: string;
  avatar?: string;
  role: 'owner' | 'editor' | 'viewer';
  lastActive: Date;
}

/** Collaboration change */
export interface CollaborationChange {
  id: string;
  userId: string;
  type: 'content' | 'title' | 'metadata';
  changes: any;
  timestamp: Date;
  version: number;
}


/** App configuration */
export interface AppConfig {
  version: string;
  environment: 'development' | 'staging' | 'production';
  supabaseUrl: string;
  supabaseAnonKey: string;
  apiBaseUrl: string;
}

/** Feature flags */
export interface FeatureFlags {
  aiContentGeneration: boolean;
  seoAudit: boolean;
  cmsIntegration: boolean;
  realTimeCollaboration: boolean;
  advancedAnalytics: boolean;
  multiLanguageSupport: boolean;
}


/** App event map */
export interface AppEventMap {
  'user:logged_in': { user: User };
  'user:logged_out': undefined;
  'article:created': { article: BlogPost };
  'article:published': { article: BlogPost; cmsType: string };
  'seo:audit_completed': { audit: SEOAudit };
  'cms:connected': { integration: CMSIntegration };
  'task:completed': { task: Task };
  'task:failed': { task: Task; error: string };
  'conversation:message_added': { message: Message };
  'conversation:agent_changed': { agent: string };
  'notification:show': { notification: ToastNotification };
  'modal:open': { modal: string; props?: any };
  'modal:close': { modal: string };
}

export type AppEvent = {
  [K in keyof AppEventMap]: { type: K; data: AppEventMap[K] };
}[keyof AppEventMap];


/** Theme configuration */
export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    error: string;
    warning: string;
    success: string;
    info: string;
    text: {
      primary: string;
      secondary: string;
      disabled: string;
    };
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
}

export type ColorMode = 'dark'; // MangoSEO uses dark theme only


/** Error boundary state */
export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

/** Error boundary props */
export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}


/** Performance metrics */
export interface PerformanceMetrics {
  pageLoadTime: number;
  apiResponseTime: number;
  renderTime: number;
  memoryUsage: number;
  networkRequests: number;
  errors: number;
}

/** Performance entry */
export interface PerformanceEntry {
  name: string;
  entryType: string;
  startTime: number;
  duration: number;
  metadata?: any;
}


/** Locale configuration */
export interface Locale {
  code: string;
  name: string;
  flag: string;
  direction: 'ltr' | 'rtl';
}

/** Translation resources */
export interface TranslationResources {
  [namespace: string]: {
    [key: string]: string;
  };
}

/** i18n configuration */
export interface I18nConfig {
  defaultLocale: string;
  locales: Locale[];
  namespaces: string[];
  loadPath: string;
}



export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';

export interface Responsive<T> {
  xs?: T;
  sm?: T;
  md?: T;
  lg?: T;
  xl?: T;
  '2xl'?: T;
}

/** Viewport size */
export interface ViewportSize {
  width: number;
  height: number;
  breakpoint: Breakpoint;
  orientation: 'portrait' | 'landscape';
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
}


/** Animation props for Framer Motion */
export interface AnimationProps {
  initial?: any;
  animate?: any;
  exit?: any;
  transition?: {
    duration?: number;
    ease?: string;
    delay?: number;
    type?: 'spring' | 'tween' | 'inertia';
    stiffness?: number;
    damping?: number;
    mass?: number;
  };
  variants?: {
    [key: string]: any;
  };
}

export type AnimationPreset = 'fade' | 'slide' | 'scale' | 'bounce' | 'none';



// frontend/types/cms.ts
export type CMSType =
  | 'wordpress'
  | 'webflow'
  | 'shopify'
  | 'hubspot'
  | 'notion'
  | 'wix'
  | 'ghost'
  | 'framer'
  | 'medium'
  | 'blogger'
  | 'substack'
  | 'bitsandbytes';

export interface CMSIntegration {
  id: UUID;
  userId?: UUID;
  type: CMSType;
  name?: string;
  connected?: boolean;
  credentials?: Record<string, unknown>;
  apiKey?: string;
  endpoint?: string;
  status?: 'connected' | 'disconnected' | 'error';
  createdAt?: string;
  updatedAt?: string;
  lastSyncedAt?: string;
}


export interface CMSDeployment {
  id: string;
  integrationId: string;
  articleId: string;
  status: 'pending' | 'processing' | 'success' | 'failed' | 'partial_failed';
  scheduledAt?: string;
  createdAt: string;
  taskId?: string;       // ✅ store backend taskId
  errorMessage?: string; // optional error messages from backend
}

export interface CMSStore {
  // State
  integrations: CMSIntegration[];
  deployments: CMSDeployment[];
  selectedIntegration: CMSIntegration | null;
  isLoading: boolean;                // general loading
  isLoadingIntegrations: boolean;    // ✅ track loading integrations
  isDeploying: boolean;              // ✅ track article deployment
  isSyncing: boolean;                // ✅ track syncing status
  error: string | null;
  isConnected: boolean;
  syncStatus: 'idle' | 'syncing' | 'success' | 'error';

  // Actions
    loadIntegrations: (userId: string) => Promise<void>;  // ✅ updated to accept userId
  connectCMS: (cmsType: CMSType, credentials: Record<string, unknown>) => Promise<void>;
  disconnectCMS: (integrationId: string) => Promise<void>;
  updateIntegration: (integrationId: string, updates: Partial<CMSIntegration>) => Promise<void>;
  deployArticle: (articleId: string, integrationId: string, scheduleDate?: Date) => Promise<void>;
  getDeploymentStatus: (deploymentId: string) => Promise<void>;
  syncContent: (integrationId: string) => Promise<void>;
  selectIntegration: (integration: CMSIntegration | null) => void;
  clearError: () => void;
  reset: () => void;
}




/** CMS preview for articles */
export interface CMSPreview {
  title: string;
  content: string;
  excerpt: string;
  featuredImage?: string;
  slug: string;
  metaDescription: string;
  tags: string[];
  categories: string[];
  status: 'draft' | 'scheduled' | 'published';
  author: string;
  publishedAt?: Date;
  updatedAt: Date;
}

/** CMS field mapping */
export interface CMSFieldMapping {
  title: string;
  content: string;
  excerpt: string;
  featuredImage: string;
  slug: string;
  metaDescription: string;
  tags: string;
  categories: string;
  status: string;
  author: string;
  publishedAt: string;
}

/** Pipeline run request for backend */
export interface CmsPipelineRunRequest {
  contentId: UUID;
  collectionId: UUID;
  trigger: 'manual' | 'scheduled' | 'webhook';
  input?: Record<string, unknown>;
  runAsUserId?: UUID;
  stream?: boolean;
  traceId?: string;
}

/** Pipeline run result */
export interface CmsPipelineRunResult {
  runId: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  startedAt?: string;
  finishedAt?: string;
  output?: Record<string, unknown>;
  error?: ApiError;
}

