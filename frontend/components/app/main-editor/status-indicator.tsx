'use client';

import { BlogPost } from '@/lib/types';
import { useCurrentTask, useTasks } from '@/stores/use-task-store';

interface StatusIndicatorProps {
  status: BlogPost['status'];
}

export const StatusIndicator = ({ status }: StatusIndicatorProps) => {
  let color = 'bg-gray-500';
  let text = 'Pending';
  let isPulsing = false;

  switch (status) {
    case 'researching':
      color = 'bg-blue-500';
      text = 'Researching';
      isPulsing = true;
      break;
    case 'writing':
      color = 'bg-yellow-500';
      text = 'Writing';
      isPulsing = true;
      break;
    case 'enhancing':
      color = 'bg-purple-500';
      text = 'Enhancing';
      break;
    case 'ready':
      color = 'bg-green-500';
      text = 'Ready';
      break;
    case 'published':
      color = 'bg-green-700';
      text = 'Published';
      break;
  }

  return (
    <div className="flex items-center space-x-2">
      <span
        className={`w-2 h-2 ${color} rounded-full ${isPulsing ? 'animate-pulse' : ''}`}
      ></span>
      <span className="text-xs">{text}</span>
    </div>
  );
};
