import { create } from 'zustand';
import { supabase } from '../lib/supabase-client';
import { User, UserSettings, UserStoreState } from '@/lib/types';

// --------------------
// Type Definitions
// --------------------



const SESSION_KEY = 'userData';

export const useUserStore = create<UserStoreState>((set, get) => ({
  user: null,
  subscription: null,
  settings: null,
  websites: [],
  loading: false,
  error: null,

  // --------------------
  // Main fetch + cache
  // --------------------
  fetchUserData: async (forceRefresh = false) => {
    set({ loading: true, error: null });
    try {
      if (!forceRefresh) {
        const cached = sessionStorage.getItem(SESSION_KEY);
        if (cached) {
          const parsed = JSON.parse(cached);
          set({ ...parsed, loading: false });
          return parsed;
        }
      }

      const { data: { user: authUser } } = await supabase.auth.getUser();
      if (!authUser) throw new Error('No authenticated user');

      const { data, error } = await supabase
        .from('users')
        .select(`
          id, email, name, avatar, created_at, updated_at,
          subscriptions (id, status, plan, current_period_end),
          user_settings (*),
          website_configs (id, domain, created_at)
        `)
        .eq('id', authUser.id)
        .single();

      if (error) throw error;

      // Map subscription
      const subscription = Array.isArray(data?.subscriptions)
        ? data.subscriptions[0]
        : data?.subscriptions;

      // Map settings properly - fix the any[] error
      const userSettingsData = Array.isArray(data?.user_settings) 
        ? data.user_settings[0] 
        : data?.user_settings;

      const userSettings: UserSettings = {
        language: userSettingsData?.language ?? 'en',
        tone: userSettingsData?.tone ?? 'neutral',
        writingStyle: userSettingsData?.writingStyle ?? 'standard',
        defaultWordCount: userSettingsData?.defaultWordCount ?? 500,
        preferredCms: userSettingsData?.preferredCms,
        autoPublish: userSettingsData?.autoPublish ?? false,
        seoFocus: userSettingsData?.seoFocus ?? 'medium',
        factChecking: userSettingsData?.factChecking ?? false,
        notifications: {
          email: userSettingsData?.notifications?.email ?? true,
          push: userSettingsData?.notifications?.push ?? true,
          desktop: userSettingsData?.notifications?.desktop ?? true,
          autopilot: userSettingsData?.notifications?.autopilot ?? false,
        },
      };

      // Construct full userData for store
      const userData = {
        user: data ? {
          id: data.id,
          email: data.email,
          name: data.name,
          avatar: data.avatar,
          createdAt: data.created_at,
          updatedAt: data.updated_at,
          subscriptionId: subscription?.id ?? null,
        } : null,
        subscription: subscription ?? null,
        settings: userSettings,
        websites: data?.website_configs ?? [],
      };

      sessionStorage.setItem(SESSION_KEY, JSON.stringify(userData));
      set(userData);
      return userData;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch user data';
      set({ error: message });
      console.error(message);
      return null;
    } finally {
      set({ loading: false });
    }
  },

  // --------------------
  // Lazy-load heavy data
  // --------------------
  fetchBlogResults: async (taskId: string) => {
    try {
      const { data, error } = await supabase
        .from('blog_results')
        .select('*')
        .eq('task_id', taskId);
      if (error) throw error;
      return data || [];
    } catch (err) {
      console.error('Failed to fetch blog results', err);
      return [];
    }
  },

fetchAIRecommendations: async (urlId: string) => {
  try {
    const { data, error } = await supabase
      .from('ai_recommendations')
      .select('*')
      .eq('url_id', urlId);  // direct filter by URL
    if (error) throw error;
    return data || [];
  } catch (err) {
    console.error('Failed to fetch AI recommendations', err);
    return [];
  }
},

  fetchPageSEOData: async (websiteId: string) => {
    try {
      const { data, error } = await supabase
        .from('page_seo_data')
        .select('*')
        .eq('website_id', websiteId);
      if (error) throw error;
      return data || [];
    } catch (err) {
      console.error('Failed to fetch SEO data', err);
      return [];
    }
  },

  fetchTasks: async (websiteId: string) => {
    try {
      const [blogTasks, seoTasks] = await Promise.all([
        supabase
          .from('blog_tasks')
          .select('id, status, created_at, title')
          .eq('website_id', websiteId)
          .order('created_at', { ascending: false })
          .limit(20),
        supabase
          .from('seo_tasks')
          .select('id, status, created_at, target_url')
          .eq('website_id', websiteId)
          .order('created_at', { ascending: false })
          .limit(20),
      ]);
      return { 
        blog_tasks: blogTasks.data || [], 
        seo_tasks: seoTasks.data || [] 
      };
    } catch (err) {
      console.error('Failed to fetch website tasks', err);
      return { blog_tasks: [], seo_tasks: [] };
    }
  },

  getGeneratedArticle: async (taskId: string) => {
    try {
      const { data, error } = await supabase
        .from('blog_results')
        .select('id, task_id, title, content, created_at')
        .eq('task_id', taskId)
        .single();
      if (error) throw error;
      return data;
    } catch (err) {
      console.error('Error fetching article:', err);
      return null;
    }
  },

  // --------------------
  // Update profile & refresh cache
  // --------------------
  updateUserProfile: async (data: Partial<User> & { user_settings?: Partial<UserSettings> }) => {
    set({ loading: true, error: null });
    try {
      const { data: { user: authUser } } = await supabase.auth.getUser();
      if (!authUser) throw new Error('No authenticated user');

      const { data: updatedUser, error } = await supabase
        .from('users')
        .update(data)
        .eq('id', authUser.id)
        .select()
        .single();
      if (error) throw error;

      await get().fetchUserData(true); // refresh main store + sessionStorage
      return updatedUser;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update user profile';
      set({ error: message });
      console.error(message);
      return null;
    } finally {
      set({ loading: false });
    }
  },

  // --------------------
// Extra actions for ContentQueue (approve/decline/schedule)
// --------------------
approvePost: async (postId: string) => {
  try {
    const { error } = await supabase
      .from('blog_results')
      .update({ status: 'approved' })
      .eq('id', postId);
    if (error) throw error;
    console.log('Post approved', postId);
  } catch (err) {
    console.error('Failed to approve post', err);
  }
},

declinePost: async (postId: string) => {
  try {
    const { error } = await supabase
      .from('blog_results')
      .update({ status: 'declined' })
      .eq('id', postId);
    if (error) throw error;
    console.log('Post declined', postId);
  } catch (err) {
    console.error('Failed to decline post', err);
  }
},

schedulePost: async (postId: string, date: Date) => {
  try {
    const { error } = await supabase
      .from('blog_results')
      .update({ scheduledDate: date.toISOString(), status: 'scheduled' })
      .eq('id', postId);
    if (error) throw error;
    console.log('Post scheduled', postId, date);
  } catch (err) {
    console.error('Failed to schedule post', err);
  }
},

fetchWebsiteBlogPosts: async (websiteId: string) => {
  try {
    const { data, error } = await supabase
      .from('blog_results')
      .select(`
        id,
        title,
        final_content,
        meta_description,
        post_url,
        status,
        created_at,
        published_at,
        scheduled_at
      `)
      .eq('website_id', websiteId)
      .order('created_at', { ascending: false });

    if (error) throw error;

    // Map to BlogPost type with backward-compatible fields
    const posts = (data || []).map((p) => ({
      id: p.id,
      title: p.title,
      content: p.final_content ?? '',
      wordCount: p.final_content ? p.final_content.split(/\s+/).length : 0,
      status: p.status,
      scheduledDate: p.scheduled_at ? new Date(p.scheduled_at) : undefined,
      publishedDate: p.published_at ? new Date(p.published_at) : undefined,
      source: p.post_url ?? undefined,
      impressions: 0, // placeholder for analytics, maintains compatibility
      clicks: 0,
      trend: 0,
    }));

    return posts;
  } catch (err) {
    console.error('Failed to fetch website blog posts', err);
    return [];
  }
},


  clearStore: () => {
    sessionStorage.removeItem(SESSION_KEY);
    set({ user: null, subscription: null, settings: null, websites: [], loading: false, error: null });
  },
}));

