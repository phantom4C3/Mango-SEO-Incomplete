// components/settings/settings-tab-content.tsx
'use client';

import { SettingsData } from '@/lib/types';

interface SettingsTabContentProps {
  activeTab: string;
  settingsData: SettingsData;
  onSettingsChange: (tab: string, field: string, value: string) => void;
}

export const SettingsTabContent = ({
  activeTab,
  settingsData,
  onSettingsChange
}: SettingsTabContentProps) => {
  switch(activeTab) {
    case 'general':
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Name</label>
            <input
              type="text"
              value={settingsData.general.name}
              onChange={(e) => onSettingsChange('general', 'name', e.target.value)}
              className="w-full bg-gray-800 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Type</label>
            <input
              type="text"
              value={settingsData.general.type}
              onChange={(e) => onSettingsChange('general', 'type', e.target.value)}
              className="w-full bg-gray-800 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Summary</label>
            <textarea
              value={settingsData.general.summary}
              onChange={(e) => onSettingsChange('general', 'summary', e.target.value)}
              className="w-full bg-gray-800 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-400"
              rows={3}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Blog Theme</label>
            <textarea
              value={settingsData.general.blogTheme}
              onChange={(e) => onSettingsChange('general', 'blogTheme', e.target.value)}
              className="w-full bg-gray-800 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-400"
              rows={3}
            />
          </div>
        </div>
      );
    case 'targetAudience':
      return (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Primary Target Country</label>
            <input
              type="text"
              value={settingsData.targetAudience.country}
              onChange={(e) => onSettingsChange('targetAudience', 'country', e.target.value)}
              className="w-full bg-gray-800 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Primary Language</label>
            <input
              type="text"
              value={settingsData.targetAudience.language}
              onChange={(e) => onSettingsChange('targetAudience', 'language', e.target.value)}
              className="w-full bg-gray-800 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Target Audience Summary</label>
            <textarea
              value={settingsData.targetAudience.summary}
              onChange={(e) => onSettingsChange('targetAudience', 'summary', e.target.value)}
              className="w-full bg-gray-800 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-400"
              rows={3}
            />
          </div>
        </div>
      );
    default:
      return <div>Settings content for {activeTab}</div>;
  }
};