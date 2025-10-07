// frontend/components/app/conversational-ui/progress-indicator.tsx

import React from 'react'; 
import { Card } from '@/components/custom-ui/extras/card';

interface ProgressIndicatorProps {
  taskId: string; // ID of the current AI task
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ taskId }) => {
  const progress = useConversationStore(
    (state) => state.getTaskProgress(taskId) // pipeline updates progress in store
  );

  if (progress === null || progress === undefined) return null; // no task running

  return (
    <Card className="p-4 w-full max-w-md mx-auto my-2 bg-gray-900 border-gray-700">
      <div className="flex flex-col space-y-2">
        <div className="text-sm font-medium text-gray-300">Task Progress</div>
        <div className="relative w-full h-4 bg-gray-700 rounded-full">
          <div
            className="absolute top-0 left-0 h-4 rounded-full transition-all duration-300 bg-gradient-to-r from-yellow-400 to-orange-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="text-sm text-gray-400 text-right">{progress}% completed</div>
      </div>
    </Card>
  );
};





// If you later want “live publish progress” → then add realtime subscription or polling inside the dashboard component (not in a separate store).
//  this is  indicator for cms deployment