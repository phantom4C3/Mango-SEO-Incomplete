'use client';

import React, { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { BlogPost, UserStats, SettingsData } from '@/lib/types';
import { EditorTopBar } from './editor-top-bar';
import { MenuPopup } from './menu-popup';
import { TerminalIO } from '../conversational-ui/terminal-io';
import { EditorFooter } from './editor-footer';
import { SettingsModal } from '@/components/settings/settings-modal';
import { BlogPreviewModal } from '@/components/blog/blog-preview-modal';
import { SidePanel } from '../side-panel/side-panel';

interface EditorProps {
  currentSite: string;
}

type TerminalMode = 'blog-generation' | 'seo-analysis';

export const Editor: React.FC<EditorProps> = ({ currentSite }) => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'content' | 'analytics' | 'settings'>('dashboard');
  const [terminalMode, setTerminalMode] = useState<TerminalMode>('blog-generation');
  const [userStats, setUserStats] = useState<UserStats>({
    credits: 100,
    articlesThisMonth: 78,
    articlesTotal: 245,
    impressions: 12400,
    clicks: 380,
    tasks: 115,
    clusters: 73
  });
  
  const [blogPosts, setBlogPosts] = useState<BlogPost[]>([
    {
      id: '1',
      title: '10 Best Montessori Toys for Toddlers in 2024',
      status: 'ready',
      content: '',
      wordCount: 2450,
      links: { min: 5, max: 11 },
      source: 'keyword',
      ready: true,
      impressions: 2470,
      clicks: 81,
      trend: 12
    },
    {
      id: '2',
      title: 'How to Set Up a Montessori Classroom at Home',
      status: 'researching',
      content: '',
      wordCount: 1200,
      links: { min: 3, max: 8 },
      source: 'serp',
      ready: false,
      impressions: 1250,
      clicks: 34,
      trend: -5
    },
    {
      id: '3',
      title: 'Montessori vs Traditional Education: Key Differences',
      status: 'writing',
      content: '',
      wordCount: 1800,
      links: { min: 7, max: 15 },
      source: 'keyword',
      ready: false,
      impressions: 890,
      clicks: 23,
      trend: 8
    }
  ]);
  
  const [selectedPost, setSelectedPost] = useState<BlogPost | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isAutopilotEnabled, setIsAutopilotEnabled] = useState(true);
  const [terminalOutput, setTerminalOutput] = useState<string[]>([
  ]);
  
  const [settingsData, setSettingsData] = useState<SettingsData>({
    general: {
      name: 'Montessori Fund',
      type: 'Education',
      summary: 'Resources and funding for Montessori education programs worldwide',
      blogTheme: 'Montessori education, child development, teaching methods, educational resources',
      founders: 'Jane Smith, John Doe',
      features: 'Funding programs, teacher training, resource library, community support',
      pricing: 'Basic: Free, Premium: $29/month, Enterprise: Custom'
    },
    targetAudience: {
      country: 'United States',
      language: 'English',
      summary: 'Educators, parents, school administrators interested in Montessori education',
      painPoints: 'Lack of funding, limited resources, need for training materials',
      usage: 'Research, resource gathering, professional development'
    }
  });

  const [activeSettingsTab, setActiveSettingsTab] = useState('general');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [activeSidePanel, setActiveSidePanel] = useState<'content' | 'seo' | 'analytics'>('content');

  // Terminal titles based on mode
  const terminalTitles = {
    'blog-generation': 'Blog Generation Terminal',
    'seo-analysis': 'SEO Analysis Terminal'
  };


  // Wrap the simulated autopilot inside a feature flag or check isAutopilotEnabled && process.env.NODE_ENV !== 'production' (so you can run it only for dev/test
  // Simulate content generation process
  // useEffect(() => {
  //   const interval = setInterval(() => {
  //     if (isAutopilotEnabled) {
  //       setBlogPosts(prev => {
  //         return prev.map(post => {
  //           if (post.status === 'researching' && Math.random() > 0.7) {
  //             addTerminalOutput(`Research complete for: ${post.title}`);
  //             return { ...post, status: 'writing', wordCount: Math.floor(Math.random() * 500) + 100 };
  //           } else if (post.status === 'writing' && Math.random() > 0.6) {
  //             const newWordCount = post.wordCount + Math.floor(Math.random() * 200) + 50;
  //             if (newWordCount >= 2500) {
  //               addTerminalOutput(`Writing complete for: ${post.title}`);
  //               return { ...post, status: 'enhancing', wordCount: newWordCount };
  //             }
  //             addTerminalOutput(`Writing progress: ${post.title} - ${newWordCount} words`);
  //             return { ...post, wordCount: newWordCount };
  //           } else if (post.status === 'enhancing' && Math.random() > 0.5) {
  //             addTerminalOutput(`Enhancement complete for: ${post.title}`);
  //             return { ...post, status: 'ready', wordCount: Math.floor(Math.random() * 1000) + 2500 };
  //           }
  //           return post;
  //         });
  //       });
  //     }
  //   }, 5000);

  //   return () => clearInterval(interval);
  // }, [isAutopilotEnabled]);

  const addTerminalOutput = (message: string) => {
    setTerminalOutput(prev => [...prev, message]);
  };

  const handleGenerateHeadline = () => {
    const newHeadline = `New Content Idea ${blogPosts.length + 1}`;
    const newPost: BlogPost = {
      id: Date.now().toString(),
      title: newHeadline,
      status: 'pending',
      content: '',
      wordCount: 0,
      links: { min: 2, max: 6 },
      source: 'ai',
      ready: false,
      impressions: 0,
      clicks: 0,
      trend: 0
    };
    
    setBlogPosts(prev => [newPost, ...prev]);
    addTerminalOutput(`> New content idea queued: ${newHeadline}`);
  };

  const handleApprovePost = (id: string) => {
    setBlogPosts(prev => 
      prev.map(post => 
        post.id === id ? { ...post, status: 'researching' } : post
      )
    );
    const post = blogPosts.find(p => p.id === id);
    addTerminalOutput(`> Approved for research: ${post?.title}`);
  };

  const handleRejectPost = (id: string) => {
    const post = blogPosts.find(p => p.id === id);
    setBlogPosts(prev => prev.filter(post => post.id !== id));
    addTerminalOutput(`> Rejected: ${post?.title}`);
  };

  const handlePublishPost = (id: string) => {
    setBlogPosts(prev => 
      prev.map(post => 
        post.id === id ? { ...post, status: 'published', publishedDate: new Date() } : post
      )
    );
    setUserStats(prev => ({ 
      ...prev, 
      articlesThisMonth: prev.articlesThisMonth + 1,
      articlesTotal: prev.articlesTotal + 1
    }));
    setShowPreview(false);
    const post = blogPosts.find(p => p.id === id);
    addTerminalOutput(`> Published: ${post?.title}`);
  };

  const handleSettingsChange = (tab: string, field: string, value: string) => {
    setSettingsData(prev => ({
      ...prev,
      [tab]: {
        ...prev[tab as keyof SettingsData],
        [field]: value
      }
    }));
    setHasUnsavedChanges(true);
  };

  const handleCloseSettings = () => {
    if (hasUnsavedChanges) {
      if (!confirm('Unsaved changes will be lost. Are you sure you want to leave?')) {
        return;
      }
    }
    setShowSettings(false);
    setHasUnsavedChanges(false);
  };

  const handleSaveSettings = () => {
    setHasUnsavedChanges(false);
    setShowSettings(false);
    addTerminalOutput('> Settings saved successfully');
  };

  const handleToggleAutopilot = () => {
    setIsAutopilotEnabled(!isAutopilotEnabled);
    addTerminalOutput(`> Autopilot ${!isAutopilotEnabled ? 'ENABLED' : 'DISABLED'}`);
  };

  const handlePostSelect = (post: BlogPost) => {
    setSelectedPost(post);
  };

  const handleTerminalModeChange = (mode: TerminalMode) => {
    setTerminalMode(mode);
    // Clear terminal when switching modes
    setTerminalOutput([`> Switched to ${terminalTitles[mode]}`]);
  };

  return (
    <div className="bg-black text-white min-h-screen flex flex-col">
      <EditorTopBar 
        isMenuOpen={isMenuOpen}
        setIsMenuOpen={setIsMenuOpen}
        userStats={userStats}
        currentSite={currentSite}
        activePanel={activeSidePanel}
        onPanelChange={setActiveSidePanel}
      />

      <MenuPopup 
        isOpen={isMenuOpen}
        onClose={() => setIsMenuOpen(false)}
        onSettingsOpen={() => setShowSettings(true)}
      />

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Column - Terminal Panel */}
        <div className="w-2/3 bg-gray-900 p-6 overflow-y-auto">
          {/* Terminal Mode Selector */}
          <div className="flex items-center gap-3 mb-4">
            <div className="relative">
              <select
                value={terminalMode}
                onChange={(e) => handleTerminalModeChange(e.target.value as TerminalMode)}
                className="appearance-none bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 pr-8 text-white focus:outline-none focus:border-yellow-500 cursor-pointer"
              >
                <option value="blog-generation">Blog Generation</option>
                <option value="seo-analysis">SEO Analysis</option>
              </select>
              {/* Custom dropdown arrow */}
              <div className="pointer-events-none absolute inset-y-0 right-2 flex items-center">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            <h2 className="text-lg font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
              {terminalTitles[terminalMode]}
            </h2>
          </div>

