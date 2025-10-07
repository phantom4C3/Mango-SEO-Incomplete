'use client';
import { useEffect } from "react";
import { supabase } from "@/lib/supabase-client";
import { useConversationStore } from "@/stores/use-conversation-store";
import { OrchestrationStatus } from "@/lib/types";

interface AutopilotToggleProps {
  isEnabled: boolean;
  onToggle: () => void;
  userId: string;
}

export const AutopilotToggle = ({ isEnabled, onToggle, userId }: AutopilotToggleProps) => {
  const publishArticle = useConversationStore(s => s.publishArticle);
  const checkOrchestrationStatus = useConversationStore(s => s.checkOrchestrationStatus);

  useEffect(() => {
    if (!isEnabled) return;

    const runAutopilot = async () => {
      try {
        // 1️⃣ Fetch topics for this user that are approved / scheduled
        const { data: topics, error } = await supabase
          .from('topics')
          .select('*')
          .eq('user_id', userId)
          .eq('ai_generated', true)
          .eq('blog_status', 'not_generated')
          .order('created_at', { ascending: true });

        if (error) throw error;
        if (!topics || topics.length === 0) return;

        // 2️⃣ Process each topic sequentially
        for (const topic of topics) {
          const taskId = topic.task_id;

          // ✅ status now includes article_id directly
          let status: OrchestrationStatus | null = await checkOrchestrationStatus(taskId);

          // wait until orchestration completes and article_id exists
          const timeoutMs = 5 * 60 * 1000; // 5 minutes
          const start = Date.now();
          while (!status?.completed_at || !status?.article_id) {
            if (Date.now() - start > timeoutMs) {
              console.warn(`Timeout waiting for task ${taskId}`);
              break;
            }
            await new Promise(res => setTimeout(res, 2000));
            status = await checkOrchestrationStatus(taskId);
          }

          if (!status?.article_id) {
            console.warn(`Orchestration completed but no article_id found for task ${taskId}`);
            continue;
          }

          // publish the article
          await publishArticle(status.article_id);
        }
      } catch (err) {
        console.error("Autopilot error:", err);
      }
    };

    runAutopilot();
  }, [isEnabled, userId, publishArticle, checkOrchestrationStatus]);

  return (
    <div className="flex items-center space-x-2">
      <button
        onClick={onToggle}
        className={`relative w-12 h-6 rounded-full transition-colors ${
          isEnabled ? "bg-yellow-400" : "bg-gray-600"
        }`}
      >
        <div
          className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
            isEnabled ? "translate-x-6" : "translate-x-0.5"
          }`}
        />
      </button>
      <span className="text-sm text-white">
        Autopilot is {isEnabled ? "ON" : "OFF"}
      </span>
    </div>
  );
};
