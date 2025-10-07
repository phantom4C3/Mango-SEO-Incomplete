
// frontend/src/stores/use-conversation-store.ts
import { create } from "zustand";
import type { Message, ConversationState, TopicRequest, SEOAnalysisRequest, BatchAnalysisRequest, PixelGenerationRequest, PixelRollbackRequest, PixelResponse } from "../lib/types";
import {
  analyzeWebsite,
  batchAnalyzeWebsite,
  generateTopics,
  orchestrateWebsite,
  publishArticle,
  generateSEOPixel,
  rollbackSEOPixel,
  getSEOPixelStatus,
  getOrchestrationStatus,
  getPublishingStatus,
  cancelOrchestration,
  getAnalysisStatus
} from "../lib/api";

export const useConversationStore = create<ConversationState>((set, get) => ({
  answers: {},
  taskLogs: {}, // Optimistic logs for UI
  messages: [],
  isLoading: false,
  suggestedResponses: [],
  context: { previousMessages: [] },

  // Answer handling
  submitAnswer: (promptId: string, answer: "yes" | "no") => {
    set((state) => ({ answers: { ...state.answers, [promptId]: answer } }));
  },

  // --------------------------
  // Website orchestration
  // --------------------------
 submitWebsite: async (websiteUrl: string) => {
  set({ isLoading: true });

try {
  const payload = {
    website_url: websiteUrl,
    target_language: "en",
    generate_article: true,
    run_seo_audit: true,
    sync_to_cms: false,
  };

  const { success, data, error } = await orchestrateWebsite(payload);
  if (!success || !data?.task_id) throw new Error(error?.message || "Orchestration failed");

  // Map task_id to a single starting log
  set((state) => ({
    taskLogs: {
      ...state.taskLogs,
      [data.task_id]: [{ timestamp: new Date().toISOString(), message: "Orchestration started..." }],
    },
  }));

} catch (err: unknown) {
  const message = err instanceof Error ? err.message : String(err);
  set((state) => ({
    taskLogs: {
      ...get().taskLogs,
      temp_error: [{ timestamp: new Date().toISOString(), message: `Error: ${message}` }],
    },
  }));
} finally {
  set({ isLoading: false });
}


  try {
    const payload = {
      website_url: websiteUrl,
      target_language: "en",
      generate_article: true,
      run_seo_audit: true,
      sync_to_cms: false,
    };

    // --- Debug: log payload being sent to orchestrateWebsite ---
    console.log("[DEBUG] orchestrateWebsite payload:", payload);

    const { success, data, error } = await orchestrateWebsite(payload);

    // --- Debug: log response from orchestrateWebsite ---
    console.log("[DEBUG] orchestrateWebsite response:", { success, data, error });

    if (!success || !data?.task_id) throw new Error(error?.message || "Orchestration failed");

    // Map temp logs to real task_id
    set((state) => ({
      taskLogs: {
        ...state.taskLogs,
        [data.task_id]: state.taskLogs[tempId],
      },
    }));

    // --- Debug: log successful mapping of task_id ---
    console.log("[DEBUG] Task mapped to real task_id:", data.task_id);

  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);

    // --- Debug: log any error caught ---
    console.error("[DEBUG] submitWebsite error:", message);

    set((state) => ({
      taskLogs: {
        ...state.taskLogs,
        [tempId]: [...(state.taskLogs[tempId] || []), { timestamp: new Date().toISOString(), message: `Error: ${message}` }],
      },
    }));
  } finally {
    set({ isLoading: false });

    // --- Debug: indicate submission flow finished ---
    console.log("[DEBUG] submitWebsite flow completed for tempId:", tempId);
  }
},


  // --------------------------
  // SEO analysis
  // --------------------------
 runSEOAnalysis: async (data: SEOAnalysisRequest) => {
  console.log("🏁 runSEOAnalysis called with:", data); // ✅ log input
  set({ isLoading: true });

  try {
    const { success, data: resp, error } = await analyzeWebsite(data);
    console.log("🔹 API response:", resp, error); // ✅ log API response

    if (!success || !resp?.task_id) {
      throw new Error(error?.message || "SEO analysis failed");
    }

    set((state) => ({
      taskLogs: {
        ...state.taskLogs,
        [resp.task_id]: [
          { timestamp: new Date().toISOString(), message: "SEO analysis started..." },
        ],
      },
    }));
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("❌ runSEOAnalysis error:", message); // ✅ log errors
    set((state) => ({
      taskLogs: {
        ...state.taskLogs,
        temp_error: [
          { timestamp: new Date().toISOString(), message: `Error: ${message}` },
        ],
      },
    }));
  } finally {
    set({ isLoading: false });
  }
},



  batchSEOAnalysis: async (data: BatchAnalysisRequest) => {
    const tempId = crypto.randomUUID();
    set((state) => ({
      taskLogs: { ...state.taskLogs, [tempId]: [{ timestamp: new Date().toISOString(), message: "Starting batch SEO analysis..." }] },
      isLoading: true,
    }));

    try {
      const { success, data: resp, error } = await batchAnalyzeWebsite(data);
      if (!success || !resp?.task_id) throw new Error(error?.message || "Batch SEO analysis failed");

      set((state) => ({
        taskLogs: { ...state.taskLogs, [resp.task_id]: state.taskLogs[tempId] },
      }));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      set((state) => ({
        taskLogs: { ...state.taskLogs, [tempId]: [...(state.taskLogs[tempId] || []), { timestamp: new Date().toISOString(), message: `Error: ${message}` }] },
      }));
    } finally {
      set({ isLoading: false });
    }
  },

  // --------------------------
  // Topic generation
  // --------------------------
  generateTopics: async (data: TopicRequest) => {
    const tempId = crypto.randomUUID();
    set((state) => ({
      taskLogs: { ...state.taskLogs, [tempId]: [{ timestamp: new Date().toISOString(), message: "Generating topics..." }] },
      isLoading: true,
    }));

    try {
      const { success, data: resp, error } = await generateTopics(data);
      if (!success || !resp?.task_id) throw new Error(error?.message || "Topic generation failed");

      set((state) => ({
        taskLogs: { ...state.taskLogs, [resp.task_id]: state.taskLogs[tempId] },
      }));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      set((state) => ({
        taskLogs: { ...state.taskLogs, [tempId]: [...(state.taskLogs[tempId] || []), { timestamp: new Date().toISOString(), message: `Error: ${message}` }] },
      }));
    } finally {
      set({ isLoading: false });
    }
  },

  // --------------------------
  // Publishing
  // --------------------------
  // keep article id as we will replce it with taskid form backend 
  publishArticle: async (articleId: string) => {
    const tempId = crypto.randomUUID();
    set((state) => ({
      taskLogs: { ...state.taskLogs, [tempId]: [{ timestamp: new Date().toISOString(), message: "Publishing article..." }] },
      isLoading: true,
    }));

    try {
      const { success, error } = await publishArticle(articleId);
      if (!success) throw new Error(error?.message || "Publishing failed");

      set((state) => ({
        taskLogs: { ...state.taskLogs, [articleId]: state.taskLogs[tempId] },
      }));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      set((state) => ({
        taskLogs: { ...state.taskLogs, [tempId]: [...(state.taskLogs[tempId] || []), { timestamp: new Date().toISOString(), message: `Error: ${message}` }] },
      }));
    } finally {
      set({ isLoading: false });
    }
  },

  // --------------------------
  // Pixel generation / rollback
  // --------------------------
  generateSEOPixel: async (data: PixelGenerationRequest) => {
    const tempId = crypto.randomUUID();
    set((state) => ({
      taskLogs: { ...state.taskLogs, [tempId]: [{ timestamp: new Date().toISOString(), message: "Generating SEO Pixel..." }] },
      isLoading: true,
    }));

    try {
      const { success, data: resp, error } = await generateSEOPixel(data);
      if (!success || !resp?.pixel_id) throw new Error(error?.message || "Pixel generation failed");

      set((state) => ({
        taskLogs: { ...state.taskLogs, [resp.pixel_id]: state.taskLogs[tempId] },
      }));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      set((state) => ({
        taskLogs: { ...state.taskLogs, [tempId]: [...(state.taskLogs[tempId] || []), { timestamp: new Date().toISOString(), message: `Error: ${message}` }] },
      }));
    } finally {
      set({ isLoading: false });
    }
  },
  fetchPixelStatus: async (pixelId: string) => {
  try {
    const { success, data, error } = await getSEOPixelStatus(pixelId);
    if (!success || !data) throw new Error(error?.message || "Failed to fetch pixel status");
    return data as PixelResponse;  // Or update state if you want logs
  } catch (err) {
    console.error("Error fetching pixel status", err);
    return null;
  }
},

  rollbackSEOPixel: async (data: PixelRollbackRequest) => {
    const tempId = crypto.randomUUID();
    set((state) => ({
      taskLogs: { ...state.taskLogs, [tempId]: [{ timestamp: new Date().toISOString(), message: "Rolling back SEO Pixel..." }] },
      isLoading: true,
    }));

    try {
      const { success, data: resp, error } = await rollbackSEOPixel(data);
      if (!success || !resp?.pixel_id) throw new Error(error?.message || "Pixel rollback failed");

      set((state) => ({
        taskLogs: { ...state.taskLogs, [resp.pixel_id]: state.taskLogs[tempId] },
      }));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      set((state) => ({
        taskLogs: { ...state.taskLogs, [tempId]: [...(state.taskLogs[tempId] || []), { timestamp: new Date().toISOString(), message: `Error: ${message}` }] },
      }));
    } finally {
      set({ isLoading: false });
    }
  },

checkOrchestrationStatus: async (taskId: string) => {
  set({ isLoading: true });
  try {
    const { success, data, error } = await getOrchestrationStatus(taskId);
    if (!success || !data) throw new Error(error?.message || "Failed to fetch orchestration status");

    // Optionally update task logs with current status
    set((state) => ({
      taskLogs: {
        ...state.taskLogs,
        [taskId]: [
          ...(state.taskLogs[taskId] || []),
          { timestamp: new Date().toISOString(), message: `Orchestration status: ${data.status}` }
        ],
      },
    }));

    return data; // can return full orchestration status
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("Orchestration status error", message);
    return null;
  } finally {
    set({ isLoading: false });
  }
},

  checkPublishingStatus: async (articleId: string) => {
  set({ isLoading: true });
  try {
    const { success, data, error } = await getPublishingStatus(articleId);
    if (!success || !data) throw new Error(error?.message || "Failed to fetch publishing status");

    // Update task logs
    set((state) => ({
      taskLogs: {
        ...state.taskLogs,
        [articleId]: [
          ...(state.taskLogs[articleId] || []),
          { timestamp: new Date().toISOString(), message: `Publishing status: ${data.status}` },
        ],
      },
    }));

    return data;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("Publishing status error", message);
    return null;
  } finally {
    set({ isLoading: false });
  }
},
cancelOrchestrationTask: async (taskId: string) => {
  const tempId = crypto.randomUUID();
  set((state) => ({
    taskLogs: {
      ...state.taskLogs,
      [tempId]: [{ timestamp: new Date().toISOString(), message: "Cancelling orchestration..." }],
    },
    isLoading: true,
  }));

  try {
    const { success, error } = await cancelOrchestration(taskId);
    if (!success) throw new Error(error?.message || "Cancellation failed");

    // Optionally mark in logs that orchestration was cancelled
    set((state) => ({
      taskLogs: {
        ...state.taskLogs,
        [taskId]: [
          ...(state.taskLogs[taskId] || []),
          { timestamp: new Date().toISOString(), message: "Orchestration cancelled." },
        ],
      },
    }));
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    set((state) => ({
      taskLogs: {
        ...state.taskLogs,
        [tempId]: [...(state.taskLogs[tempId] || []), { timestamp: new Date().toISOString(), message: `Error: ${message}` }],
      },
    }));
  } finally {
    set({ isLoading: false });
  }
},
checkAnalysisStatus: async (taskId: string) => {
  set({ isLoading: true });
  try {
    const { success, data, error } = await getAnalysisStatus(taskId);

    if (!success || !data) throw new Error(error?.message || "Failed to fetch analysis status");

    set((state) => ({
      taskLogs: {
        ...state.taskLogs,
        [taskId]: [
          ...(state.taskLogs[taskId] || []),
          { timestamp: new Date().toISOString(), message: `Analysis status: ${data.status}` },
        ],
      },
    }));

    return data;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("Analysis status error", message);
    return null;
  } finally {
    set({ isLoading: false });
  }
},


}));
// --------------------------
// Selectors / Hooks
// --------------------------
export const useConversationMessages = () =>
  useConversationStore((state) => state.messages);