// --------------------
// Backward-compatible hooks
// --------------------
export const useUser = () => useUserStore((state) => state.user);

export const useSubscription = () => useUserStore((state) => state.subscription);
export const useUserSettings = () => useUserStore((state) => state.settings);
export const useWebsites = () => useUserStore((state) => state.websites);
export const useUserLoading = () => useUserStore((state) => state.loading);
export const useUserError = () => useUserStore((state) => state.error);
export const useFetchUserData = () => useUserStore((state) => state.fetchUserData);
export const useFetchBlogResults = () => useUserStore((state) => state.fetchBlogResults);
export const useFetchAIRecommendations = () => useUserStore((state) => state.fetchAIRecommendations);
export const useFetchPageSEOData = () => useUserStore((state) => state.fetchPageSEOData);
export const useFetchTasks = () => useUserStore((state) => state.fetchTasks);
export const useGetGeneratedArticle = () => useUserStore((state) => state.getGeneratedArticle);
export const useUpdateUserProfile = () => useUserStore((state) => state.updateUserProfile);
export const useClearUserStore = () => useUserStore((state) => state.clearStore);

export const useFetchWebsiteBlogPosts = () =>
useUserStore((state) => state.fetchWebsiteBlogPosts);

// --------------------
// ContentQueue action hooks
// --------------------
export const useApprovePost = () => useUserStore((state) => state.approvePost);
export const useDeclinePost = () => useUserStore((state) => state.declinePost);
export const useSchedulePost = () => useUserStore((state) => state.schedulePost);
