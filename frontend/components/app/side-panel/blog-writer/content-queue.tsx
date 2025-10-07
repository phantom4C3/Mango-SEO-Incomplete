// components/app/side-panel/content-queue.tsx
'use client';

import { StatusIndicator } from '../../main-editor/status-indicator';
import { BlogPost } from '@/lib/types';
import { useApprovePost, useDeclinePost, useSchedulePost, useFetchWebsiteBlogPosts, useWebsites } from '@/stores/use-user-store';
import React from 'react';



interface ContentQueueProps {
  posts?: BlogPost[];
  selectedPost: BlogPost | null;
  onSelectPost: (post: BlogPost) => void;
}

export const ContentQueue = ({  selectedPost, onSelectPost }: ContentQueueProps) => {
  const approvePost = useApprovePost();
  const declinePost = useDeclinePost();
  const schedulePost = useSchedulePost();

const fetchWebsiteBlogPosts = useFetchWebsiteBlogPosts(); // returns the fetch function
const [blogPosts, setBlogPosts] = React.useState<BlogPost[]>([]); // rename local state to avoid conflict

const websites = useWebsites();
const websiteId = websites[0]?.id; // pick the first website's id (or whichever is selected)

React.useEffect(() => {
  if (!websiteId || !fetchWebsiteBlogPosts) return; // check existence

  const loadPosts = async () => {
    const posts = await fetchWebsiteBlogPosts(websiteId);
    setBlogPosts(posts);
  };

  loadPosts();
}, [websiteId, fetchWebsiteBlogPosts]);



  // Determine which buttons to show based on post status
  const getActionButtons = (post: BlogPost) => {
const buttons: React.ReactNode[] = [];

    if (post.status === 'pending') {
      buttons.push(
        <button
          key="approve"
          className="px-2 py-1 bg-green-600 rounded text-xs"
          onClick={(e) => { e.stopPropagation(); approvePost?.(post.id); }}
        >
          Approve
        </button>
      );
      buttons.push(
        <button
          key="decline"
          className="px-2 py-1 bg-red-600 rounded text-xs"
          onClick={(e) => { e.stopPropagation(); declinePost?.(post.id); }}
        >
          Decline
        </button>
      );
      buttons.push(
        <button
          key="schedule"
          className="px-2 py-1 bg-yellow-600 rounded text-xs"
          onClick={(e) => { e.stopPropagation(); schedulePost?.(post.id, new Date()); }}
        >
          Schedule
        </button>
      );
    } else if (post.status === 'ready') {
      buttons.push(
        <button
          key="schedule"
          className="px-2 py-1 bg-yellow-600 rounded text-xs"
          onClick={(e) => { e.stopPropagation(); schedulePost?.(post.id, new Date()); }}
        >
          Schedule
        </button>
      );
    } else if (post.status === 'scheduled') {
      buttons.push(
        <span key="scheduled" className="text-xs text-gray-300">Scheduled</span>
      );
    }

    return buttons;
  };

  return (
    <div className="space-y-3">
      {blogPosts.map((post) => (
        <div
          key={post.id}
          className={`bg-gray-800 rounded-lg p-3 cursor-pointer hover:bg-gray-750 border ${
            selectedPost?.id === post.id ? 'border-yellow-400' : 'border-gray-700'
          }`}
          onClick={() => onSelectPost(post)}
        >
          <div className="flex justify-between items-start mb-2">
            <h4 className="font-medium text-sm line-clamp-2">{post.title}</h4>
            <StatusIndicator status={post.status} />
          </div>

          <div className="flex justify-between text-xs text-gray-400">
            <span>{post.wordCount} words</span>
            {post.scheduledDate && (
              <span>Scheduled: {post.scheduledDate.toLocaleDateString()}</span>
            )}
            {post.publishedDate && (
              <span>Published: {post.publishedDate.toLocaleDateString()}</span>
            )}
          </div>

          {/* Dynamic buttons */}
          <div className="flex justify-end space-x-2 mt-2">
            {getActionButtons(post)}
          </div>
        </div>
      ))}
    </div>
  );
};
