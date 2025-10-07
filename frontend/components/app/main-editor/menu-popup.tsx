'use client';

import React, { useEffect, useRef } from 'react';
import { useUser, useUserSettings } from '@/stores/use-user-store';

interface MenuPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onSettingsOpen: () => void;
  userEmail?: string; // Optional dynamic email
}

export const MenuPopup = ({
  isOpen,
  onClose,
  onSettingsOpen,
  userEmail = 'email@example.com', // <-- default placeholder
}: MenuPopupProps) => {
  const popupRef = useRef<HTMLDivElement>(null);

  // ✅ Add these lines right here
  const user = useUser();              // fetch real user data
  const settings = useUserSettings();  // fetch user settings if needed

  // Then override the placeholder with real data
  const emailToShow = user?.email ?? userEmail;

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={popupRef}
      className="absolute top-16 right-4 bg-gray-900 border border-gray-800 rounded-lg shadow-xl z-50 w-48"
      role="menu"
    >
      <nav className="p-2">
        {/* User Email */}
        <div className="px-4 py-2 text-gray-400 border-b border-gray-800">{emailToShow}</div>

        <div className="border-b border-gray-800 my-2"></div>

        {/* Leave Website */}
        <button
          className="block w-full text-left px-4 py-2 rounded-md text-red-500 hover:bg-gray-800"
          role="menuitem"
          onClick={onClose}
        >
          Leave this website
        </button>

        <div className="border-b border-gray-800 my-2"></div>

        {/* Other Menu Items */}
        {['backlinks', 'invite', 'settings', 'logout'].map((item) => (
          <button
            key={item}
            className="block w-full text-left px-4 py-2 rounded-md capitalize text-gray-300 hover:bg-gray-800 hover:text-white"
            role="menuitem"
            onClick={() => {
              if (item === 'settings') onSettingsOpen();
              onClose();
            }}
          >
            {item}
          </button>
        ))}
      </nav>
    </div>
  );
};
