/**
 * CMS Store - Zustand store for managing Content Management System integrations
 * Handles CMS connections, deployments, and synchronization state
 */

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type {
  CMSIntegration,
  CMSType,
  CMSDeployment,
  ApiResponse,
  CMSStore,
} from "../lib/types";
import { supabase } from "../lib/supabase-client"; // ✅ add this


export const useCMSStore = create<CMSStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      // Initial state
      integrations: [],
      deployments: [],
      selectedIntegration: null,
      isLoading: false, // general loading
      isLoadingIntegrations: false, // ✅ track loading integrations
      isDeploying: false, // ✅ track article deployment
      isSyncing: false, // ✅ track syncing status
      error: null,
      isConnected: false,
      syncStatus: "idle",


      loadIntegrations: async (userId: string) => {
  set({ isLoadingIntegrations: true, error: null });

  try {
    // Fetch integrations for this user only
    const { data, error } = await supabase
      .from("cms_integrations")
      .select("*")
      .eq("user_id", userId);

    if (error) throw error;

    set({ integrations: data || [] });

    // Subscribe only to this user’s integrations
    const subscription = supabase
      .channel(`cms_integrations_${userId}`)
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "cms_integrations",
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          console.log("Realtime update received:", payload);

          set((state) => {
            const updated = [...state.integrations];

            if (payload.eventType === "INSERT" && payload.new) {
              updated.push(payload.new);
            }
            if (payload.eventType === "UPDATE" && payload.new) {
              return {
                integrations: updated.map((i) =>
                  i.id === payload.new.id ? payload.new : i
                ),
              };
            }
            if (payload.eventType === "DELETE" && payload.old) {
              return {
                integrations: updated.filter(
                  (i) => i.id !== payload.old.id
                ),
              };
            }
            return { integrations: updated };
          });
        }
      )
      .subscribe();
  } catch (err) {
    console.error("Failed to load/subscribe to CMS integrations:", err);
    set({ error: "Failed to load CMS integrations" });
  } finally {
    set({ isLoadingIntegrations: false });
  }
},



 unsubscribeAll: () => {
        try {
          supabase.removeAllChannels();
          console.log("Unsubscribed from all Supabase channels");
        } catch (err) {
          console.error("Failed to unsubscribe:", err);
        }
      },

      // Connect a new CMS integration
      connectCMS: async (
        cmsType: CMSType,
        credentials: Record<string, unknown>
      ) => {
        set({ isLoading: true, error: null });

        try {
          const response: ApiResponse<CMSIntegration> = await apiClient.post(
            "/cms/connect",
            {
              cmsType,
              credentials,
            }
          );

          if (response.success && response.data) {
            set((state) => ({
              integrations: [...state.integrations, response.data!],
              isLoading: false,
              isConnected: true,
              selectedIntegration: response.data!,
            }));
          } else {
            set({
              error: response.error?.message || "Failed to connect CMS",
              isLoading: false,
            });
          }
        } catch (error) {
          set({
            error:
              error instanceof Error ? error.message : "Failed to connect CMS",
            isLoading: false,
          });
        }
      },

      // Disconnect a CMS integration
      disconnectCMS: async (integrationId: string) => {
        set({ isLoading: true, error: null });

        try {
          const response: ApiResponse<{ success: boolean }> =
            await apiClient.delete(`/cms/integrations/${integrationId}`);

          if (response.success) {
            set((state) => ({
              integrations: state.integrations.filter(
                (integration) => integration.id !== integrationId
              ),
              selectedIntegration:
                state.selectedIntegration?.id === integrationId
                  ? null
                  : state.selectedIntegration,
              isLoading: false,
              isConnected: state.integrations.some(
                (integration) =>
                  integration.id !== integrationId &&
                  integration.status === "connected"
              ),
            }));
          } else {
            set({
              error: response.error?.message || "Failed to disconnect CMS",
              isLoading: false,
            });
          }
        } catch (error) {
          set({
            error:
              error instanceof Error
                ? error.message
                : "Failed to disconnect CMS",
            isLoading: false,
          });
        }
      },

      // Update CMS integration settings
      updateIntegration: async (
        integrationId: string,
        updates: Partial<CMSIntegration>
      ) => {
        set({ isLoading: true, error: null });

        try {
          const response: ApiResponse<CMSIntegration> = await apiClient.put(
            `/cms/integrations/${integrationId}`,
            updates
          );

          if (response.success && response.data) {
            set((state) => ({
              integrations: state.integrations.map((integration) =>
                integration.id === integrationId ? response.data! : integration
              ),
              selectedIntegration:
                state.selectedIntegration?.id === integrationId
                  ? response.data!
                  : state.selectedIntegration,
              isLoading: false,
            }));
          } else {
            set({
              error:
                response.error?.message || "Failed to update CMS integration",
              isLoading: false,
            });
          }
        } catch (error) {
          set({
            error:
              error instanceof Error
                ? error.message
                : "Failed to update CMS integration",
            isLoading: false,
          });
        }
      },

      // Deploy an article to a CMS
      deployArticle: async (
        articleId: string,
        integrationId: string,
        scheduleDate?: Date
      ) => {
        set({ isDeploying: true, error: null });

        try {
          const payload: Record<string, unknown> = {
            articleId,
            integrationId,
          };

          if (scheduleDate) {
            payload.scheduleDate = scheduleDate.toISOString();
          }

          const response = await deployArticleToCMS(articleId, integrationId, scheduleDate);


          if (response.success && response.data) {
            set((state) => ({
              deployments: [...state.deployments, response.data!],
              isLoading: false,
            }));

            // Start polling for deployment status
get().subscribeToDeployment(response.data!.id);
          } else {
            set({
              error: response.error?.message || "Failed to deploy article",
              isLoading: false,
            });
          }
        } catch (error) {
          set({
            error:
              error instanceof Error
                ? error.message
                : "Failed to deploy article",
            isLoading: false,
          });
        }
      }, 

      // Sync content between MangoSEO and CMS
     syncContent: async (integrationId: string, userId: string) => {
  set({ isSyncing: true, syncStatus: "syncing", error: null });

  try {
    const response = await syncCMSContent(integrationId);

    if (response.success) {
      set({ syncStatus: "success" });

      // Reload integrations scoped to this user
      setTimeout(() => {
        get().loadIntegrations(userId);
        set({ syncStatus: "idle" });
      }, 2000);
    } else {
      set({
        error: response.error?.message || "Failed to sync content",
        syncStatus: "error",
      });
    }
  } catch (error) {
    set({
      error: error instanceof Error ? error.message : "Failed to sync content",
      syncStatus: "error",
    });
  }
},
subscribeToDeployment: (deploymentId: string) => {
  const channel = supabase
    .channel(`cms_deployment_${deploymentId}`)
    .on(
      "postgres_changes",
      {
        event: "*",
        schema: "public",
        table: "cms_deployments",
        filter: `id=eq.${deploymentId}`,
      },
      (payload: any) => {
        set((state) => ({
          deployments: state.deployments.map((d) =>
            d.id === deploymentId ? payload.new : d
          ),
        }));
      }
    )
    .subscribe();

  // Optional: store the channel if you want to unsubscribe later
  set((state) => ({
    context: { ...state.context, [`channel_deployment_${deploymentId}`]: channel },
  }));
},


      // Select a CMS integration
      selectIntegration: (integration: CMSIntegration | null) => {
        set({ selectedIntegration: integration });
      },

      // Clear error message
      clearError: () => {
        set({ error: null });
      },

      // Reset store to initial state
      reset: () => {
        set({
          integrations: [],
          deployments: [],
          selectedIntegration: null,
          isLoading: false,
          error: null,
          isConnected: false,
          syncStatus: "idle",
        });
      },
    }),
    {
      name: "cms-store",
      enabled: process.env.NODE_ENV !== "production",
    }
  )
);

// Export hooks for easier usage
export const useCMSIntegrations = () =>
  useCMSStore((state) => state.integrations);
export const useSelectedCMS = () =>
  useCMSStore((state) => state.selectedIntegration);
export const useCMSLoading = () => useCMSStore((state) => state.isLoading);
export const useCMSError = () => useCMSStore((state) => state.error);
export const useCMSConnected = () => useCMSStore((state) => state.isConnected);
export const useCMSSyncStatus = () => useCMSStore((state) => state.syncStatus);
export const useCMSLoadingIntegrations = () =>
  useCMSStore((state) => state.isLoadingIntegrations);
export const useCMSDeploying = () => useCMSStore((state) => state.isDeploying);
export const useCMSSyncing = () => useCMSStore((state) => state.isSyncing);