<TerminalIO output={terminalOutput} mode={terminalMode} />

          {/* Content Actions */}
          {selectedPost && (
            <div className="mt-6 bg-gray-800 rounded-lg p-4">
              <h3 className="font-bold mb-3 text-yellow-400">{selectedPost.title}</h3>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <span className="text-gray-400 text-sm">Status:</span>
                  <p className="font-medium capitalize">{selectedPost.status}</p>
                </div>
                <div>
                  <span className="text-gray-400 text-sm">Word Count:</span>
                  <p className="font-medium">{selectedPost.wordCount}</p>
                </div>
              </div>

              {selectedPost.status === 'ready' && (
                <button 
                  className="bg-gradient-to-r from-yellow-400 to-orange-500 text-black px-4 py-2 rounded-md font-bold w-full"
                  onClick={() => setShowPreview(true)}
                >
                  Preview & Publish
                </button>
              )}
            </div>
          )}
        </div>

        {/* Right Column - Side Panel */}
        <div className="w-1/3 bg-gray-800 border-l border-gray-700 overflow-y-auto">
          <SidePanel
            activePanel={activeSidePanel}
            blogPosts={blogPosts}
            selectedPost={selectedPost}
            onPostSelect={handlePostSelect}
            onApprovePost={handleApprovePost}
            onRejectPost={handleRejectPost}
            onGenerateHeadline={handleGenerateHeadline}
          />
        </div>
      </div>

      <EditorFooter 
        isAutopilotEnabled={isAutopilotEnabled}
        onToggleAutopilot={handleToggleAutopilot}
      />

      <SettingsModal
        isOpen={showSettings}
        onClose={handleCloseSettings}
        onSave={handleSaveSettings}
        settingsData={settingsData}
        onSettingsChange={handleSettingsChange}
        activeTab={activeSettingsTab}
        onTabChange={setActiveSettingsTab}
        hasUnsavedChanges={hasUnsavedChanges}
      />

      <BlogPreviewModal
        isOpen={showPreview}
        onClose={() => setShowPreview(false)}
        post={selectedPost}
        onPublish={handlePublishPost}
      />
    </div>
  );
};