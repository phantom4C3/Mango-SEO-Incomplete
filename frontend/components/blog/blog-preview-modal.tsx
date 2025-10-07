'use client';

import { motion, AnimatePresence } from 'framer-motion';
import React, { useState, useEffect } from 'react';
import { BlogPost } from '@/lib/types';
import { Button } from '@/components/custom-ui/extras/button'; 
import { supabase } from '@/lib/supabase-client'; // import your supabase client

interface BlogPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  post: BlogPost | null;
  onPublish: (id: string) => void;
}

export const BlogPreviewModal: React.FC<BlogPreviewModalProps> = ({
  isOpen,
  onClose,
  post,
  onPublish,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [editedTitle, setEditedTitle] = useState(''); 

  // Initialize content when post changes or modal opens
  useEffect(() => {
    if (post) {
      setEditedContent(post.content || '');
      setEditedTitle(post.title || '');
    }
  }, [post, isOpen]);
 

  const handleSaveEdit = () => {
    // Here you would typically save to your database
    console.log('Saving edits:', { title: editedTitle, content: editedContent });
    // For now, we'll just update the local state
    if (post) {
      // In a real app, you'd update the post in your state/store
      // setBlogPosts(prev => prev.map(p => p.id === post.id ? {...p, title: editedTitle, content: editedContent} : p))
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    // Reset to original content
    if (post) {
      setEditedContent(post.content || '');
      setEditedTitle(post.title || '');
    }
    setIsEditing(false);
  };

  const handlePublish = () => {
    if (post) {
      // If there are unsaved edits, save them first or warn the user
      if (isEditing) {
        if (confirm('You have unsaved changes. Save changes before publishing?')) {
          handleSaveEdit();
        }
      }
      onPublish(post.id);
    }
  };

  if (!isOpen || !post) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-gray-900 rounded-lg w-full max-w-6xl max-h-[95vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-800 bg-gray-900">
              <div className="flex items-center gap-4">
                <h2 className="text-2xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
                  {isEditing ? 'Edit Article' : 'Preview Article'}
                </h2>
                {isEditing && (
                  <span className="px-2 py-1 bg-yellow-500 text-black text-sm rounded-full font-medium">
                    Editing Mode
                  </span>
                )}
              </div>
              <button
  onClick={() => {
    if (isEditing && (editedContent !== post?.content || editedTitle !== post?.title)) {
      if (!window.confirm("You have unsaved changes. Are you sure you want to close?")) return;
    }
    onClose();
  }}
  className="text-gray-400 hover:text-white text-2xl transition-colors"
>
  ✕
</button>

            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto p-6 bg-gray-800">
              {isEditing ? (
                // Edit Mode
                <div className="max-w-4xl mx-auto space-y-6">
                  {/* Title Editor */}
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-2">
                      Article Title
                    </label>
                    <input
                      type="text"
                      value={editedTitle}
                      onChange={(e) => setEditedTitle(e.target.value)}
                      className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-yellow-500 focus:outline-none text-xl font-bold"
                      placeholder="Enter article title..."
                    />
                  </div>

                  {/* Content Editor */}
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-2">
                      Article Content
                    </label>
                    <textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                    
                        className="w-full min-h-[24rem] max-h-[70vh] bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-yellow-500 focus:outline-none font-mono text-sm resize-y overflow-auto"

                      placeholder="Write your article content here..."
                    />
                    <div className="mt-2 text-xs text-gray-400">
                      Word count: {editedContent.split(/\s+/).filter(word => word.length > 0).length} words
                    </div>
                  </div>
 
                </div>
              ) : (
                // Preview Mode
                <div className="max-w-4xl mx-auto">
                  {/* Article Header */}
                  <div className="mb-8 text-center">
                    <h1 className="text-4xl font-bold text-white mb-4">
                      {editedTitle || post.title}
                    </h1>
                    <div className="text-gray-400 text-sm">
                      <span>Status: </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        post.status === 'ready' ? 'bg-green-500 text-white' :
                        post.status === 'writing' ? 'bg-yellow-500 text-black' :
                        'bg-gray-500 text-white'
                      }`}>
                        {post.status}
                      </span>
                      <span className="mx-4">•</span>
                      <span>Word Count: {post.wordCount}</span>
                    </div>
                  </div>

                  {/* Article Content */}
                  <div className="prose prose-invert prose-lg max-w-none">
                    <div 
                      className="text-gray-300 leading-relaxed"
                      dangerouslySetInnerHTML={{ 
                        __html: editedContent || post.content || `
                          <div class="text-center py-12 text-gray-500">
                            <p class="text-lg mb-4">No content available for preview</p>
                            <p class="text-sm">Click "Edit Content" to add article content</p>
                          </div>
                        ` 
                      }} 
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Footer Actions */}
            <div className="flex justify-between items-center p-6 border-t border-gray-800 bg-gray-900">
              <div className="text-sm text-gray-400">
                {isEditing ? 'Edit your article content' : 'Preview your article before publishing'}
              </div>
              
              <div className="flex gap-3">
                {isEditing ? (
                  // Editing Mode Actions
                  <>
                    <Button
                      onClick={handleCancelEdit}
                      variant="outline"
                      className="border-gray-600 text-white hover:bg-gray-800"
                    >
                      Discard Changes
                    </Button>
                    <Button
                      onClick={handleSaveEdit}
                      className="bg-yellow-500 hover:bg-yellow-400 text-black font-medium"
                    >
                      Save Changes
                    </Button>
                  </>
                ) : (
                  // Preview Mode Actions
                  <>
                    <Button
                      onClick={() => setIsEditing(true)}
                      variant="outline"
                      className="border-gray-600 text-white hover:bg-gray-800"
                    >
                      Edit Content
                    </Button> 
                    <Button
                      onClick={handlePublish}
                      className="bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold hover:from-yellow-300 hover:to-orange-400"
                    >
                      Publish Now
                    </Button>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};


// You cannot show the final blog immediately; the frontend must poll the task status or use a real-time listener If this is a draft workflow, save locally in modal until the user clicks Save & Publish. Optionally implement auto-save draft via debounced API calls to Supabase for better UX.