export const useConversationContext = () =>
  useConversationStore((state) => state.context);
export const useConversationIsLoading = () =>
  useConversationStore((state) => state.isLoading);
export const useConversationAnswers = () =>
  useConversationStore((state) => state.answers);
export const useConversationSuggestedResponses = () =>
  useConversationStore((state) => state.suggestedResponses);
export const useConversationLogs = () =>
  useConversationStore((state) => state.taskLogs);

// --------------------------
// Action Hooks
// --------------------------
export const useSubmitAnswer = () =>
  useConversationStore((state) => state.submitAnswer);

export const useSubmitWebsite = () =>
  useConversationStore((state) => state.submitWebsite);

export const useRunSEOAnalysis = () =>
  useConversationStore((state) => state.runSEOAnalysis);

export const useBatchSEOAnalysis = () =>
  useConversationStore((state) => state.batchSEOAnalysis);

export const useGenerateTopics = () =>
  useConversationStore((state) => state.generateTopics);

export const usePublishArticle = () =>
  useConversationStore((state) => state.publishArticle);

export const useGenerateSEOPixel = () =>
  useConversationStore((state) => state.generateSEOPixel);

export const useFetchPixelStatus = () =>
  useConversationStore((state) => state.fetchPixelStatus);

export const useRollbackSEOPixel = () =>
  useConversationStore((state) => state.rollbackSEOPixel);

export const useCheckOrchestrationStatus = () =>
  useConversationStore((state) => state.checkOrchestrationStatus);

export const useCheckPublishingStatus = () =>
  useConversationStore((state) => state.checkPublishingStatus);

export const useCancelOrchestrationTask = () =>
  useConversationStore((state) => state.cancelOrchestrationTask);

export const useCheckAnalysisStatus = () =>
  useConversationStore((state) => state.checkAnalysisStatus);
