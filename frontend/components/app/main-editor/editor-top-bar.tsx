'use client';

import { useEffect, useState } from 'react';
import { useSubscription, useUser, useWebsites, useFetchTasks, useFetchBlogResults } from '@/stores/use-user-store';

interface EditorTopBarProps {
  isMenuOpen: boolean;
  setIsMenuOpen: (open: boolean) => void;
}

export const EditorTopBar = ({ isMenuOpen, setIsMenuOpen }: EditorTopBarProps) => {
  const subscription = useSubscription();
  const user = useUser();
  const websites = useWebsites();

  const fetchTasks = useFetchTasks();
  const fetchBlogResults = useFetchBlogResults();

  const [tasks, setTasks] = useState(0);
  const [articlesThisMonth, setArticlesThisMonth] = useState(0);

  const credits = subscription?.credits ?? 0;
  const currentSite = websites.length > 0 ? websites[0].domain : 'No site selected';

  useEffect(() => {
    if (!user?.id || websites.length === 0) return;

    const loadStats = async () => {
      // ✅ get tasks count
      const { blog_tasks, seo_tasks } = await fetchTasks(websites[0].id);
      setTasks((blog_tasks?.length ?? 0) + (seo_tasks?.length ?? 0));

      // ✅ get articles count
      const blogs = await fetchBlogResults(websites[0].id);
      setArticlesThisMonth(blogs.length);
    };

    loadStats();
  }, [user?.id, websites]);

  return (
    <div className="bg-gray-900 border-b border-gray-800 p-3 flex justify-between items-center">
      <div className="flex items-center space-x-4">
        <h1 className="text-lg font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
          mangoseo
        </h1>

        {/* Status Pills */}
        <div className="flex items-center space-x-2">
          <div className="bg-green-500 text-black text-xs px-2 py-1 rounded-full font-medium">
            {tasks} Tasks
          </div>
          <div
            className={`text-xs px-2 py-1 rounded-full font-medium ${
              articlesThisMonth >= credits
                ? 'bg-red-500 text-white'
                : 'bg-blue-500 text-black'
            }`}
          >
            {articlesThisMonth}/{credits} Articles
          </div>
        </div>

        {/* Current Site */}
        <div className="text-sm text-gray-400">{currentSite}</div>
      </div>

      <div className="flex items-center space-x-3">
        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="text-white hover:text-yellow-400 transition-colors text-sm"
        >
          Menu
        </button>
      </div>
    </div>
  );
};
