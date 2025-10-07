// central place to poll tasks + update UI inline with terminal-style logs.// frontend/stores/use-task-store.tsx

import { create } from 'zustand'
import { supabase } from '../lib/supabase-client'  // ✅ Corrected import path
import { Task, TaskStatus, TaskState, TaskActions, AgentSubtask, BlogPost
 } from '../lib/types'  // ✅ Corrected import path
 
 

export const taskToBlogPost = (task: Task): BlogPost => ({
  id: task.id,
  title: task.name || 'Untitled',        // 👈 fallback if DB has no title
  content: '',                           // no content in Task, UI can fill later
  status: mapTaskStatusToBlogStatus(task.status),
  wordCount: 0,
  scheduledDate: undefined,
  publishedDate: undefined,
});

// helper to map backend TaskStatus → frontend BlogPost status
const mapTaskStatusToBlogStatus = (status: Task['status']): BlogPost['status'] => {
  switch (status) {
    case 'pending': return 'pending';
    case 'processing': return 'writing';
    case 'completed': return 'ready';
    case 'failed': return 'declined' as any; // or map to "pending"
    case 'cancelled': return 'pending';
    default: return 'pending';
  }
};


// Convert any Supabase row to AgentSubtask
const toAgentSubtask = (obj: any): AgentSubtask => ({
  id: obj.id,
  taskId: obj.task_id,
  agentType: obj.agent_type,
  status: obj.status,
  attempt: obj.attempt ?? 0,
  errorMessage: obj.error_message ?? null,
  parameters: obj.parameters ?? {},
  createdAt: obj.created_at,
  updatedAt: obj.updated_at,
  completedAt: obj.completed_at,
});

