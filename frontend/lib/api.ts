// frontend/src/lib/api.ts
import {
  TopicRequest,
  SEOAnalysisRequest,
  PixelGenerationRequest,
  PixelRollbackRequest,
  ApiResponse,
  ApiMethod,
  OrchestrationStatus,
  BatchAnalysisRequest,
  BatchAnalysisResponse,
  OrchestrateWebsiteResponse,
  GenerateTopicsResponse,
  PixelResponse,
  CancelOrchestrationResponse,
  PublishArticleResponse,
  TaskStatusResponse,
  SEOAnalysisResponse,
  SEOAnalysisStatus,
} from "../lib/types";

import { supabase } from "./supabase-client";
import { CLIENT_CONFIG } from "../lib/client_config";

// ✅ Normalize URLs: if relative, prefix with backend_api_url
function buildUrl(url: string) {
  if (url.startsWith("http")) return url;
  return `${CLIENT_CONFIG.backend_api_url}${url}`;
}

// use  isUUID(v: unknown): v is UUID from validators file if feasible
// frontend/src/lib/api.ts - UPDATE THE REQUEST FUNCTION
async function request<T>(
  url: string,
  method: ApiMethod = "GET",
  body?: any
): Promise<ApiResponse<T>> {
  try {
    let token: string | undefined;

    if (process.env.NODE_ENV === "development") {
      token =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." +
        "eyJzdWIiOiJkZXYtdXNlcl9pZCIsImVtYWlsIjoiZGV2QGV4YW1wbGUuY29tIiwiaWQiOiJkZXYtdXNlcl9pZCJ9." +
        "fake-signature";
    } else {
      const {
        data: { session },
        error,
      } = await supabase.auth.getSession();

      if (error) throw error;
      if (!session) throw new Error("User not authenticated");

      token = session.access_token;
    }

    const fullUrl = buildUrl(url);
    console.log(`🌐 [API] Making ${method} request to: ${fullUrl}`);
    console.log(`🌐 [API] Body:`, body);
    console.log(`🌐 [API] Token present: ${!!token}`);

    const fetchOptions: RequestInit = {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    };

    if (["POST", "PUT", "PATCH", "DELETE"].includes(method) && body) {
      fetchOptions.body = JSON.stringify(body);
    }

    const res = await fetch(fullUrl, fetchOptions);
    
    console.log(`🌐 [API] Response status: ${res.status} ${res.statusText}`);
    
    if (!res.ok) {
      const text = await res.text();
      console.log(`🌐 [API] Error response:`, text);
      return {
        success: false,
        error: { message: text || "Request failed", code: res.status },
      };
    }

    const data = (await res.json()) as T;
    console.log(`🌐 [API] Success response:`, data);
    return { success: true, data };
    
  } catch (err: any) {
    console.error(`🌐 [API] Fetch error:`, err);
    return {
      success: false,
      error: { message: err.message || "Unknown error", provider: "fetch" },
    };
  }
}

/* -------------------- Orchestration -------------------- */

export const orchestrateWebsite = (data: {
  website_url: string;
  target_language: string;
  generate_article: boolean;
  run_seo_audit: boolean;
  sync_to_cms?: boolean;
}): Promise<ApiResponse<OrchestrateWebsiteResponse>> =>
  request<OrchestrateWebsiteResponse>("/api/v1/orchestrate", "POST", data);

export const getOrchestrationStatus = (taskId: string) =>
  request<OrchestrationStatus>(
    `/api/v1/orchestration-status/${taskId}`,
    "GET"
  );

export const cancelOrchestration = (
  taskId: string
): Promise<ApiResponse<CancelOrchestrationResponse>> =>
  request<CancelOrchestrationResponse>(
    `/api/v1/cancel-orchestration/${taskId}`,
    "POST"
  );

/* -------------------- Topics -------------------- */

export const generateTopics = (
  data: TopicRequest
): Promise<ApiResponse<GenerateTopicsResponse>> =>
  request<GenerateTopicsResponse>("/api/v1/topics", "POST", data);

/* -------------------- Publishing -------------------- */

export const publishArticle = (
  articleId: string
): Promise<ApiResponse<PublishArticleResponse>> =>
  request<PublishArticleResponse>(
    `/api/v1/publish/article/${articleId}`,
    "POST"
  );

export const getPublishingStatus = (
  taskId: string
): Promise<ApiResponse<TaskStatusResponse>> =>
  request<TaskStatusResponse>(
    `/api/v1/publish/publishing-status/${taskId}`,
    "GET"
  );

/* -------------------- SEO -------------------- */

export const analyzeWebsite = (
  data: SEOAnalysisRequest
): Promise<ApiResponse<SEOAnalysisResponse>> =>
  request<SEOAnalysisResponse>("/api/v1/seo/analyze", "POST", data);

export const batchAnalyzeWebsite = (data: BatchAnalysisRequest) =>
  request<BatchAnalysisResponse>("/api/v1/seo/batch/analyze", "POST", data);

export const getAnalysisStatus = (
  taskId: string
): Promise<ApiResponse<SEOAnalysisStatus>> =>
  request<SEOAnalysisStatus>(`/api/v1/seo/analysis/${taskId}`, "GET");

/* -------------------- SEO Pixel -------------------- */

export const generateSEOPixel = (
  data: PixelGenerationRequest
): Promise<ApiResponse<PixelResponse>> =>
  request<PixelResponse>("/api/v1/seo/pixel/generate", "POST", data);

export const rollbackSEOPixel = (
  data: PixelRollbackRequest
): Promise<ApiResponse<PixelResponse>> =>
  request<PixelResponse>("/api/v1/seo/pixel/rollback", "POST", data);

export const getSEOPixelStatus = (
  pixelId: string
): Promise<ApiResponse<PixelResponse>> =>
  request<PixelResponse>(`/api/v1/seo/pixel/${pixelId}/status`, "GET");

// ✅ New: deploy endpoint
export const deploySEOPixel = (): Promise<ApiResponse<PixelResponse>> =>
  request<PixelResponse>("/api/v1/seo/pixel/deploy", "GET");

// ✅ New: raw JS pixel script
export const getSEOPixelScript = async (pixelId: string): Promise<string> => {
  const res = await fetch(
    buildUrl(`/api/v1/seo/pixel/${pixelId}.js`),
    { method: "GET" }
  );
  if (!res.ok) throw new Error(`Pixel script fetch failed: ${res.status}`);
  return res.text();
};

/* -------------------- Health Endpoints -------------------- */

export const getHealth = () => request<{ status: string }>(`/api/v1/health`, "GET");
export const getDetailedHealth = () =>
  request<Record<string, any>>(`/api/v1/health/detailed`, "GET");
export const getReadiness = () =>
  request<{ status: string }>(`/api/v1/health/readiness`, "GET");
export const getLiveness = () =>
  request<{ status: string }>(`/api/v1/health/liveness`, "GET");
export const getVersion = () =>
  request<{ version: string }>(`/api/v1/health/version`, "GET");
export const getServices = () =>
  request<{ services: string[] }>(`/api/v1/health/services`, "GET");
export const getStats = () =>
  request<Record<string, any>>(`/api/v1/health/stats`, "GET");
