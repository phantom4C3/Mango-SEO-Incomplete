// components/app/main-editor/editor-footer.tsx
'use client'; 
import { useUserSettings, useUpdateUserProfile } from '@/stores/use-user-store';
import { AutopilotToggle } from './autopilot-toggle';

interface EditorFooterProps {
  isAutopilotEnabled: boolean;
  onToggleAutopilot: () => void;
}

export const EditorFooter = ({ isAutopilotEnabled, onToggleAutopilot }: EditorFooterProps) => {
  const settings = useUserSettings();
  const updateUserProfile = useUpdateUserProfile();

  const toggleAutopilot = async () => {
    if (!settings) return;

    // Toggle autopilot and save to backend
    const updatedSettings: typeof settings = {
      ...settings,
      notifications: {
        ...settings.notifications,
        autopilot: !settings.notifications.autopilot
      }
    };
    
    await updateUserProfile({ user_settings: updatedSettings });
    // Also call the local toggle for immediate UI response
    onToggleAutopilot();
  };

  return (
    <div className="bg-gray-900 border-t border-gray-800 p-3 flex justify-between items-center">
      <AutopilotToggle
        isEnabled={settings?.notifications?.autopilot ?? false}
        onToggle={toggleAutopilot}
      />
      
      <div className="flex space-x-4">
        <button className="w-8 h-8 rounded-md bg-gray-800 flex items-center justify-center hover:bg-yellow-400 hover:text-black transition-colors">
          <span className="text-sm">D</span>
        </button>
        <button className="w-8 h-8 rounded-md bg-gray-800 flex items-center justify-center hover:bg-yellow-400 hover:text-black transition-colors">
          <span className="text-sm">X</span>
        </button>
        <button className="w-8 h-8 rounded-md bg-gray-800 flex items-center justify-center hover:bg-yellow-400 hover:text-black transition-colors">
          <span className="text-sm">@</span>
        </button>
      </div>
    </div>
  );
};