export const useTaskStore = create<TaskState & TaskActions>((set, get) => 
  ({



      initRealtimeSubscriptions: (userId: string) => {
    // ✅ Subscribe to seo_tasks
    const seoTasksChannel = supabase
      .channel('seo_tasks_changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'seo_tasks', filter: `user_id=eq.${userId}` },
        (payload) => {
const { tasks } = get();
if (payload.eventType === 'INSERT') {
  const taskMap = new Map(tasks.map(t => [t.id, t]));
taskMap.set(payload.new.id, payload.new as Task);
set({ tasks: Array.from(taskMap.values()).sort((a,b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()).slice(0, 500) });

} else if (payload.eventType === 'UPDATE') {
  set({
    tasks: tasks.map((t) => (t.id === payload.new.id ? (payload.new as Task) : t)),
  });
} else if (payload.eventType === 'DELETE') {
  set({ tasks: tasks.filter((t) => t.id !== payload.old.id) });
}
        }
      )
      .subscribe();

    // ✅ Subscribe to blog_tasks
    const blogTasksChannel = supabase
      .channel('blog_tasks_changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'blog_tasks', filter: `user_id=eq.${userId}` },
        (payload) => {
          const { tasks } = get();
          if (payload.eventType === 'INSERT') {
            set({ tasks: [payload.new as Task, ...tasks] });
          } else if (payload.eventType === 'UPDATE') {
            set({
              tasks: tasks.map((t) => (t.id === payload.new.id ? (payload.new as Task) : t)),
            });
          } else if (payload.eventType === 'DELETE') {
            set({ tasks: tasks.filter((t) => t.id !== payload.old.id) });
          }
        }
      )
      .subscribe();

    // ✅ Subscribe to agent runs (subtasks)
    const seoRunsChannel = supabase
      .channel('seo_runs_changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'seo_agent_runs' },
        (payload) => {
const { subtasks } = get();
if (payload.eventType === 'INSERT') {
  set({ subtasks: [...subtasks, toAgentSubtask(payload.new)] });
} else if (payload.eventType === 'UPDATE') {
  set({
    subtasks: subtasks.map((s) =>
      s.id === payload.new.id ? toAgentSubtask(payload.new) : s
    ),
  });
}
        }
      )
      .subscribe();

    const blogRunsChannel = supabase
      .channel('blog_runs_changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'blog_agent_runs' },
        (payload) => {
          const { subtasks } = get();
if (payload.eventType === 'INSERT') {
  set({ subtasks: [...subtasks, toAgentSubtask(payload.new)] });
} else if (payload.eventType === 'UPDATE') {
  set({
    subtasks: subtasks.map((s) =>
      s.id === payload.new.id ? toAgentSubtask(payload.new) : s
    ),
  });
}

        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(seoTasksChannel);
      supabase.removeChannel(blogTasksChannel);
      supabase.removeChannel(seoRunsChannel);
      supabase.removeChannel(blogRunsChannel);
    };
  },

  // State
  tasks: [],
  currentTask: null,
    subtasks: [],   // ✅ add this line
  isLoading: false,
  error: null,

  // Actions
  fetchTasks: async (userId: string) => {
    try {
      set({ isLoading: true, error: null })
      
const { data: seoTasks, error: seoError } = await supabase
  .from("seo_tasks")
  .select("*")
  .eq("user_id", userId)
  .order("created_at", { ascending: false })
  .limit(500); // ✅ add this

const { data: blogTasks, error: blogError } = await supabase
  .from("blog_tasks")
  .select("*")
  .eq("user_id", userId)
  .order("created_at", { ascending: false })
  .limit(500); // ✅ add this


if (seoError || blogError) throw seoError || blogError;

set({
  tasks: [...(seoTasks || []), ...(blogTasks || [])],
  isLoading: false,
});




 
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch tasks'
      set({ error: errorMessage, isLoading: false })
    }
  },

  fetchTaskById: async (taskId: string) => {
    try {
      set({ isLoading: true, error: null })
      
let task = null;

const { data: seoTask } = await supabase
  .from("seo_tasks")
  .select("*")
  .eq("id", taskId)
  .maybeSingle();

if (seoTask) task = seoTask;

if (!task) {
  const { data: blogTask } = await supabase
    .from("blog_tasks")
    .select("*")
    .eq("id", taskId)
    .maybeSingle();

  if (blogTask) task = blogTask;
}

if (!task) throw new Error("Task not found");

set({ currentTask: task, isLoading: false });
 
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch task'
      set({ error: errorMessage, isLoading: false })
    }
  },
fetchSubtasks: async (taskId: string) => {
  try {
    set({ isLoading: true, error: null });

    const { data: seoRuns, error: seoError } = await supabase
      .from("seo_agent_runs")
      .select("*")
      .eq("task_id", taskId);

    const { data: blogRuns, error: blogError } = await supabase
      .from("blog_agent_runs")
      .select("*")
      .eq("task_id", taskId);

    if (seoError || blogError) throw seoError || blogError;
set({
  subtasks: [
    ...(seoRuns?.map(toAgentSubtask) || []),
    ...(blogRuns?.map(toAgentSubtask) || []),
  ],
  isLoading: false,
});

  } catch (err) {
    const errorMessage =
      err instanceof Error ? err.message : "Failed to fetch subtasks";
    set({ error: errorMessage, isLoading: false });
  }
},
retryTask: async (taskId: string) => {
  try {
    set({ error: null });
    // call backend RPC if available
    await supabase.rpc("retry_task", { task_id: taskId });
    await get().fetchTaskById(taskId);
  } catch (err) {
    set({ error: err instanceof Error ? err.message : "Failed to retry task" });
  }
},

retrySubtask: async (taskId: string, agentType: string) => {
  try {
    set({ error: null });
    await supabase.rpc("retry_subtask", { task_id: taskId, agent_type: agentType });
    await get().fetchSubtasks(taskId);
  } catch (err) {
    set({ error: err instanceof Error ? err.message : "Failed to retry subtask" });
  }
},

cancelTask: async (taskId: string) => {
  try {
    set({ error: null });
// Try seo_tasks first, then blog_tasks
const { error: seoError } = await supabase
  .from("seo_tasks")
  .update({ status: "cancelled" })
  .eq("id", taskId);

if (seoError) {
  const { error: blogError } = await supabase
    .from("blog_tasks")
    .update({ status: "cancelled" })
    .eq("id", taskId);

  if (blogError) throw blogError;
}


    // update local state
    const { tasks } = get();
    set({
      tasks: tasks.map((t) =>
        t.id === taskId ? { ...t, status: "cancelled" } : t
      ),
    });
  } catch (err) {
    set({ error: err instanceof Error ? err.message : "Failed to cancel task" });
  }
},
updateTaskStatus: async (taskId: string, status: TaskStatus, result?: any) => {
  try {
    set({ error: null });

    let supabaseError: any = null;

    // Try seo_tasks
    const { error: seoError } = await supabase
      .from("seo_tasks")
      .update({
        status,
        result,
        updated_at: new Date().toISOString(),
      })
      .eq("id", taskId);

    if (seoError) {
      // If not found in seo_tasks, try blog_tasks
      const { error: blogError } = await supabase
        .from("blog_tasks")
        .update({
          status,
          result,
          updated_at: new Date().toISOString(),
        })
        .eq("id", taskId);

      supabaseError = blogError;
    } else {
      supabaseError = seoError;
    }

    if (supabaseError) {
      throw new Error(supabaseError.message);
    }

    // ✅ Update local state
    const { tasks } = get();
    const updatedTasks = tasks.map((task) =>
      task.id === taskId ? { ...task, status, result } : task
    );
    set({ tasks: updatedTasks });
  } catch (err) {
    const errorMessage =
      err instanceof Error ? err.message : "Failed to update task";
    set({ error: errorMessage });
  }
},


  createTask: async (taskData: Partial<Task>) => {
    try {
      set({ isLoading: true, error: null })


const { data, error: supabaseError } = await supabase
  .from("blog_tasks") // or "seo_tasks"
  .insert([{
    ...taskData,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }])
  .select()
  .single();


      if (supabaseError) {
        throw new Error(supabaseError.message)
      }

      // Add to local state
      const { tasks } = get()
      set({ tasks: [data, ...tasks], isLoading: false })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create task'
      set({ error: errorMessage, isLoading: false })
    }
  },

  clearError: () => set({ error: null }),


}))




// State hooks
export const useTasks = () => useTaskStore((state) => state.tasks);
export const useCurrentTask = () => useTaskStore((state) => state.currentTask);
export const useSubtasks = () => useTaskStore((state) => state.subtasks);
export const useTaskIsLoading = () => useTaskStore((state) => state.isLoading);
export const useTaskError = () => useTaskStore((state) => state.error);


export const useInitTaskRealtime = () =>
  useTaskStore((state) => state.initRealtimeSubscriptions);

// Action hooks
export const useFetchTasks = () => useTaskStore((state) => state.fetchTasks);
export const useFetchTaskById = () => useTaskStore((state) => state.fetchTaskById);
export const useFetchSubtasks = () => useTaskStore((state) => state.fetchSubtasks);
export const useUpdateTaskStatus = () => useTaskStore((state) => state.updateTaskStatus);
export const useCreateTask = () => useTaskStore((state) => state.createTask);
export const useRetryTask = () => useTaskStore((state) => state.retryTask);
export const useRetrySubtask = () => useTaskStore((state) => state.retrySubtask);
export const useCancelTask = () => useTaskStore((state) => state.cancelTask);
export const useClearTaskError = () => useTaskStore((state) => state.clearError);
