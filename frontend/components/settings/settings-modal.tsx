// components/settings/settings-modal.tsx
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { SettingsData } from '@/lib/types';
import { SettingsTabContent } from './settings-tab-content';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  settingsData: SettingsData;
  onSettingsChange: (tab: string, field: string, value: string) => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
  hasUnsavedChanges: boolean;
}

export const SettingsModal = ({
  isOpen,
  onClose,
  onSave,
  settingsData,
  onSettingsChange,
  activeTab,
  onTabChange,
  hasUnsavedChanges
}: SettingsModalProps) => {
  if (!isOpen) return null;

  const handleClose = () => {
    if (hasUnsavedChanges) {
      if (!confirm('Unsaved changes will be lost. Are you sure you want to leave?')) {
        return;
      }
    }
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={handleClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-gray-900 rounded-lg w-full max-w-4xl max-h-screen overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center p-6 border-b border-gray-800">
              <h2 className="text-xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
                Settings
              </h2>
              <button 
                onClick={handleClose}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="flex flex-1 overflow-hidden">
              {/* Settings Tabs */}
              <div className="w-1/4 bg-gray-800 p-4 overflow-y-auto">
                <div className="space-y-1">
                  {['general', 'targetAudience', 'competitors', 'images', 'cta', 'prompts', 'backlinks', 'news', 'videos', 'advanced'].map((tab) => (
                    <button
                      key={tab}
                      className={`w-full text-left px-4 py-2 rounded-md capitalize ${
                        activeTab === tab 
                          ? 'bg-yellow-400 text-black' 
                          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }`}
                      onClick={() => onTabChange(tab)}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Settings Content */}
              <div className="flex-1 p-6 overflow-y-auto">
                <SettingsTabContent 
                  activeTab={activeTab}
                  settingsData={settingsData}
                  onSettingsChange={onSettingsChange}
                />
              </div>
            </div>
            
            <div className="flex justify-end p-6 border-t border-gray-800">
              <button
                onClick={handleClose}
                className="px-4 py-2 rounded-md border border-gray-600 text-white mr-3"
              >
                Cancel
              </button>
              <button
                onClick={onSave}
                className="bg-gradient-to-r from-yellow-400 to-orange-500 text-black px-4 py-2 rounded-md font-bold"
              >
                Save Changes
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};